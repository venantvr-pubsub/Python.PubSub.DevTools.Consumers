"""
Démonstration des race conditions avec et sans traitement séquentiel.

Ce script montre visuellement pourquoi sequential_processing=True est important
quand on modifie un état partagé.
"""
import queue
import threading
import time


class Counter:
    """Compteur non thread-safe pour démontrer les race conditions."""

    def __init__(self):
        self.count = 0
        self.events = []

    def increment_unsafe(self, event_name: str):
        """Incrémentation NON atomique (race condition possible)."""
        # Lire la valeur actuelle
        current = self.count
        # Simuler du traitement
        time.sleep(0.001)
        # Écrire la nouvelle valeur
        self.count = current + 1
        self.events.append(event_name)


def simulate_parallel_processing(num_events: int = 20) -> Counter:
    """
    Simule le traitement PARALLÈLE (mode direct, pas de queue).
    DANGEREUX : race conditions possibles !
    """
    counter = Counter()

    def process_event(event_name: str):
        """Handler exécuté en parallèle."""
        counter.increment_unsafe(event_name)

    # Créer plusieurs threads qui modifient le compteur en parallèle
    threads = []
    for i in range(num_events):
        t = threading.Thread(target=process_event, args=(f"event{i}",))
        threads.append(t)
        t.start()

    # Attendre que tous les threads finissent
    for t in threads:
        t.join()

    return counter


def simulate_sequential_processing(num_events: int = 20) -> Counter:
    """
    Simule le traitement SÉQUENTIEL (mode queue).
    SAFE : pas de race conditions !
    """
    counter = Counter()
    event_queue = queue.Queue()
    stop_worker = False

    def process_event(event_name: str):
        """Handler exécuté séquentiellement."""
        counter.increment_unsafe(event_name)

    def worker_loop():
        """Worker qui traite les événements un par un."""
        while not stop_worker:
            try:
                event_name = event_queue.get(timeout=0.5)
                if event_name is None:
                    break
                process_event(event_name)
                event_queue.task_done()
            except queue.Empty:
                continue

    # Démarrer le worker
    worker = threading.Thread(target=worker_loop, daemon=True)
    worker.start()

    # Envoyer les événements dans la queue
    for i in range(num_events):
        event_queue.put(f"event{i}")

    # Attendre que tous soient traités
    event_queue.join()

    # Arrêter le worker
    stop_worker = True
    event_queue.put(None)
    worker.join()

    return counter


def run_demo():
    """Exécute la démonstration."""
    print("=" * 80)
    print("DÉMONSTRATION : RACE CONDITIONS")
    print("=" * 80)
    print()

    num_events = 50
    num_runs = 5

    print(f"Configuration : {num_events} événements, {num_runs} essais\n")

    # Test 1 : Traitement parallèle (avec race conditions)
    print("🔴 TEST 1 : TRAITEMENT PARALLÈLE (sequential_processing=False)")
    print("-" * 80)
    print("Chaque événement est traité dans un thread Flask séparé.")
    print("Plusieurs threads modifient le compteur EN MÊME TEMPS → race conditions!\n")

    parallel_results = []
    for run in range(num_runs):
        result = simulate_parallel_processing(num_events)
        parallel_results.append(result.count)
        print(f"  Essai {run + 1}: count = {result.count} (attendu: {num_events})")

    avg_parallel = sum(parallel_results) / len(parallel_results)
    print(f"\n  Moyenne: {avg_parallel:.1f} / {num_events}")

    if avg_parallel < num_events:
        print(f"  ⚠️  PERTE: {num_events - avg_parallel:.1f} événements perdus en moyenne!")
        print("  ❌ Race conditions détectées!\n")
    else:
        print("  ✅ Aucune race condition (vous avez eu de la chance!)\n")

    # Test 2 : Traitement séquentiel (sans race conditions)
    print("✅ TEST 2 : TRAITEMENT SÉQUENTIEL (sequential_processing=True)")
    print("-" * 80)
    print("Les événements sont mis en queue et traités UN PAR UN.")
    print("Un seul thread traite les événements → pas de race conditions!\n")

    sequential_results = []
    for run in range(num_runs):
        result = simulate_sequential_processing(num_events)
        sequential_results.append(result.count)
        print(f"  Essai {run + 1}: count = {result.count} (attendu: {num_events})")

    avg_sequential = sum(sequential_results) / len(sequential_results)
    print(f"\n  Moyenne: {avg_sequential:.1f} / {num_events}")

    if avg_sequential == num_events:
        print("  ✅ Aucune perte d'événement!")
        print("  ✅ Traitement séquentiel garantit l'intégrité!\n")
    else:
        print("  ❌ Erreur inattendue!\n")

    # Résumé
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print()
    print(f"Mode PARALLÈLE  : {avg_parallel:.1f}/{num_events} événements traités")
    print(f"Mode SÉQUENTIEL : {avg_sequential:.1f}/{num_events} événements traités")
    print()

    if avg_parallel < num_events:
        loss_percent = ((num_events - avg_parallel) / num_events) * 100
        print(f"❌ Perte en mode parallèle : {loss_percent:.1f}%")
        print()
        print("RECOMMANDATION : Utilisez sequential_processing=True si votre")
        print("handler modifie un état partagé (DB, variables, fichiers, etc.)")
    else:
        print("✅ Aucune race condition détectée dans cette exécution.")
        print("⚠️  Mais elles peuvent survenir sous charge réelle!")

    print()
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
