# Guide de Migration

Ce document explique comment migrer du code utilisant les anciens proxies DevTools locaux vers la nouvelle librairie générique `python-pubsub-devtools-consumers`.

## Changements Principaux

### 1. Imports

**Avant :**

```python
from .devtools_player_proxy import DevToolsPlayerProxy
from .devtools_recorder_proxy import DevToolsRecorderProxy
```

**Après :**

```python
from python_pubsub_devtools_consumers import DevToolsPlayerProxy, DevToolsRecorderProxy
```

### 2. Configuration du Recorder

**Avant :**

```python
recorder = DevToolsRecorderProxy(
    devtools_host='localhost',
    devtools_port=5556
)
```

**Après :**

```python
recorder = DevToolsRecorderProxy(
    devtools_url='http://localhost:5556'
)
```

### 3. Configuration du Player

**Avant :**

```python
player = DevToolsPlayerProxy(
    publish_callback=my_callback,
    consumer_name='my-consumer',
    devtools_host='localhost',
    devtools_port=5556
)
```

**Après :**

```python
player = DevToolsPlayerProxy(
    publish_callback=my_callback,
    consumer_name='my-consumer',
    devtools_url='http://localhost:5556'
)
```

## Nouvelles Fonctionnalités

### 1. Gestion Avancée des Ports

La nouvelle librairie offre plus de contrôle sur les ports :

```python
# Port automatique (défaut)
player = DevToolsPlayerProxy(
    publish_callback=my_callback,
    consumer_name='my-consumer',
    devtools_url='http://localhost:5556'
    # Port trouvé automatiquement entre 10001 et 65535
)

# Port spécifique
player = DevToolsPlayerProxy(
    publish_callback=my_callback,
    consumer_name='my-consumer',
    devtools_url='http://localhost:5556',
    player_port=9000,
    auto_find_port=False
)

# Plage de ports personnalisée
player = DevToolsPlayerProxy(
    publish_callback=my_callback,
    consumer_name='my-consumer',
    devtools_url='http://localhost:5556',
    port_range=(20000, 30000)
)
```

### 2. Endpoints Personnalisables

Vous pouvez maintenant personnaliser tous les endpoints :

```python
# Player avec endpoints personnalisés
player = DevToolsPlayerProxy(
    publish_callback=my_callback,
    consumer_name='my-consumer',
    devtools_url='http://localhost:5556',
    player_endpoint='/custom/replay',
    register_endpoint='/custom/player/register',
    unregister_endpoint='/custom/player/unregister'
)

# Recorder avec endpoints personnalisés
recorder = DevToolsRecorderProxy(
    devtools_url='http://localhost:5556',
    start_endpoint='/custom/record/start',
    event_endpoint='/custom/record/event',
    stop_endpoint='/custom/record/stop'
)
```

### 3. Configuration du Timeout

Le recorder permet maintenant de configurer le timeout :

```python
recorder = DevToolsRecorderProxy(
    devtools_url='http://localhost:5556',
    timeout=10  # 10 secondes au lieu de 5 (défaut)
)
```

### 4. Utilitaires de Port

La librairie expose des utilitaires pour gérer les ports :

```python
from python_pubsub_devtools_consumers import find_free_port
from python_pubsub_devtools_consumers.port_utils import is_port_available

# Trouver un port libre
port = find_free_port(start_port=8000, end_port=9000)

# Vérifier si un port est disponible
if is_port_available(8080):
    print("Port 8080 est disponible")
```

### 5. Propriétés d'État

Les proxies exposent maintenant des propriétés pour vérifier leur état :

```python
# Player
if player.is_registered:
    print("Player est enregistré auprès de DevTools")

# Recorder
if recorder.is_recording:
    print("Une session d'enregistrement est active")
```

## Exemple Complet de Migration

### Avant (Python.PubSub.Client/base_bus.py)

```python
if enable_recording:
    try:
        from .devtools_recorder_proxy import DevToolsRecorderProxy

        self._devtools_recorder = DevToolsRecorderProxy(
            devtools_host='localhost',
            devtools_port=devtools_recording_port
        )
        self._devtools_recorder.start_session(recording_session_name)
    except Exception as e:
        logger.warning(f"Failed to start DevTools recording: {e}")

if enable_replay:
    try:
        from .devtools_player_proxy import DevToolsPlayerProxy

        self._devtools_player = DevToolsPlayerProxy(
            publish_callback=lambda event_name, payload, producer: self.publish(event_name, payload, producer),
            consumer_name=consumer_name,
            devtools_host='localhost',
            devtools_port=devtools_recording_port
        )
        self._devtools_player.start()
    except Exception as e:
        logger.warning(f"Failed to start DevTools player: {e}")
```

### Après

```python
if enable_recording:
    try:
        from python_pubsub_devtools_consumers import DevToolsRecorderProxy

        self._devtools_recorder = DevToolsRecorderProxy(
            devtools_url=f'http://localhost:{devtools_recording_port}'
        )
        self._devtools_recorder.start_session(recording_session_name)
    except Exception as e:
        logger.warning(f"Failed to start DevTools recording: {e}")

if enable_replay:
    try:
        from python_pubsub_devtools_consumers import DevToolsPlayerProxy

        self._devtools_player = DevToolsPlayerProxy(
            publish_callback=lambda event_name, payload, producer: self.publish(event_name, payload, producer),
            consumer_name=consumer_name,
            devtools_url=f'http://localhost:{devtools_recording_port}'
        )
        self._devtools_player.start()
    except Exception as e:
        logger.warning(f"Failed to start DevTools player: {e}")
```

## Installation

Pour utiliser la nouvelle librairie, ajoutez-la aux dépendances de votre projet :

**pyproject.toml :**

```toml
dependencies = [
    "python-pubsub-devtools-consumers>=0.1.0",
    # ... autres dépendances
]
```

**Installation en mode développement :**

```bash
pip install -e /path/to/Python.PubSub.DevTools.Consumers
```

## Avantages de la Migration

1. **Réutilisabilité** : La librairie peut être utilisée dans n'importe quel projet
2. **Configuration Flexible** : Tous les paramètres sont maintenant configurables
3. **Meilleure Maintenabilité** : Code centralisé et testé
4. **Extensibilité** : Facile d'ajouter de nouvelles fonctionnalités
5. **Type Safety** : Support complet des type hints
6. **Documentation** : README complet et exemples fournis

## Support

Pour toute question ou problème, consultez :

- [README.md](README.md) pour la documentation complète
- [examples/simple_usage.py](examples/simple_usage.py) pour des exemples d'utilisation
