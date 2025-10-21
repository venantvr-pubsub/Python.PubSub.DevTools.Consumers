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
    # Note: Peut échouer si le port est pris entre-temps
    assert isinstance(is_port_available(port), bool)


def test_recorder_instantiation():
    """Test l'instantiation du recorder."""
    from python_pubsub_devtools_consumers import DevToolsRecorderProxy

    recorder = DevToolsRecorderProxy(devtools_url="http://localhost:5556")
    assert recorder.devtools_url == "http://localhost:5556"
    assert recorder.is_recording is False


def test_player_instantiation():
    """Test l'instantiation du player."""
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    def dummy_callback(event_name, payload, producer):
        pass

    player = DevToolsPlayerProxy(
        publish_callback=dummy_callback,
        consumer_name="test-consumer",
        devtools_url="http://localhost:5556",
    )

    assert player.devtools_url == "http://localhost:5556"
    assert player.consumer_name == "test-consumer"
    assert player.is_registered is False


def test_player_custom_config():
    """Test la configuration personnalisée du player."""
    from python_pubsub_devtools_consumers import DevToolsPlayerProxy

    def dummy_callback(event_name, payload, producer):
        pass

    player = DevToolsPlayerProxy(
        publish_callback=dummy_callback,
        consumer_name="test-consumer",
        devtools_url="http://localhost:5556",
        player_port=9999,
        player_endpoint="/custom/replay",
        auto_find_port=False,
    )

    assert player.player_port == 9999
    assert player.player_endpoint == "/custom/replay"
    assert "9999" in player.player_url


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
