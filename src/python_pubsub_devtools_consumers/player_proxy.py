"""
Proxy HTTP générique pour rejouer les événements depuis DevTools.

Démarre un serveur HTTP sur un port configurable et s'enregistre auprès
de DevTools pour recevoir les événements rejoués.
"""
from __future__ import annotations

import logging
import queue
import random
import string
import threading
from typing import Callable, Optional

import requests
from flask import Flask, request, jsonify

from .port_utils import find_free_port

logger = logging.getLogger(__name__)


def _generate_random_endpoint() -> str:
    """
    Génère un endpoint aléatoire avec 8 caractères minuscules.

    Returns:
        Endpoint sous forme /abcdefgh
    """
    random_chars = ''.join(random.choices(string.ascii_lowercase, k=8))
    return f'/{random_chars}'


class DevToolsPlayerProxy:
    """
    Proxy qui reçoit les événements depuis DevTools via HTTP.

    Encapsule toute la logique Flask/HTTP/JSON. Le consommateur fournit
    simplement un handler qui traite les événements déjà parsés.

    L'endpoint HTTP est généré automatiquement de façon aléatoire pour
    une abstraction totale de Flask.

    Args:
        consumer_name: Nom du consumer pour l'enregistrement
        event_handler: Fonction appelée avec l'événement parsé
                      Signature: (event_name, event_data, source) -> bool
                      Retourne True si succès, False si erreur
        devtools_url: URL complète de DevTools (ex: http://localhost:5556)
        player_port: Port du serveur player (None pour auto)
        player_host: Hôte du serveur player (défaut: localhost)
        register_endpoint: Endpoint d'enregistrement DevTools (défaut: /api/player/register)
        unregister_endpoint: Endpoint de désenregistrement DevTools (défaut: /api/player/unregister)
        port_range: Tuple (start, end) pour la recherche de port libre (défaut: 10001, 65535)
        auto_find_port: Si True, trouve automatiquement un port libre (défaut: True)
        sequential_processing: Si True, traite les événements séquentiellement via une queue
                              pour éviter les race conditions (défaut: False)

    Example:
        >>> def handle_event(event_name, event_data, source):
        ...     print(f"Received: {event_name}")
        ...     process_event(event_data)
        ...     return True  # Success
        ...
        >>> player = DevToolsPlayerProxy(
        ...     consumer_name="my-consumer",
        ...     event_handler=handle_event
        ... )
        >>> player.start()
    """

    def __init__(
            self,
            consumer_name: str,
            event_handler: Callable[[str, dict, str], bool],
            devtools_url: str = 'http://localhost:5556',
            player_port: Optional[int] = None,
            player_host: str = 'localhost',
            register_endpoint: str = '/api/player/register',
            unregister_endpoint: str = '/api/player/unregister',
            port_range: tuple[int, int] = (10001, 65535),
            auto_find_port: bool = True,
            sequential_processing: bool = False,
    ):
        self.consumer_name = consumer_name
        self.event_handler = event_handler
        self.devtools_url = devtools_url.rstrip('/')
        self.player_host = player_host
        self.register_endpoint = register_endpoint
        self.unregister_endpoint = unregister_endpoint

        # Générer un endpoint aléatoire (abstraction totale)
        self._player_endpoint = _generate_random_endpoint()

        # Déterminer le port
        if player_port is None and auto_find_port:
            self.player_port = find_free_port(port_range[0], port_range[1])
        elif player_port is None:
            raise ValueError("player_port must be specified when auto_find_port is False")
        else:
            self.player_port = player_port

        self.player_url = f'http://{player_host}:{self.player_port}'

        # Créer l'application Flask (tout est encapsulé ici)
        self._app = Flask(__name__)
        self._app.add_url_rule(
            self._player_endpoint,
            'handle_event',
            self._flask_handler,
            methods=['POST']
        )

        # Thread du serveur
        self._server_thread: Optional[threading.Thread] = None
        self._registered = False

        # Mode de traitement séquentiel
        self.sequential_processing = sequential_processing
        self._event_queue: Optional[queue.Queue] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_worker = False

        if self.sequential_processing:
            self._event_queue = queue.Queue()

    def _flask_handler(self):
        """
        Handler Flask interne - encapsule toute la logique HTTP/JSON.
        Le consommateur n'a pas besoin de connaître Flask.
        """
        try:
            # Parser la requête JSON
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400

            # Extraire les champs (logique DevTools encapsulée ici)
            event_name = data.get('event_name')
            event_data = data.get('event_data')
            source = data.get('source', 'DevTools')

            # Validation
            if not event_name:
                return jsonify({'error': 'Missing event_name'}), 400
            if event_data is None:
                return jsonify({'error': 'Missing event_data'}), 400

            # Mode de traitement selon la configuration
            if self.sequential_processing:
                # Mode queue : mettre l'événement en queue pour traitement séquentiel
                self._event_queue.put((event_name, event_data, source))
                logger.debug(f"Event queued: {event_name} from {source}")
                return jsonify({
                    'status': 'queued',
                    'event_name': event_name,
                    'queue_size': self._event_queue.qsize()
                }), 202  # 202 Accepted

            else:
                # Mode direct : traiter immédiatement (comportement original)
                success = self.event_handler(event_name, event_data, source)

                # Retourner la réponse HTTP appropriée
                if success:
                    logger.debug(f"Event processed: {event_name} from {source}")
                    return jsonify({
                        'status': 'success',
                        'event_name': event_name
                    }), 200
                else:
                    logger.warning(f"Event processing failed: {event_name}")
                    return jsonify({
                        'status': 'error',
                        'event_name': event_name,
                        'error': 'Handler returned False'
                    }), 500

        except Exception as e:
            logger.error(f"Error in Flask handler: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500

    def _worker_loop(self):
        """
        Boucle worker - traite les événements séquentiellement depuis la queue.
        Cette méthode s'exécute dans un thread séparé et garantit qu'un seul
        événement est traité à la fois, éliminant ainsi les race conditions.
        """
        logger.info("Event worker thread started")

        while not self._stop_worker:
            try:
                # Attendre un événement avec timeout pour pouvoir vérifier _stop_worker
                try:
                    event_name, event_data, source = self._event_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Signal d'arrêt
                if event_name is None:
                    break

                # Traitement séquentiel garanti
                try:
                    success = self.event_handler(event_name, event_data, source)

                    if success:
                        logger.debug(f"Event processed: {event_name} from {source}")
                    else:
                        logger.warning(f"Event processing failed: {event_name}")

                except Exception as e:
                    logger.error(f"Error processing event {event_name}: {e}", exc_info=True)

                finally:
                    self._event_queue.task_done()

            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

        logger.info("Event worker thread stopped")

    def start(self, flask_host: str = '0.0.0.0', flask_debug: bool = False) -> bool:
        """
        Démarre le serveur player et s'enregistre auprès de DevTools.

        Args:
            flask_host: Hôte Flask (défaut: 0.0.0.0)
            flask_debug: Mode debug Flask (défaut: False)

        Returns:
            True si succès, False sinon
        """
        # Démarrer le worker thread si mode séquentiel
        if self.sequential_processing:
            self._stop_worker = False
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f"EventWorker-{self.player_port}"
            )
            self._worker_thread.start()
            logger.info(f"Sequential processing enabled - worker thread started")

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
                'player_endpoint': f'{self.player_url}{self._player_endpoint}',
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
            logger.warning(f"Failed to register with DevTools: {e}")
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
                'player_endpoint': f'{self.player_url}{self._player_endpoint}'
            }

            response = requests.post(
                f'{self.devtools_url}{self.unregister_endpoint}',
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            self._registered = False
            logger.info("Unregistered from DevTools")
            return True

        except requests.RequestException as e:
            logger.warning(f"Failed to unregister from DevTools: {e}")
            return False

    def stop(self, timeout: float = 5.0) -> bool:
        """
        Arrête proprement le player et le worker thread.

        Cette méthode :
        1. Désenregistre le player de DevTools
        2. Arrête le worker thread (si mode séquentiel)
        3. Attend que tous les événements en queue soient traités

        Args:
            timeout: Temps maximum d'attente (en secondes) pour que la queue se vide

        Returns:
            True si l'arrêt s'est bien passé, False sinon
        """
        logger.info("Stopping player...")

        # Désenregistrer de DevTools
        self.unregister()

        # Arrêter le worker thread si mode séquentiel
        if self.sequential_processing and self._worker_thread and self._worker_thread.is_alive():
            logger.info("Stopping worker thread...")

            # Signaler l'arrêt
            self._stop_worker = True

            # Mettre un signal d'arrêt dans la queue (au cas où elle serait bloquée)
            self._event_queue.put((None, None, None))

            # Attendre que la queue se vide
            try:
                logger.info(f"Waiting for queue to empty (timeout={timeout}s)...")
                self._event_queue.join()
                logger.info("Queue emptied successfully")
            except Exception as e:
                logger.warning(f"Error while waiting for queue to empty: {e}")

            # Attendre que le thread se termine
            self._worker_thread.join(timeout=timeout)

            if self._worker_thread.is_alive():
                logger.warning("Worker thread did not stop gracefully")
                return False
            else:
                logger.info("Worker thread stopped successfully")

        logger.info("Player stopped")
        return True

    @property
    def is_registered(self) -> bool:
        """Retourne True si le player est enregistré auprès de DevTools."""
        return self._registered

    @property
    def player_endpoint(self) -> str:
        """Retourne l'endpoint du player."""
        return self._player_endpoint

    def __repr__(self) -> str:
        return f"DevToolsPlayerProxy({self.player_url} -> {self.devtools_url})"
