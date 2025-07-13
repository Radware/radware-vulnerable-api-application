from __future__ import annotations

import os
from typing import Any

from .db_base import DatabaseBackend
from .db_memory import MemoryBackend

# Map supported backend modes to their implementations
_BACKENDS = {
    "memory": MemoryBackend,
}

_db_mode = os.getenv("DB_MODE", "memory").lower()
_backend_cls = _BACKENDS.get(_db_mode)
if _backend_cls is None:
    raise ValueError(f"Unsupported DB_MODE '{_db_mode}'")

_backend: DatabaseBackend = _backend_cls()
# initialize using default prepopulated data if available
if hasattr(_backend, "initialize_database_from_json"):
    _backend.initialize_database_from_json()


def __getattr__(name: str) -> Any:  # pragma: no cover - thin delegation
    return getattr(_backend, name)


def initialize_database_from_json() -> None:
    """Reinitialize the current backend from prepopulated JSON."""
    if hasattr(_backend, "initialize_database_from_json"):
        _backend.initialize_database_from_json()
