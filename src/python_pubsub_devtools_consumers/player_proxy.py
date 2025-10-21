"""
Proxy HTTP générique pour rejouer les événements depuis DevTools.

Démarre un serveur HTTP sur un port configurable et s'enregistre auprès
de DevTools pour recevoir les événements rejoués.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Optional

import requests
from flask import Flask, request, jsonify

from .port_utils import find_free_port

logger = logging.getLogger(__name__)


class DevToolsPlayerProxy:
    """
    Proxy qui reçoit les événements rejoués de DevTools.

    Démarre un serveur HTTP local, s'enregistre auprès de DevTools,
    et invoque une callback pour chaque événement reçu.

    Args:
        publish_callback: Fonction appelée pour publier les événements (signature: event_name, payload, producer)
        consumer_name: Nom du consumer pour l'enregistrement
        devtools_url: URL complète de DevTools (ex: http://localhost:5556)
        player_port: Port du serveur player (None pour auto)
        player_host: Hôte du serveur player (défaut: localhost)
        player_endpoint: Endpoint pour recevoir les replays (défaut: /replay)
        register_endpoint: Endpoint d'enregistrement DevTools (défaut: /api/player/register)
        unregister_endpoint: Endpoint de désenregistrement DevTools (défaut: /api/player/unregister)
        port_range: Tuple (start, end) pour la recherche de port libre (défaut: 10001, 65535)
        auto_find_port: Si True, trouve automatiquement un port libre (défaut: True)
    """

    def __init__(
            self,
            publish_callback: Callable[[str, Any, str], None],
            consumer_name: str,
            devtools_url: str = 'http://localhost:5556',
            player_port: Optional[int] = None,
            player_host: str = 'localhost',
            player_endpoint: str = '/replay',
            register_endpoint: str = '/api/player/register',
            unregister_endpoint: str = '/api/player/unregister',
            port_range: tuple[int, int] = (10001, 65535),
            auto_find_port: bool = True,
    ):
        self.publish_callback = publish_callback
        self.consumer_name = consumer_name
        self.devtools_url = devtools_url.rstrip('/')
        self.player_host = player_host
        self.player_endpoint = player_endpoint
        self.register_endpoint = register_endpoint
        self.unregister_endpoint = unregister_endpoint

        # Déterminer le port
        if player_port is None and auto_find_port:
            self.player_port = find_free_port(port_range[0], port_range[1])
        elif player_port is None:
            raise ValueError("player_port must be specified when auto_find_port is False")
        else:
            self.player_port = player_port

        self.player_url = f'http://{player_host}:{self.player_port}'

        # Créer l'application Flask
        self._app = Flask(__name__)
        self._app.add_url_rule(
            self.player_endpoint,
            'replay',
            self._handle_replay,
            methods=['POST']
        )

        # Thread du serveur
        self._server_thread: Optional[threading.Thread] = None
        self._registered = False

    def _handle_replay(self):
        """
        Endpoint qui reçoit les événements rejoués de DevTools.

        Payload attendu:
        {
            "event_name": str,
            "event_data": dict,
            "source": str
        }
        """
        try:
            data = request.get_json()
            event_name = data.get('event_name')
            event_data = data.get('event_data')
            source = data.get('source', 'DevToolsReplay')

            if not event_name or event_data is None:
                return jsonify({'error': 'Missing event_name or event_data'}), 400

            # Publier l'événement via la callback
            self.publish_callback(event_name, event_data, source)

            logger.debug(f"Replayed event: {event_name} from {source}")
            return jsonify({'status': 'replayed', 'event_name': event_name}), 200

        except Exception as e:
            logger.error(f"Error handling replay: {e}")
            return jsonify({'error': str(e)}), 500

    def start(self, flask_host: str = '0.0.0.0', flask_debug: bool = False) -> bool:
        """
        Démarre le serveur player et s'enregistre auprès de DevTools.

        Args:
            flask_host: Hôte Flask (défaut: 0.0.0.0)
            flask_debug: Mode debug Flask (défaut: False)

        Returns:
            True si succès, False sinon
        """
        # Démarrer le serveur Flask dans un thread
        self._server_thread = threading.Thread(
            target=lambda: self._app.run(
                host=flask_host,
                port=self.player_port,
                debug=flask_debug,
                use_reloader=False,
                threaded=True
            ),
            daemon=True,
            name=f"DevToolsPlayer-{self.player_port}"
        )
        self._server_thread.start()

        logger.info(f"DevTools player started on {self.player_url}")

        # S'enregistrer auprès de DevTools
        return self._register_with_devtools()

    def _register_with_devtools(self) -> bool:
        """
        Enregistre ce player auprès de DevTools.

        Returns:
            True si succès, False sinon
        """
        try:
            payload = {
                'player_endpoint': f'{self.player_url}{self.player_endpoint}',
                'consumer_name': self.consumer_name
            }

            response = requests.post(
                f'{self.devtools_url}{self.register_endpoint}',
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            self._registered = True
            logger.info(f"Registered with DevTools at {self.devtools_url}")
            return True

        except requests.RequestException as e:
            logger.warning(f"Failed to register with DevTools player: {e}")
            return False

    def unregister(self) -> bool:
        """
        Désenregistre ce player de DevTools.

        Returns:
            True si succès, False sinon
        """
        if not self._registered:
            return False

        try:
            payload = {
                'player_endpoint': f'{self.player_url}{self.player_endpoint}'
            }

            response = requests.post(
                f'{self.devtools_url}{self.unregister_endpoint}',
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            self._registered = False
            logger.info(f"Unregistered from DevTools")
            return True

        except requests.RequestException as e:
            logger.warning(f"Failed to unregister from DevTools player: {e}")
            return False

    @property
    def is_registered(self) -> bool:
        """Retourne True si le player est enregistré auprès de DevTools."""
        return self._registered

    def __repr__(self) -> str:
        return f"DevToolsPlayerProxy({self.player_url} -> {self.devtools_url})"
