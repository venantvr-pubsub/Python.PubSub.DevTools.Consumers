"""
Tests pour vérifier le traitement séquentiel des événements.

Ces tests vérifient que les événements sont traités dans l'ordre
lorsque sequential_processing=True.
"""
import pytest
import threading
import time
from unittest.mock import MagicMock, patch


def test_sequential_order_with_queue():
    """
    Test que les événements sont traités dans l'ordre avec sequential_processing=True.
    """
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    # Liste pour capturer l'ordre des événements traités
    processed_events = []
    processing_times = []

    def handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler qui enregistre l'ordre de traitement."""
        # Simuler un traitement qui prend du temps
        time.sleep(0.05)
        processed_events.append(event_name)
        processing_times.append(time.time())
        return True

    # Créer un player avec traitement séquentiel
    player = DevToolsPlayerProxy(
        consumer_name="test-sequential",
        event_handler=handler,
        sequential_processing=True,
        player_port=19999,
        auto_find_port=False
    )

    # Vérifier que la queue est créée
    assert player._event_queue is not None
    assert player._event_queue.qsize() == 0

    # Démarrer le worker thread
    player._stop_worker = False
    player._worker_thread = threading.Thread(
        target=player._worker_loop,
        daemon=True
    )
    player._worker_thread.start()

    # Attendre un peu que le worker démarre
    time.sleep(0.1)

    # Envoyer plusieurs événements dans la queue rapidement
    events_to_send = ["event1", "event2", "event3", "event4", "event5"]
    for event_name in events_to_send:
        player._event_queue.put((event_name, {"data": "test"}, "test-source"))

    # Attendre que tous les événements soient traités
    player._event_queue.join()

    # Arrêter le worker
    player._stop_worker = True
    player._event_queue.put((None, None, None))  # Signal d'arrêt
    player._worker_thread.join(timeout=2)

    # Vérifications
    assert len(processed_events) == 5, "Tous les événements doivent être traités"
    assert processed_events == events_to_send, "Les événements doivent être traités dans l'ordre"

    # Vérifier que les événements ont été traités séquentiellement (pas en parallèle)
    # Chaque événement prend ~0.05s, donc ils doivent être espacés
    for i in range(1, len(processing_times)):
        time_diff = processing_times[i] - processing_times[i-1]
        assert time_diff >= 0.04, f"Les événements doivent être traités séquentiellement (diff={time_diff})"


def test_sequential_handler_can_fail():
    """
    Test que le worker continue même si un handler échoue.
    """
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    processed_events = []
    success_count = 0
    failure_count = 0

    def handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler qui échoue sur event2."""
        processed_events.append(event_name)
        if event_name == "event2":
            return False  # Échec
        return True

    player = DevToolsPlayerProxy(
        consumer_name="test-failures",
        event_handler=handler,
        sequential_processing=True,
        player_port=19998,
        auto_find_port=False
    )

    # Démarrer le worker
    player._stop_worker = False
    player._worker_thread = threading.Thread(
        target=player._worker_loop,
        daemon=True
    )
    player._worker_thread.start()
    time.sleep(0.1)

    # Envoyer des événements
    player._event_queue.put(("event1", {}, "source"))
    player._event_queue.put(("event2", {}, "source"))  # Celui-ci va échouer
    player._event_queue.put(("event3", {}, "source"))

    # Attendre
    player._event_queue.join()

    # Arrêter
    player._stop_worker = True
    player._event_queue.put((None, None, None))
    player._worker_thread.join(timeout=2)

    # Vérifier que tous les événements ont été traités malgré l'échec
    assert len(processed_events) == 3
    assert processed_events == ["event1", "event2", "event3"]


def test_sequential_handler_exception():
    """
    Test que le worker continue même si un handler lève une exception.
    """
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    processed_events = []

    def handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler qui lève une exception sur event2."""
        processed_events.append(event_name)
        if event_name == "event2":
            raise ValueError("Simulated error")
        return True

    player = DevToolsPlayerProxy(
        consumer_name="test-exceptions",
        event_handler=handler,
        sequential_processing=True,
        player_port=19997,
        auto_find_port=False
    )

    # Démarrer le worker
    player._stop_worker = False
    player._worker_thread = threading.Thread(
        target=player._worker_loop,
        daemon=True
    )
    player._worker_thread.start()
    time.sleep(0.1)

    # Envoyer des événements
    player._event_queue.put(("event1", {}, "source"))
    player._event_queue.put(("event2", {}, "source"))  # Celui-ci va lever une exception
    player._event_queue.put(("event3", {}, "source"))

    # Attendre
    player._event_queue.join()

    # Arrêter
    player._stop_worker = True
    player._event_queue.put((None, None, None))
    player._worker_thread.join(timeout=2)

    # Vérifier que tous les événements ont été traités malgré l'exception
    assert len(processed_events) == 3
    assert processed_events == ["event1", "event2", "event3"]


def test_queue_size_tracking():
    """
    Test que la taille de la queue est correctement suivie.
    """
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    def slow_handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler lent pour accumuler des événements dans la queue."""
        time.sleep(0.2)
        return True

    player = DevToolsPlayerProxy(
        consumer_name="test-queue-size",
        event_handler=slow_handler,
        sequential_processing=True,
        player_port=19996,
        auto_find_port=False
    )

    # Démarrer le worker
    player._stop_worker = False
    player._worker_thread = threading.Thread(
        target=player._worker_loop,
        daemon=True
    )
    player._worker_thread.start()
    time.sleep(0.1)

    # Envoyer rapidement plusieurs événements
    for i in range(5):
        player._event_queue.put((f"event{i}", {}, "source"))

    # La queue devrait avoir des éléments
    initial_size = player._event_queue.qsize()
    assert initial_size > 0, "La queue devrait contenir des événements"

    # Attendre que tout soit traité
    player._event_queue.join()

    # La queue devrait être vide
    final_size = player._event_queue.qsize()
    assert final_size == 0, "La queue devrait être vide après traitement"

    # Arrêter
    player._stop_worker = True
    player._event_queue.put((None, None, None))
    player._worker_thread.join(timeout=2)


def test_stop_method_waits_for_queue():
    """
    Test que la méthode stop() attend que la queue se vide.
    """
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    processed_events = []

    def handler(event_name: str, event_data: dict, source: str) -> bool:
        """Handler qui enregistre les événements traités."""
        time.sleep(0.05)
        processed_events.append(event_name)
        return True

    player = DevToolsPlayerProxy(
        consumer_name="test-stop",
        event_handler=handler,
        sequential_processing=True,
        player_port=19995,
        auto_find_port=False
    )

    # Démarrer le worker
    player._stop_worker = False
    player._worker_thread = threading.Thread(
        target=player._worker_loop,
        daemon=True
    )
    player._worker_thread.start()
    time.sleep(0.1)

    # Envoyer des événements
    for i in range(5):
        player._event_queue.put((f"event{i}", {}, "source"))

    # Appeler stop() qui devrait attendre que tout soit traité
    start_time = time.time()
    player.stop(timeout=5.0)
    elapsed = time.time() - start_time

    # Vérifier que stop() a attendu (devrait prendre au moins 5*0.05 = 0.25s)
    assert elapsed >= 0.2, "stop() devrait attendre que la queue se vide"

    # Tous les événements doivent avoir été traités
    assert len(processed_events) == 5
    assert processed_events == [f"event{i}" for i in range(5)]


def test_non_sequential_mode_still_works():
    """
    Test que le mode non-séquentiel (défaut) fonctionne toujours.
    """
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    processed_events = []

    def handler(event_name: str, event_data: dict, source: str) -> bool:
        processed_events.append(event_name)
        return True

    # Player SANS sequential_processing
    player = DevToolsPlayerProxy(
        consumer_name="test-non-seq",
        event_handler=handler,
        sequential_processing=False  # Mode par défaut
    )

    # Pas de queue créée
    assert player._event_queue is None
    assert player._worker_thread is None

    # Appeler le handler directement fonctionne toujours
    result = player.event_handler("test_event", {"data": "test"}, "source")
    assert result is True
    assert processed_events == ["test_event"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
