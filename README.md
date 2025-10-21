# Python PubSub DevTools Consumers

Librairie générique pour les proxies DevTools permettant l'enregistrement et la relecture d'événements PubSub.

## Installation

```bash
pip install -e /path/to/Python.PubSub.DevTools.Consumers
```

## Fonctionnalités

- **Player Proxy**: Reçoit et rejoue les événements depuis DevTools
- **Recorder Proxy**: Enregistre les événements vers DevTools
- **Port Utils**: Utilitaires pour trouver des ports libres automatiquement
- **Configuration injectable**: Tous les paramètres (URLs, ports, endpoints) sont configurables

## Utilisation

### Player Proxy

```python
from python_pubsub_devtools_consumers import DevToolsPlayerProxy


def my_publish_callback(event_name: str, payload: dict, producer: str):
    """Callback appelée lors de la réception d'événements."""
    print(f"Received event {event_name} from {producer}: {payload}")


# Configuration basique (port automatique)
player = DevToolsPlayerProxy(
    publish_callback=my_publish_callback,
    consumer_name="my-consumer",
    devtools_url="http://localhost:5556"
)

# Démarrer le serveur et s'enregistrer
if player.start():
    print(f"Player running on {player.player_url}")
    # Le serveur tourne en background...

# Désenregistrer quand terminé
player.unregister()
```

### Configuration avancée du Player

```python
player = DevToolsPlayerProxy(
    publish_callback=my_publish_callback,
    consumer_name="my-consumer",
    devtools_url="http://devtools.example.com:8080",
    player_port=9000,  # Port fixe au lieu d'auto
    player_host="192.168.1.10",  # Hôte personnalisé
    player_endpoint="/custom/replay",  # Endpoint personnalisé
    register_endpoint="/custom/player/register",
    unregister_endpoint="/custom/player/unregister",
    port_range=(20000, 30000),  # Plage de ports personnalisée
    auto_find_port=False  # Désactiver la recherche auto de port
)
```

### Recorder Proxy

```python
from python_pubsub_devtools_consumers import DevToolsRecorderProxy

# Configuration basique
recorder = DevToolsRecorderProxy(
    devtools_url="http://localhost:5556"
)

# Démarrer une session d'enregistrement
recorder.start_session("test-session")

# Enregistrer des événements
recorder.record_event("user.created", {"id": 123, "name": "John"}, "my-service")
recorder.record_event("user.updated", {"id": 123, "email": "john@example.com"}, "my-service")

# Arrêter et sauvegarder
recorder.stop_session()
```

### Configuration avancée du Recorder

```python
recorder = DevToolsRecorderProxy(
    devtools_url="http://devtools.example.com:8080",
    start_endpoint="/custom/record/start",
    event_endpoint="/custom/record/event",
    stop_endpoint="/custom/record/stop",
    timeout=10  # Timeout personnalisé
)
```

### Utilitaires de port

```python
from python_pubsub_devtools_consumers import find_free_port
from python_pubsub_devtools_consumers.port_utils import is_port_available

# Trouver un port libre
port = find_free_port(start_port=8000, end_port=9000)
print(f"Port libre trouvé: {port}")

# Vérifier si un port est disponible
if is_port_available(8080):
    print("Port 8080 disponible")
```

## Architecture

```
python_pubsub_devtools_consumers/
├── __init__.py           # API publique
├── player_proxy.py       # Proxy pour rejouer les événements
├── recorder_proxy.py     # Proxy pour enregistrer les événements
└── port_utils.py         # Utilitaires de gestion des ports
```

## Avantages de la librairie

1. **Réutilisabilité**: Utilisez les proxies DevTools dans n'importe quel projet
2. **Configuration flexible**: Tous les paramètres sont injectables
3. **Auto-configuration**: Recherche automatique de ports libres
4. **Endpoints personnalisables**: Adaptez-vous à différentes implémentations DevTools
5. **Logging intégré**: Utilise le système de logging Python standard
6. **Type hints**: Support complet des annotations de type

## Exemples d'intégration

### Avec un client PubSub

```python
from python_pubsub_devtools_consumers import DevToolsPlayerProxy, DevToolsRecorderProxy


class MyPubSubClient:

    def __init__(self):
        self.recorder = DevToolsRecorderProxy()
        self.player = DevToolsPlayerProxy(
            publish_callback=self._handle_replayed_event,
            consumer_name="my-client"
        )

    def _handle_replayed_event(self, event_name, payload, producer):
        # Publier l'événement rejoué
        self.publish(event_name, payload)

    def publish(self, event_name, payload):
        # Logique de publication...
        # Enregistrer dans DevTools
        if self.recorder.is_recording:
            self.recorder.record_event(event_name, payload, "my-client")
```

## Dépendances

- Flask >= 2.0.0
- requests >= 2.25.0
- Python >= 3.8

## Licence

MIT
