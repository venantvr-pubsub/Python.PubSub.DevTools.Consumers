"""
Démonstration du bug task_done() et de sa correction.

Ce script montre ce qui se passe AVANT et APRÈS la correction du bug
où task_done() n'était pas appelé pour le signal d'arrêt.
"""
import queue
import threading
import time
import signal
import sys


def demo_bug_version():
    """
    Démo de la version BUGGÉE (avant correction).

    ATTENTION: Cette démo va se bloquer volontairement pour montrer le bug !
    Elle timeout après 3 secondes.
    """
    print("🔴 VERSION BUGGÉE (AVANT correction)")
    print("-" * 60)
    print("Cette version ne call pas task_done() pour le signal d'arrêt.")
    print()

    event_queue = queue.Queue()
    stop_worker = False
    processed = []

    def buggy_worker():
        """Worker avec le BUG : task_done() pas appelé si None."""
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # BUG: Si on break ici, on ne rentre jamais dans le try ci-dessous
                if event_name is None:
                    processed.append("STOP_SIGNAL")
                    break  # ← BUG: Sort avant le finally !

                # Le finally est ici, mais on n'y arrive jamais si break
                try:
                    processed.append(event_name)
                finally:
                    event_queue.task_done()  # ← Jamais atteint si break !

            except Exception as e:
                print(f"Error: {e}")

    # Démarrer le worker
    worker = threading.Thread(target=buggy_worker, daemon=True)
    worker.start()
    time.sleep(0.1)

    # Envoyer des événements
    print("Envoi de 2 événements normaux + 1 signal d'arrêt...")
    event_queue.put(("event1", {}, "source"))
    event_queue.put(("event2", {}, "source"))
    event_queue.put((None, None, None))  # Signal d'arrêt

    # Tenter de join avec timeout
    print("Appel de queue.join() (va bloquer !)...")
    start = time.time()

    # Créer un timeout pour éviter de bloquer indéfiniment
    def timeout_handler(signum, frame):
        raise TimeoutError("BLOCAGE DÉTECTÉ!")

    # Protection contre le blocage (Linux/Mac seulement)
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3)  # Timeout de 3 secondes

        event_queue.join()  # ← Va bloquer ici car task_done() pas appelé !

        signal.alarm(0)  # Annuler l'alarme
    except (TimeoutError, AttributeError) as e:
        # AttributeError sur Windows (pas de SIGALRM)
        elapsed = time.time() - start
        print(f"❌ BLOCAGE après {elapsed:.1f}s!")
        print(f"   Raison: task_done() pas appelé pour le signal d'arrêt")
        print(f"   Queue size: {event_queue.qsize()}")
        print()
        return False

    print("✅ Pas de blocage (étonnant!)")
    return True


def demo_fixed_version():
    """
    Démo de la version CORRIGÉE (après correction).
    """
    print("✅ VERSION CORRIGÉE (APRÈS correction)")
    print("-" * 60)
    print("Cette version call TOUJOURS task_done(), même pour le signal d'arrêt.")
    print()

    event_queue = queue.Queue()
    stop_worker = False
    processed = []

    def fixed_worker():
        """Worker CORRIGÉ : task_done() toujours appelé."""
        while not stop_worker:
            try:
                try:
                    event_name, event_data, source = event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # CORRECTION: finally englobe tout
                try:
                    if event_name is None:
                        processed.append("STOP_SIGNAL")
                        return  # Sortie propre

                    processed.append(event_name)

                finally:
                    # ✅ TOUJOURS appelé, même si return !
                    event_queue.task_done()

            except Exception as e:
                print(f"Error: {e}")

    # Démarrer le worker
    worker = threading.Thread(target=fixed_worker, daemon=True)
    worker.start()
    time.sleep(0.1)

    # Envoyer des événements
    print("Envoi de 2 événements normaux + 1 signal d'arrêt...")
    event_queue.put(("event1", {}, "source"))
    event_queue.put(("event2", {}, "source"))
    event_queue.put((None, None, None))  # Signal d'arrêt

    # Join devrait réussir sans blocage
    print("Appel de queue.join()...")
    start = time.time()

    event_queue.join()  # ✅ Ne bloque pas !

    elapsed = time.time() - start
    print(f"✅ Succès en {elapsed:.2f}s!")
    print(f"   Événements traités: {processed}")
    print()

    # Attendre que le worker se termine
    worker.join(timeout=1.0)
    return True


def main():
    """Programme principal."""
    print()
    print("=" * 60)
    print("DÉMONSTRATION : BUG task_done() dans la Queue")
    print("=" * 60)
    print()
    print("Ce bug est un classique du multithreading en Python :")
    print("Si task_done() n'est pas appelé après CHAQUE get(),")
    print("alors queue.join() attendra indéfiniment.")
    print()
    print("=" * 60)
    print()

    # Test 1 : Version buggée
    try:
        blocked = not demo_bug_version()
    except Exception as e:
        print(f"❌ Exception: {e}")
        blocked = True

    time.sleep(0.5)

    # Test 2 : Version corrigée
    demo_fixed_version()

    # Résumé
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print()
    if blocked:
        print("❌ Version BUGGÉE : Se bloque à queue.join()")
        print("   → task_done() pas appelé pour le signal d'arrêt")
        print()
        print("✅ Version CORRIGÉE : Aucun blocage")
        print("   → task_done() toujours appelé grâce au finally")
        print()
        print("RÈGLE D'OR : task_done() doit être appelé pour CHAQUE get() réussi,")
        print("             y compris pour les signaux de contrôle (None, etc.)")
    else:
        print("✅ Les deux versions fonctionnent (timing chanceux?)")

    print()
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterruption clavier détectée.")
        sys.exit(0)
