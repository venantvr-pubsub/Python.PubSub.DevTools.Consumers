"""
Utilitaires pour la gestion des ports réseau.
"""
from __future__ import annotations

import socket


def find_free_port(start_port: int = 10001, end_port: int = 65535, host: str = '') -> int:
    """
    Trouve un port libre dans la plage spécifiée.

    Args:
        start_port: Port de départ (défaut: 10001)
        end_port: Port de fin (défaut: 65535)
        host: Hôte sur lequel bind (défaut: '' pour toutes les interfaces)

    Returns:
        Numéro de port libre

    Raises:
        RuntimeError: Si aucun port libre n'est trouvé
    """
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((host, port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port found between {start_port} and {end_port}")


def is_port_available(port: int, host: str = '') -> bool:
    """
    Vérifie si un port est disponible.

    Args:
        port: Numéro de port à vérifier
        host: Hôte sur lequel vérifier (défaut: '' pour toutes les interfaces)

    Returns:
        True si le port est disponible, False sinon
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, port))
            return True
    except OSError:
        return False
