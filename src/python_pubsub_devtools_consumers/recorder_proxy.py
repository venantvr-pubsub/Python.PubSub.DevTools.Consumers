"""
Proxy HTTP générique pour enregistrer les événements vers DevTools.

Envoie automatiquement tous les événements publiés vers DevTools
pour enregistrement en temps réel.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class DevToolsRecorderProxy:
    """
    Proxy qui envoie les événements à DevTools pour enregistrement.

    Utilisé pour capturer automatiquement tous les événements publiés
    et les enregistrer dans DevTools via HTTP.

    Args:
        devtools_url: URL complète de DevTools (ex: http://localhost:5556)
        start_endpoint: Endpoint pour démarrer l'enregistrement (défaut: /api/record/start)
        event_endpoint: Endpoint pour enregistrer un événement (défaut: /api/record/event)
        stop_endpoint: Endpoint pour arrêter l'enregistrement (défaut: /api/record/stop)
        timeout: Timeout des requêtes HTTP en secondes (défaut: 5)
    """

    def __init__(
            self,
            devtools_url: str = 'http://localhost:5556',
            start_endpoint: str = '/api/record/start',
            event_endpoint: str = '/api/record/event',
            stop_endpoint: str = '/api/record/stop',
            timeout: int = 5,
    ):
        self.devtools_url = devtools_url.rstrip('/')
        self.start_endpoint = start_endpoint
        self.event_endpoint = event_endpoint
        self.stop_endpoint = stop_endpoint
        self.timeout = timeout
        self._session_started = False

    def start_session(self, session_name: Optional[str] = None) -> bool:
        """
        Démarre une session d'enregistrement dans DevTools.

        Args:
            session_name: Nom de la session (optionnel)

        Returns:
            True si succès, False sinon
        """
        try:
            payload = {}
            if session_name:
                payload['session_name'] = session_name

            response = requests.post(
                f'{self.devtools_url}{self.start_endpoint}',
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            self._session_started = True
            logger.info(f"DevTools recording session started: {session_name or 'auto'}")
            return True
        except requests.RequestException as e:
            logger.warning(f"Failed to start DevTools recording session: {e}")
            return False

    def record_event(self, event_name: str, event_data: Any, source: str) -> None:
        """
        Enregistre un événement dans DevTools.

        Args:
            event_name: Nom de l'événement
            event_data: Données de l'événement
            source: Source de l'événement
        """
        if not self._session_started:
            logger.debug("DevTools recording session not started, skipping event")
            return

        try:
            response = requests.post(
                f'{self.devtools_url}{self.event_endpoint}',
                json={
                    'event_name': event_name,
                    'event_data': event_data,
                    'source': source
                },
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.debug(f"Failed to record event to DevTools: {e}")

    def stop_session(self) -> bool:
        """
        Arrête la session d'enregistrement et sauvegarde.

        Returns:
            True si succès, False sinon
        """
        if not self._session_started:
            return False

        try:
            response = requests.post(
                f'{self.devtools_url}{self.stop_endpoint}',
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            self._session_started = False
            logger.info(
                f"DevTools recording saved: {result.get('filename')} "
                f"({result.get('event_count')} events)"
            )
            return True
        except requests.RequestException as e:
            logger.warning(f"Failed to stop DevTools recording session: {e}")
            return False

    @property
    def is_recording(self) -> bool:
        """Retourne True si une session d'enregistrement est active."""
        return self._session_started

    def __repr__(self) -> str:
        return f"DevToolsRecorderProxy({self.devtools_url})"
