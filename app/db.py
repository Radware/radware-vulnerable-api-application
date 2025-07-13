from __future__ import annotations

import os
from typing import Any

from .db_base import DatabaseBackend
from .db_memory import MemoryBackend
from .db_sqlite import SQLiteBackend

# Map supported backend modes to their implementations
_BACKENDS = {
    "memory": MemoryBackend,
    "sqlite": SQLiteBackend,
}

# Determine backend based on DB_MODE
_db_mode = os.getenv("DB_MODE", "memory").lower()
if _db_mode == "external":
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise ValueError("DB_URL must be set when DB_MODE=external")
    _backend = SQLiteBackend(db_url)
else:
    _backend_cls = _BACKENDS.get(_db_mode)
    if _backend_cls is None:
        raise ValueError(f"Unsupported DB_MODE '{_db_mode}'")
    _backend = _backend_cls()
# initialize using default prepopulated data if available
if hasattr(_backend, "initialize_database_from_json"):
    _backend.initialize_database_from_json()


def __getattr__(name: str) -> Any:  # pragma: no cover - thin delegation
    return getattr(_backend, name)


def initialize_database_from_json() -> None:
    """Reinitialize the current backend from prepopulated JSON."""
    if hasattr(_backend, "initialize_database_from_json"):
        _backend.initialize_database_from_json()
