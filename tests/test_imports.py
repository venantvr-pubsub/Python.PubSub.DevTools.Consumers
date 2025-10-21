"""Tests de base pour vérifier que tous les modules s'importent correctement."""
import pytest


def test_main_imports():
    """Test que tous les exports principaux s'importent correctement."""
    from python_pubsub_devtools_consumers import (
        DevToolsPlayerProxy,
        DevToolsRecorderProxy,
        find_free_port,
    )

    assert DevToolsPlayerProxy is not None
    assert DevToolsRecorderProxy is not None
    assert find_free_port is not None


def test_port_utils():
    """Test des utilitaires de port."""
    from python_pubsub_devtools_consumers import find_free_port
    from python_pubsub_devtools_consumers.port_utils import is_port_available

    # Trouver un port libre
    port = find_free_port(start_port=50000, end_port=51000)
    assert 50000 <= port < 51000

    # Le port trouvé devrait être disponible (au moment du test)
    assert isinstance(is_port_available(port), bool)


def test_recorder_instantiation():
    """Test l'instantiation du recorder."""
    from python_pubsub_devtools_consumers import DevToolsRecorderProxy

    recorder = DevToolsRecorderProxy(devtools_url="http://localhost:5556")
    assert recorder.devtools_url == "http://localhost:5556"
    assert recorder.is_recording is False


def test_player_instantiation():
    """Test l'instantiation du player avec handler simple."""
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    def simple_handler(event_name, event_data, source):
        """Handler simple qui retourne toujours True."""
        return True

    player = DevToolsPlayerProxy(
        consumer_name="test-consumer",
        event_handler=simple_handler
    )

    assert player.consumer_name == "test-consumer"
    assert player.devtools_url == "http://localhost:5556"
    assert player.is_registered is False


def test_player_custom_config():
    """Test la configuration personnalisée du player."""
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    def simple_handler(event_name, event_data, source):
        return True

    player = DevToolsPlayerProxy(
        consumer_name="test-consumer",
        event_handler=simple_handler,
        devtools_url="http://localhost:5556",
        player_port=9999,
        auto_find_port=False,
    )

    assert player.player_port == 9999
    assert "9999" in player.player_url
    # L'endpoint est généré automatiquement (aléatoire)
    assert player.player_endpoint.startswith("/")
    assert len(player.player_endpoint) == 9  # '/' + 8 caractères


def test_recorder_custom_config():
    """Test la configuration personnalisée du recorder."""
    from python_pubsub_devtools_consumers import DevToolsRecorderProxy

    recorder = DevToolsRecorderProxy(
        devtools_url="http://localhost:8888",
        event_endpoint="/custom/event",
        timeout=15,
    )

    assert recorder.devtools_url == "http://localhost:8888"
    assert recorder.event_endpoint == "/custom/event"
    assert recorder.timeout == 15


def test_event_handler_return_values():
    """Test que le handler peut retourner True/False."""
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    # Handler qui retourne True
    def success_handler(event_name, event_data, source):
        return True

    player1 = DevToolsPlayerProxy(
        consumer_name="success-consumer",
        event_handler=success_handler
    )
    assert player1.event_handler("test", {}, "source") is True

    # Handler qui retourne False
    def failure_handler(event_name, event_data, source):
        return False

    player2 = DevToolsPlayerProxy(
        consumer_name="failure-consumer",
        event_handler=failure_handler
    )
    assert player2.event_handler("test", {}, "source") is False


def test_event_handler_signature():
    """Test que le handler reçoit les bons paramètres."""
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    received = {}

    def capture_handler(event_name, event_data, source):
        received['event_name'] = event_name
        received['event_data'] = event_data
        received['source'] = source
        return True

    player = DevToolsPlayerProxy(
        consumer_name="capture-consumer",
        event_handler=capture_handler
    )

    # Simuler un appel
    player.event_handler("test_event", {"key": "value"}, "test_source")

    assert received['event_name'] == "test_event"
    assert received['event_data'] == {"key": "value"}
    assert received['source'] == "test_source"


def test_sequential_processing_mode():
    """Test le mode sequential_processing."""
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    def simple_handler(event_name, event_data, source):
        return True

    # Player avec sequential_processing activé
    player = DevToolsPlayerProxy(
        consumer_name="seq-consumer",
        event_handler=simple_handler,
        sequential_processing=True
    )

    assert player.sequential_processing is True
    assert player._event_queue is not None
    assert player._worker_thread is None  # Pas encore démarré
    assert player._stop_worker is False


def test_sequential_processing_disabled():
    """Test le mode par défaut (sans sequential_processing)."""
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    def simple_handler(event_name, event_data, source):
        return True

    # Player sans sequential_processing (défaut)
    player = DevToolsPlayerProxy(
        consumer_name="normal-consumer",
        event_handler=simple_handler
    )

    assert player.sequential_processing is False
    assert player._event_queue is None
    assert player._worker_thread is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
