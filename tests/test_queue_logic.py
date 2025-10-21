"""
Tests unitaires de la logique de queue sans dépendances Flask/requests.

Ces tests vérifient directement la logique de traitement séquentiel
en isolant la queue et le worker thread.
"""
import pytest
import queue
import threading
import time


def test_sequential_processing_order():
    """
    Test que les événements sont traités dans l'ordre via une queue.
    Ce test simule la logique du player sans dépendre de Flask.
    """
    processed_events = []
    event_queue = queue.Queue()
    stop_worker = False

    def mock_handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler mock qui enregistre l'ordre."""
        time.sleep(0.05)  # Simuler un traitement
        processed_events.append(event_name)
        return True

    def worker_loop():
        """Simulation de _worker_loop()."""
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if event_name is None:  # Signal d'arrêt
                    break

                mock_handler(event_name, event_data, source)
                event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    # Démarrer le worker
    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    time.sleep(0.1)  # Attendre le démarrage

    # Envoyer des événements dans l'ordre
    events_to_send = ["event1", "event2", "event3", "event4", "event5"]
    for event_name in events_to_send:
        event_queue.put((event_name, {"data": "test"}, "test-source"))

    # Attendre que tous soient traités
    event_queue.join()

    # Arrêter le worker
    stop_worker = True
    event_queue.put((None, None, None))
    worker_thread.join(timeout=2)

    # VÉRIFICATIONS
    assert len(processed_events) == 5, "Tous les événements doivent être traités"
    assert processed_events == events_to_send, f"L'ordre doit être préservé: {processed_events}"


def test_handler_exceptions_dont_break_queue():
    """
    Test que les exceptions dans le handler n'arrêtent pas le traitement.
    """
    processed_events = []
    event_queue = queue.Queue()
    stop_worker = False

    def failing_handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler qui lève une exception sur event2."""
        processed_events.append(event_name)
        if event_name == "event2":
            raise ValueError("Simulated error")
        return True

    def worker_loop():
        """Worker avec gestion d'erreurs."""
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if event_name is None:
                    break

                try:
                    failing_handler(event_name, event_data, source)
                except Exception as e:
                    # Le worker doit capturer les exceptions et continuer
                    pass

                event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    # Envoyer 3 événements
    event_queue.put(("event1", {}, "source"))
    event_queue.put(("event2", {}, "source"))  # Va lever une exception
    event_queue.put(("event3", {}, "source"))

    # Attendre
    event_queue.join()

    # Arrêter
    stop_worker = True
    event_queue.put((None, None, None))
    worker_thread.join(timeout=2)

    # Tous les événements doivent avoir été traités
    assert len(processed_events) == 3
    assert processed_events == ["event1", "event2", "event3"]


def test_handler_returning_false_continues():
    """
    Test que si un handler retourne False, le traitement continue.
    """
    processed_events = []
    results = []
    event_queue = queue.Queue()
    stop_worker = False

    def selective_handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler qui retourne False pour event2."""
        processed_events.append(event_name)
        if event_name == "event2":
            return False
        return True

    def worker_loop():
        """Worker qui enregistre les résultats."""
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if event_name is None:
                    break

                result = selective_handler(event_name, event_data, source)
                results.append((event_name, result))
                event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    # Envoyer des événements
    event_queue.put(("event1", {}, "source"))
    event_queue.put(("event2", {}, "source"))  # Va retourner False
    event_queue.put(("event3", {}, "source"))

    # Attendre
    event_queue.join()

    # Arrêter
    stop_worker = True
    event_queue.put((None, None, None))
    worker_thread.join(timeout=2)

    # Vérifier
    assert len(processed_events) == 3
    assert processed_events == ["event1", "event2", "event3"]
    assert results == [
        ("event1", True),
        ("event2", False),  # Échec
        ("event3", True)
    ]


def test_queue_size_changes():
    """
    Test que la taille de la queue change correctement pendant le traitement.
    """
    event_queue = queue.Queue()
    stop_worker = False
    queue_sizes = []

    def slow_handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler lent."""
        time.sleep(0.15)
        return True

    def worker_loop():
        """Worker."""
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if event_name is None:
                    break

                slow_handler(event_name, event_data, source)
                event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    # Envoyer rapidement plusieurs événements
    for i in range(5):
        event_queue.put((f"event{i}", {}, "source"))

    # Enregistrer la taille initiale (devrait être > 0)
    initial_size = event_queue.qsize()
    queue_sizes.append(initial_size)

    # Attendre un peu
    time.sleep(0.2)
    mid_size = event_queue.qsize()
    queue_sizes.append(mid_size)

    # Attendre que tout soit traité
    event_queue.join()
    final_size = event_queue.qsize()
    queue_sizes.append(final_size)

    # Arrêter
    stop_worker = True
    event_queue.put((None, None, None))
    worker_thread.join(timeout=2)

    # Vérifications
    assert initial_size > 0, f"La queue devrait avoir des éléments au début: {initial_size}"
    assert final_size == 0, f"La queue devrait être vide à la fin: {final_size}"
    # La taille devrait décroître
    assert initial_size >= mid_size >= final_size


def test_timing_proves_sequential_not_parallel():
    """
    Test que le timing prouve que les événements sont traités séquentiellement.
    Si c'était en parallèle, le temps total serait ~0.05s (le plus long).
    Séquentiel = 5 * 0.05s = ~0.25s
    """
    processed_events = []
    processing_times = []
    event_queue = queue.Queue()
    stop_worker = False

    def timed_handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler qui enregistre le temps."""
        time.sleep(0.05)
        processed_events.append(event_name)
        processing_times.append(time.time())
        return True

    def worker_loop():
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if event_name is None:
                    break

                timed_handler(event_name, event_data, source)
                event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    # Envoyer 5 événements
    start_time = time.time()
    for i in range(5):
        event_queue.put((f"event{i}", {}, "source"))

    # Attendre
    event_queue.join()
    total_time = time.time() - start_time

    # Arrêter
    stop_worker = True
    event_queue.put((None, None, None))
    worker_thread.join(timeout=2)

    # Vérifier le timing
    assert len(processed_events) == 5
    assert processed_events == [f"event{i}" for i in range(5)]

    # Le temps total devrait être au moins 5*0.05 = 0.25s (séquentiel)
    # Si c'était parallèle, ce serait ~0.05s
    assert total_time >= 0.2, f"Le traitement devrait prendre au moins 0.25s (séquentiel), pris: {total_time}s"

    # Vérifier que les événements sont espacés (traitement séquentiel)
    for i in range(1, len(processing_times)):
        time_diff = processing_times[i] - processing_times[i-1]
        # Chaque événement devrait être traité ~0.05s après le précédent
        assert time_diff >= 0.04, f"Les événements doivent être espacés (séquentiel): {time_diff}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
