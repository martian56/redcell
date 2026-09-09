"""Process-wide live services shared across runs in the worker: the reverse-shell
listener manager (its bound sockets must outlive any single run)."""

from __future__ import annotations

from ..bus import bus
from .listeners import ListenerManager
from .ngrok import NgrokManager

_listeners: ListenerManager | None = None
_ngrok: NgrokManager | None = None


def get_listener_manager() -> ListenerManager:
    global _listeners
    if _listeners is None:
        _listeners = ListenerManager(bus)
    return _listeners


def get_ngrok_manager() -> NgrokManager:
    global _ngrok
    if _ngrok is None:
        _ngrok = NgrokManager()
    return _ngrok
