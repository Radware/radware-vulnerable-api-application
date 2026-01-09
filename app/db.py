from __future__ import annotations

from typing import Any

from .db_base import DatabaseBackend
from .db_memory import MemoryBackend

_backend: DatabaseBackend = MemoryBackend()


def set_backend(backend: DatabaseBackend) -> None:
    """Set the global backend implementation."""

    global _backend
    _backend = backend


def __getattr__(name: str) -> Any:  # pragma: no cover - thin delegation
    return getattr(_backend, name)


def initialize_database_from_json() -> None:
    """Reinitialize the current backend from prepopulated JSON."""
    if hasattr(_backend, "initialize_database_from_json"):
        _backend.initialize_database_from_json()
