"""Application package initialization."""

from __future__ import annotations

import os

from .db import set_backend
from .db_memory import MemoryBackend
from .db_sqlite import SQLiteBackend


def _choose_backend_from_env() -> object:
    """Select and initialize the DB backend based on environment variables."""

    db_mode = os.getenv("DB_MODE", "memory").lower()
    if db_mode == "external":
        db_url = os.getenv("DB_URL")
        if not db_url:
            raise ValueError("DB_URL must be set when DB_MODE=external")
        backend = SQLiteBackend(db_url)
    elif db_mode == "sqlite":
        backend = SQLiteBackend(None)
    elif db_mode == "memory":
        backend = MemoryBackend()
    else:
        raise ValueError(f"Unsupported DB_MODE '{db_mode}'")

    if hasattr(backend, "initialize_database_from_json"):
        backend.initialize_database_from_json()

    return backend


set_backend(_choose_backend_from_env())

