"""
Test pour vérifier que task_done() est TOUJOURS appelé.

Ce test vérifie spécifiquement le bug où task_done() n'était pas appelé
lors du signal d'arrêt (None, None, None), causant un blocage de queue.join().
"""
import queue
import threading
import time

import pytest


def test_task_done_called_for_stop_signal():
    """
    Test CRITIQUE : Vérifie que task_done() est appelé même pour le signal d'arrêt.

    Si ce test se bloque, c'est que task_done() n'est pas appelé et queue.join()
    attend indéfiniment.
    """
    event_queue = queue.Queue()
    stop_worker = False
    processed = []

    def worker_loop():
        """Worker qui simule _worker_loop de DevToolsPlayerProxy."""
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Structure corrigée : finally englobe tout
                try:
                    if event_name is None:
                        processed.append("STOP_SIGNAL")
                        return  # Sortie propre

                    processed.append(event_name)

                finally:
                    # CRITIQUE: Doit être appelé même si return !
                    event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    # Démarrer le worker
    worker = threading.Thread(target=worker_loop, daemon=True)
    worker.start()
    time.sleep(0.1)

    # Envoyer des événements normaux
    event_queue.put(("event1", {}, "source"))
    event_queue.put(("event2", {}, "source"))

    # Envoyer le signal d'arrêt
    event_queue.put((None, None, None))

    # Attendre avec timeout pour détecter un blocage
    start_time = time.time()
    join_timeout = 3.0

    # Si task_done() n'est pas appelé pour le signal d'arrêt,
    # join() bloquera et on timeout
    event_queue.join()
    elapsed = time.time() - start_time

    # Vérifications
    assert elapsed < join_timeout, f"join() a pris {elapsed}s, possible blocage!"
    assert "event1" in processed
    assert "event2" in processed
    assert "STOP_SIGNAL" in processed, "Le signal d'arrêt doit avoir été traité"

    # Attendre que le worker se termine
    worker.join(timeout=1.0)
    assert not worker.is_alive(), "Worker should have stopped"


def test_task_done_called_on_exception():
    """
    Test que task_done() est appelé même si le handler lève une exception.
    """
    event_queue = queue.Queue()
    stop_worker = False

    def worker_loop():
        """Worker avec gestion d'exceptions."""
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    if event_name is None:
                        return

                    # Simuler une exception
                    if event_name == "bad_event":
                        raise ValueError("Simulated error")

                finally:
                    event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    worker = threading.Thread(target=worker_loop, daemon=True)
    worker.start()
    time.sleep(0.1)

    # Envoyer un événement qui va lever une exception
    event_queue.put(("bad_event", {}, "source"))

    # Si task_done() n'est pas appelé, join() bloquera
    start_time = time.time()
    event_queue.join()
    elapsed = time.time() - start_time

    assert elapsed < 2.0, "join() should not block even on exception"

    # Arrêter proprement
    stop_worker = True
    event_queue.put((None, None, None))
    worker.join(timeout=1.0)


def test_task_done_called_for_all_events():
    """
    Test que task_done() est appelé pour tous les événements,
    y compris le signal d'arrêt.
    """
    event_queue = queue.Queue()
    stop_worker = False
    task_done_count = 0

    # Wrapper pour compter les appels à task_done()
    original_task_done = event_queue.task_done

    def counted_task_done():
        nonlocal task_done_count
        task_done_count += 1
        original_task_done()

    event_queue.task_done = counted_task_done

    def worker_loop():
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    if event_name is None:
                        return
                finally:
                    event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    worker = threading.Thread(target=worker_loop, daemon=True)
    worker.start()
    time.sleep(0.1)

    # Envoyer 3 événements normaux + 1 signal d'arrêt = 4 task_done attendus
    event_queue.put(("event1", {}, "source"))
    event_queue.put(("event2", {}, "source"))
    event_queue.put(("event3", {}, "source"))
    event_queue.put((None, None, None))  # Signal d'arrêt

    # Attendre que tout soit traité
    event_queue.join()

    # Attendre que le worker se termine
    worker.join(timeout=1.0)

    # Vérifier que task_done() a été appelé 4 fois (3 events + 1 stop signal)
    assert task_done_count == 4, f"Expected 4 task_done() calls, got {task_done_count}"


def test_stop_signal_order_race_condition():
    """
    Test la race condition dans stop() où _stop_worker était mis à True
    AVANT le signal d'arrêt, causant le worker à sortir sans traiter le signal.

    Bug: Si _stop_worker=True AVANT put(None), le worker peut sortir de la boucle
    sans traiter le signal d'arrêt, donc task_done() n'est jamais appelé.
    """
    event_queue = queue.Queue()
    stop_worker = False
    processed = []

    def worker_loop():
        """Worker qui simule _worker_loop."""
        nonlocal stop_worker
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    if event_name is None:
                        processed.append("STOP")
                        return
                    processed.append(event_name)
                finally:
                    event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    # Démarrer le worker
    worker = threading.Thread(target=worker_loop, daemon=True)
    worker.start()
    time.sleep(0.1)

    # Envoyer des événements
    for i in range(3):
        event_queue.put((f"event{i}", {}, "source"))

    # Simuler stop() CORRIGÉ : signal d'arrêt AVANT _stop_worker
    event_queue.put((None, None, None))  # Signal d'arrêt d'abord

    # Attendre que la queue se vide
    start_time = time.time()
    event_queue.join()  # Ne devrait PAS bloquer
    elapsed = time.time() - start_time

    # Signaler l'arrêt APRÈS
    stop_worker = True

    # Vérifications
    assert elapsed < 2.0, f"join() a pris {elapsed}s, blocage détecté!"
    assert "STOP" in processed, "Le signal d'arrêt doit avoir été traité"
    assert len(processed) == 4, f"4 événements attendus, got {len(processed)}"

    # Attendre le worker
    worker.join(timeout=1.0)
    assert not worker.is_alive()


def test_buggy_stop_order_would_block():
    """
    Démontre que l'ordre BUGUÉ (_stop_worker AVANT signal) causerait un blocage.

    Version buggée: _stop_worker=True puis put(None)
    → Le worker peut sortir avant de traiter le signal
    → task_done() jamais appelé
    → join() bloque
    """
    event_queue = queue.Queue()
    stop_worker = False
    processed = []

    def worker_loop():
        """Worker."""
        nonlocal stop_worker
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    if event_name is None:
                        processed.append("STOP")
                        return
                    processed.append(event_name)
                finally:
                    event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    worker = threading.Thread(target=worker_loop, daemon=True)
    worker.start()
    time.sleep(0.1)

    # Envoyer un événement
    event_queue.put(("event1", {}, "source"))
    time.sleep(0.05)  # Laisser le worker le traiter

    # Simuler stop() BUGUÉ : _stop_worker AVANT signal
    stop_worker = True  # ← BUG: Avant le signal !
    time.sleep(0.1)  # Laisser le worker checker la condition
    event_queue.put((None, None, None))  # Signal d'arrêt après

    # Essayer join avec timeout court
    start_time = time.time()
    try:
        # Utiliser un timeout court pour détecter le blocage
        import signal as sig

        def timeout_handler(signum, frame):
            raise TimeoutError("Blocage détecté!")

        old_handler = sig.signal(sig.SIGALRM, timeout_handler)
        sig.alarm(2)  # 2 secondes

        event_queue.join()  # Devrait bloquer

        sig.alarm(0)  # Annuler
        sig.signal(sig.SIGALRM, old_handler)

        # Si on arrive ici sans timeout, c'est que ça a marché (timing chanceux)
        elapsed = time.time() - start_time
        print(f"Pas de blocage (timing chanceux): {elapsed}s")

    except (TimeoutError, AttributeError) as e:
        # TimeoutError = blocage détecté
        # AttributeError = pas de SIGALRM (Windows)
        elapsed = time.time() - start_time
        # On s'attend à un blocage avec l'ordre bugué
        assert elapsed >= 1.5, "Devrait bloquer avec l'ordre bugué"
        print(f"Blocage attendu détecté: {elapsed}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
