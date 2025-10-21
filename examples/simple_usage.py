"""
Exemple simple d'utilisation de la librairie python-pubsub-devtools-consumers.

Ce script démontre comment utiliser les proxies player et recorder avec
des configurations personnalisées.
"""
import time

from python_pubsub_devtools_consumers import (
    DevToolsPlayerProxy,
    DevToolsRecorderProxy,
    find_free_port
)


def my_event_handler(event_name: str, payload: dict, producer: str):
    """Callback appelée quand un événement est rejoué."""
    print(f"[REPLAY] Event: {event_name}")
    print(f"[REPLAY] From: {producer}")
    print(f"[REPLAY] Payload: {payload}")
    print("-" * 50)


def example_recorder():
    """Exemple d'utilisation du recorder."""
    print("=== RECORDER EXAMPLE ===\n")

    # Configuration simple avec URL
    recorder = DevToolsRecorderProxy(
        devtools_url="http://localhost:5556"
    )

    # Démarrer une session d'enregistrement
    print("Starting recording session...")
    if recorder.start_session("example-session"):
        print("✓ Recording started\n")

        # Simuler l'enregistrement d'événements
        print("Recording events...")
        recorder.record_event(
            "user.created",
            {"id": 1, "name": "Alice"},
            "example-service"
        )
        recorder.record_event(
            "user.updated",
            {"id": 1, "email": "alice@example.com"},
            "example-service"
        )
        print("✓ Events recorded\n")

        # Arrêter et sauvegarder
        time.sleep(1)
        print("Stopping recording...")
        if recorder.stop_session():
            print("✓ Recording saved\n")
    else:
        print("✗ Failed to start recording (DevTools not running?)\n")


def example_player():
    """Exemple d'utilisation du player."""
    print("=== PLAYER EXAMPLE ===\n")

    # Configuration avec port automatique
    player = DevToolsPlayerProxy(
        publish_callback=my_event_handler,
        consumer_name="example-consumer",
        devtools_url="http://localhost:5556",
        # Le port sera trouvé automatiquement
    )

    print(f"Starting player on {player.player_url}...")
    if player.start():
        print("✓ Player started and registered\n")
        print(f"Player listening on: {player.player_url}")
        print(f"Is registered: {player.is_registered}")
        print("\nPlayer is now ready to receive replayed events.")
        print("Use DevTools UI to replay events.")
        print("\nPress Ctrl+C to stop...\n")

        try:
            # Garder le player actif
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping player...")
            player.unregister()
            print("✓ Player stopped\n")
    else:
        print("✗ Failed to start player (DevTools not running?)\n")


def example_custom_config():
    """Exemple avec configuration personnalisée."""
    print("=== CUSTOM CONFIGURATION EXAMPLE ===\n")

    # Trouver un port libre dans une plage spécifique
    free_port = find_free_port(start_port=20000, end_port=21000)
    print(f"Found free port: {free_port}\n")

    # Configuration avancée du player
    player = DevToolsPlayerProxy(
        publish_callback=my_event_handler,
        consumer_name="custom-consumer",
        devtools_url="http://localhost:5556",
        player_port=free_port,  # Port spécifique
        player_host="localhost",
        player_endpoint="/custom/replay",
        register_endpoint="/api/player/register",
        auto_find_port=False  # Désactiver la recherche auto
    )

    print(f"Player configured with custom settings:")
    print(f"  - URL: {player.player_url}")
    print(f"  - Endpoint: {player.player_endpoint}")
    print(f"  - DevTools: {player.devtools_url}")
    print()

    # Configuration avancée du recorder
    recorder = DevToolsRecorderProxy(
        devtools_url="http://localhost:5556",
        timeout=10,  # Timeout personnalisé
        event_endpoint="/api/record/event"
    )

    print(f"Recorder configured with custom settings:")
    print(f"  - DevTools: {recorder.devtools_url}")
    print(f"  - Timeout: {recorder.timeout}s")
    print()


if __name__ == "__main__":
    print("Python PubSub DevTools Consumers - Examples")
    print("=" * 60)
    print()

    # Choisir l'exemple à exécuter
    print("Choose an example:")
    print("1. Recorder example")
    print("2. Player example")
    print("3. Custom configuration example")
    print()

    choice = input("Enter choice (1/2/3): ").strip()

    print("\n" + "=" * 60 + "\n")

    if choice == "1":
        example_recorder()
    elif choice == "2":
        example_player()
    elif choice == "3":
        example_custom_config()
    else:
        print("Invalid choice!")

    print("=" * 60)
