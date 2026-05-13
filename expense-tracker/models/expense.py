"""
Expense persistence: MongoDB CRUD only (no HTTP layer).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError

from utils.db import get_expenses_collection

logger = logging.getLogger(__name__)


def _doc_to_row(doc: dict[str, Any]) -> dict[str, Any]:
    """Plain dict for templates (id is string for forms)."""
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name") or "",
        "amount": float(doc.get("amount") or 0),
        "category": doc.get("category") or "",
        "date": doc.get("date"),
    }


def load_expenses() -> list[dict[str, Any]]:
    """Fetch all expenses, oldest first."""
    col = get_expenses_collection()
    if col is None:
        return []
    try:
        cursor = col.find().sort([("date", 1), ("_id", 1)])
        return [_doc_to_row(doc) for doc in cursor]
    except PyMongoError as exc:
        logger.error("Failed to load expenses: %s", exc)
        return []


def insert_expense(name: str, amount: float, category: str) -> bool:
    """Insert one expense with current UTC datetime."""
    col = get_expenses_collection()
    if col is None:
        return False
    doc = {
        "name": name,
        "amount": float(amount),
        "category": category,
        "date": datetime.now(timezone.utc),
    }
    try:
        col.insert_one(doc)
        return True
    except PyMongoError as exc:
        logger.error("Failed to insert expense: %s", exc)
        return False


def delete_expense_by_id(id_str: str) -> bool:
    """Delete by MongoDB ObjectId string."""
    try:
        oid = ObjectId(id_str)
    except InvalidId:
        logger.warning("Invalid expense id for delete: %s", id_str)
        return False
    col = get_expenses_collection()
    if col is None:
        return False
    try:
        result = col.delete_one({"_id": oid})
        return result.deleted_count == 1
    except PyMongoError as exc:
        logger.error("Failed to delete expense: %s", exc)
        return False


def delete_expense_by_index(zero_based: int) -> bool:
    """Delete by list position (same order as load_expenses)."""
    col = get_expenses_collection()
    if col is None:
        return False
    try:
        cursor = col.find().sort([("date", 1), ("_id", 1)])
        docs = list(cursor)
        if not (0 <= zero_based < len(docs)):
            return False
        oid = docs[zero_based]["_id"]
        result = col.delete_one({"_id": oid})
        return result.deleted_count == 1
    except PyMongoError as exc:
        logger.error("Failed to delete expense by index: %s", exc)
        return False
