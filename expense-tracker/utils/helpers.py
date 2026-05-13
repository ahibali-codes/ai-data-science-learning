"""
Shared helpers: validation, aggregates, and row lookups.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable


def get_expense_id(entry) -> str | None:
    """Return string id for a dict expense row (MongoDB ObjectId hex), or None."""
    if not isinstance(entry, dict):
        return None
    raw = entry.get("id")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def category_totals_for(expense_rows: Iterable) -> list[tuple[str, float]]:
    """Return sorted list of (category, total) for the given rows."""
    totals: defaultdict[str, float] = defaultdict(float)
    for entry in expense_rows:
        if not isinstance(entry, dict):
            continue
        cat = (entry.get("category") or "").strip() or "Uncategorized"
        try:
            totals[cat] += float(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            continue
    return sorted(totals.items(), key=lambda x: (-x[1], x[0].lower()))


def all_categories_sorted(all_expenses: list) -> list[str]:
    names = {
        (entry.get("category") or "").strip()
        for entry in all_expenses
        if isinstance(entry, dict) and (entry.get("category") or "").strip()
    }
    return sorted(names, key=str.lower)


def displayed_expenses(all_expenses: list, filter_category: str) -> list:
    """Rows for the home table (dict entries only)."""
    if filter_category:
        return [
            entry
            for entry in all_expenses
            if isinstance(entry, dict)
            and (entry.get("category") or "").strip() == filter_category
        ]
    return [entry for entry in all_expenses if isinstance(entry, dict)]


def validate_expense_form(name: str | None, amount_raw: str | None, category: str | None):
    """
    Validate add-expense form fields.

    Returns:
        (success: bool, payload: dict | None, errors: list[str])
    """
    errors: list[str] = []
    name_clean = (name or "").strip()
    category_clean = (category or "").strip()
    amount_str = (amount_raw if amount_raw is not None else "").strip()

    if not name_clean:
        errors.append("Name is required.")
    if not category_clean:
        errors.append("Category is required.")
    amount_value, amount_err = parse_amount(amount_str)
    if amount_err:
        errors.append(amount_err)

    if errors:
        return False, None, errors

    return True, {"name": name_clean, "amount": amount_value, "category": category_clean}, []


def parse_amount(amount_str: str) -> tuple[float | None, str | None]:
    """Parse a non-negative finite float from user input."""
    if not amount_str.strip():
        return None, "Amount is required."
    try:
        value = float(amount_str.strip())
    except ValueError:
        return None, "Amount must be a number."
    if math.isnan(value) or math.isinf(value):
        return None, "Amount must be a finite number."
    if value < 0:
        return None, "Amount cannot be negative."
    return value, None
