"""
MongoDB connection helpers (pymongo client + collection accessors).
"""

from __future__ import annotations

import logging
import os

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "expense_tracker"
EXPENSES_COLLECTION = "expenses"

_client: MongoClient | None = None


def get_client() -> MongoClient | None:
    """Lazy singleton client with ping; returns None if MongoDB is unreachable."""
    global _client
    if _client is not None:
        return _client
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        _client = client
        logger.info("Connected to MongoDB at %s", MONGO_URI)
        return _client
    except PyMongoError as exc:
        logger.error("MongoDB connection failed: %s", exc)
        return None


def get_expenses_collection() -> Collection | None:
    """Collection used for expense documents."""
    client = get_client()
    if client is None:
        return None
    return client[DB_NAME][EXPENSES_COLLECTION]


def reset_client() -> None:
    """Clear cached client (e.g. tests). Next call reconnects."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None


def log_connection_status() -> None:
    """Log once whether MongoDB can be reached (call from create_app)."""
    if get_expenses_collection() is None:
        logger.warning(
            "MongoDB not reachable at %s — start mongod or set MONGO_URI for Atlas.",
            MONGO_URI,
        )
    else:
        logger.info(
            "MongoDB OK (%s, db=%s, coll=%s)",
            MONGO_URI,
            DB_NAME,
            EXPENSES_COLLECTION,
        )
