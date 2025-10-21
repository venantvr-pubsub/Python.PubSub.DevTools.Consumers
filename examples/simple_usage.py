"""
Exemple simple d'utilisation de la librairie python-pubsub-devtools-consumers.

Ce script démontre l'API simplifiée où toute la logique Flask/HTTP/JSON
est encapsulée dans la librairie.
"""
import time

from python_pubsub_devtools_consumers import (
    DevToolsPlayerProxy,
    DevToolsRecorderProxy,
    find_free_port
)


def example_recorder():
    """Exemple d'utilisation du recorder."""
    print("=== RECORDER EXAMPLE ===\n")

    # Configuration simple
    recorder = DevToolsRecorderProxy(
        devtools_url="http://localhost:5556"
    )

    # Démarrer une session d'enregistrement
    print("Starting recording session...")
    if recorder.start_session("example-session"):
        print("✓ Recording started\n")

        # Enregistrer des événements
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
    """Exemple d'utilisation du player avec handler simple."""
    print("=== PLAYER EXAMPLE (Simplified API) ===\n")

    # Handler simple - reçoit juste les données déjà parsées
    def handle_event(event_name: str, event_data: dict, source: str) -> bool:
        """
        Handler ultra-simple qui traite l'événement.
        Pas besoin de connaître Flask, JSON, HTTP, etc.

        Args:
            event_name: Nom de l'événement
            event_data: Données de l'événement (déjà parsées!)
            source: Source de l'événement

        Returns:
            True si succès, False si erreur
        """
        print(f"[REPLAY] Event: {event_name}")
        print(f"[REPLAY] From: {source}")
        print(f"[REPLAY] Data: {event_data}")
        print("-" * 50)

        # Votre logique métier ici
        # Par exemple: sauvegarder en DB, envoyer à Kafka, etc.

        return True  # Succès

    # Configuration simple - un seul paramètre requis!
    player = DevToolsPlayerProxy(
        consumer_name="example-consumer",
        event_handler=handle_event  # Handler simple
    )

    print(f"Starting player on {player.player_url}...")
    if player.start():
        print("✓ Player started and registered\n")
        print(f"Player listening on: {player.player_url}")
        print(f"Is registered: {player.is_registered}")
        print("\nPlayer is now ready to receive events.")
        print("Use DevTools UI to send events.")
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


def example_custom_business_logic():
    """Exemple avec logique métier personnalisée."""
    print("=== CUSTOM BUSINESS LOGIC EXAMPLE ===\n")

    # Logique métier plus complexe
    class EventProcessor:

        def __init__(self):
            self.events_processed = 0

        def process(self, event_name: str, event_data: dict, source: str) -> bool:
            """Processeur d'événements avec logique métier."""
            self.events_processed += 1

            print(f"Processing event #{self.events_processed}: {event_name}")

            # Validation métier
            if event_name.startswith("user."):
                if "id" not in event_data:
                    print(f"  ✗ Validation failed: missing 'id' field")
                    return False

            # Traitement
            print(f"  ✓ Event processed successfully")

            # Vous pourriez ici:
            # - Sauvegarder en base de données
            # - Envoyer à Kafka
            # - Appeler d'autres services
            # - Transformer les données
            # - etc.

            return True

    processor = EventProcessor()

    player = DevToolsPlayerProxy(
        consumer_name="business-consumer",
        event_handler=processor.process  # Méthode de classe
    )

    print(f"Player configured with custom business logic")
    print(f"Player URL: {player.player_url}\n")


def example_error_handling():
    """Exemple avec gestion d'erreurs."""
    print("=== ERROR HANDLING EXAMPLE ===\n")

    def handle_with_errors(event_name: str, event_data: dict, source: str) -> bool:
        """Handler qui gère les erreurs."""
        try:
            print(f"Processing: {event_name}")

            # Simuler une validation
            if event_name == "invalid.event":
                print("  ✗ Invalid event type")
                return False  # Échec

            if not isinstance(event_data, dict):
                print("  ✗ Invalid data format")
                return False

            # Traitement normal
            print(f"  ✓ Success")
            return True

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            return False  # Échec

    player = DevToolsPlayerProxy(
        consumer_name="error-handler-consumer",
        event_handler=handle_with_errors
    )

    print(f"Player with error handling: {player.player_url}\n")


def example_custom_config():
    """Exemple avec configuration avancée."""
    print("=== CUSTOM CONFIGURATION EXAMPLE ===\n")

    # Trouver un port libre dans une plage spécifique
    free_port = find_free_port(start_port=20000, end_port=21000)
    print(f"Found free port: {free_port}\n")

    def simple_handler(event_name, event_data, source):
        print(f"Received: {event_name}")
        return True

    # Configuration avancée
    player = DevToolsPlayerProxy(
        consumer_name="custom-consumer",
        event_handler=simple_handler,
        devtools_url="http://localhost:5556",
        player_port=free_port,
        player_host="localhost",
        auto_find_port=False
    )

    print(f"Player configured with custom settings:")
    print(f"  - URL: {player.player_url}")
    print(f"  - Endpoint: {player.player_endpoint} (auto-generated)")
    print(f"  - DevTools: {player.devtools_url}")
    print()


def example_sequential_processing():
    """Exemple avec traitement séquentiel (évite les race conditions)."""
    print("=== SEQUENTIAL PROCESSING EXAMPLE ===\n")

    # Simuler un état partagé qui pourrait avoir des race conditions
    class EventCounter:

        def __init__(self):
            self.count = 0
            self.processed_events = []

        def handle_event(self, event_name: str, event_data: dict, source: str) -> bool:
            """
            Handler qui modifie un état partagé.
            Sans sequential_processing=True, il y aurait des race conditions!
            """
            import time

            # Simuler un traitement qui prend du temps
            time.sleep(0.1)

            # Incrémenter le compteur (opération non-atomique)
            self.count += 1
            self.processed_events.append(event_name)

            print(f"[{self.count}] Processed: {event_name} from {source}")
            return True

    counter = EventCounter()

    # Créer le player avec traitement séquentiel
    player = DevToolsPlayerProxy(
        consumer_name="sequential-consumer",
        event_handler=counter.handle_event,
        sequential_processing=True  # ✅ Garantit l'ordre et évite les race conditions
    )

    print(f"Player configured with sequential processing:")
    print(f"  - URL: {player.player_url}")
    print(f"  - Sequential: {player.sequential_processing}")
    print(f"\nStarting player...\n")

    if player.start():
        print("✓ Player started\n")
        print("Player is now processing events SEQUENTIALLY.")
        print("Events are queued and processed one at a time.")
        print("This eliminates race conditions!")
        print("\nSend multiple events simultaneously from DevTools")
        print("and they will be processed in order.\n")
        print("Press Ctrl+C to stop...\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping player...")
            player.stop()  # Arrêt propre avec attente de la queue
            print(f"✓ Player stopped")
            print(f"\nTotal events processed: {counter.count}")
            print(f"Events: {counter.processed_events}\n")
    else:
        print("✗ Failed to start player (DevTools not running?)\n")


if __name__ == "__main__":
    print("Python PubSub DevTools Consumers - Examples (Simplified API)")
    print("=" * 70)
    print()

    # Choisir l'exemple à exécuter
    print("Choose an example:")
    print("1. Recorder example")
    print("2. Player example (Simple handler)")
    print("3. Custom business logic")
    print("4. Error handling")
    print("5. Custom configuration")
    print("6. Sequential processing (no race conditions)")
    print()

    choice = input("Enter choice (1/2/3/4/5/6): ").strip()

    print("\n" + "=" * 70 + "\n")

    if choice == "1":
        example_recorder()
    elif choice == "2":
        example_player()
    elif choice == "3":
        example_custom_business_logic()
    elif choice == "4":
        example_error_handling()
    elif choice == "5":
        example_custom_config()
    elif choice == "6":
        example_sequential_processing()
    else:
        print("Invalid choice!")

    print("=" * 70)
