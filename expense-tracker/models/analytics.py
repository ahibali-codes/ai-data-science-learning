"""
Analytics queries over expenses (MongoDB aggregations only).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pymongo.errors import PyMongoError

from utils.db import get_expenses_collection

logger = logging.getLogger(__name__)


def _iso(dt: Any) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    """Move month by delta (negative = earlier)."""
    m = month + delta
    y = year
    while m <= 0:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return y, m


def _month_start_utc(year: int, month: int) -> datetime:
    return datetime(year, month, 1, tzinfo=timezone.utc)


def _month_window(year: int, month: int) -> tuple[datetime, datetime]:
    """[start, next_start) for the calendar month."""
    start = _month_start_utc(year, month)
    ny, nm = _shift_month(year, month, 1)
    end = _month_start_utc(ny, nm)
    return start, end


def get_summary() -> dict[str, Any] | None:
    """
    total_expenses, monthly_spending (current UTC month),
    average_expense (mean amount over all expenses).
    """
    col = get_expenses_collection()
    if col is None:
        return None
    try:
        now = datetime.now(timezone.utc)
        ms, me = _month_window(now.year, now.month)

        agg = list(
            col.aggregate(
                [
                    {
                        "$group": {
                            "_id": None,
                            "total": {"$sum": "$amount"},
                            "count": {"$sum": 1},
                        }
                    }
                ]
            )
        )
        row = agg[0] if agg else {"total": 0, "count": 0}
        total = float(row.get("total") or 0)
        count = int(row.get("count") or 0)

        month_agg = list(
            col.aggregate(
                [
                    {"$match": {"date": {"$gte": ms, "$lt": me}}},
                    {
                        "$group": {
                            "_id": None,
                            "monthly": {"$sum": "$amount"},
                        }
                    },
                ]
            )
        )
        monthly = float(month_agg[0]["monthly"]) if month_agg else 0.0

        avg = (total / count) if count else 0.0

        return {
            "total_expenses": round(total, 2),
            "monthly_spending": round(monthly, 2),
            "average_expense": round(avg, 2),
        }
    except PyMongoError as exc:
        logger.error("analytics summary failed: %s", exc)
        return None


def get_category_breakdown() -> dict[str, Any] | None:
    """Per-category totals and share of grand total (percent)."""
    col = get_expenses_collection()
    if col is None:
        return None
    try:
        rows = list(
            col.aggregate(
                [
                    {
                        "$group": {
                            "_id": {"$ifNull": ["$category", ""]},
                            "total": {"$sum": "$amount"},
                        }
                    },
                    {"$sort": {"total": -1}},
                ]
            )
        )
        grand = sum(float(r.get("total") or 0) for r in rows)
        breakdown = []
        for r in rows:
            cat = (r["_id"] or "").strip() or "Uncategorized"
            t = float(r.get("total") or 0)
            pct = (t / grand * 100.0) if grand > 0 else 0.0
            breakdown.append(
                {
                    "category": cat,
                    "total": round(t, 2),
                    "percentage": round(pct, 2),
                }
            )
        return {
            "grand_total": round(grand, 2),
            "categories": breakdown,
        }
    except PyMongoError as exc:
        logger.error("analytics category breakdown failed: %s", exc)
        return None


def get_monthly_trend(months: int = 6) -> dict[str, Any] | None:
    """Spending per calendar month for the last `months` months (UTC), oldest first."""
    col = get_expenses_collection()
    if col is None:
        return None
    try:
        now = datetime.now(timezone.utc)
        y, m = _shift_month(now.year, now.month, -(months - 1))
        trend = []
        cy, cm = y, m
        for _ in range(months):
            start, next_start = _month_window(cy, cm)
            label = f"{cy}-{cm:02d}"
            sub = list(
                col.aggregate(
                    [
                        {"$match": {"date": {"$gte": start, "$lt": next_start}}},
                        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
                    ]
                )
            )
            total = float(sub[0]["total"]) if sub else 0.0
            trend.append({"month": label, "total": round(total, 2)})
            cy, cm = _shift_month(cy, cm, 1)
        return {"months": trend}
    except PyMongoError as exc:
        logger.error("analytics monthly trend failed: %s", exc)
        return None


def get_top_expenses(limit: int = 5) -> dict[str, Any] | None:
    """Highest expenses by amount."""
    col = get_expenses_collection()
    if col is None:
        return None
    try:
        cursor = col.find().sort([("amount", -1), ("date", -1)]).limit(limit)
        items = []
        for doc in cursor:
            items.append(
                {
                    "id": str(doc["_id"]),
                    "name": doc.get("name") or "",
                    "amount": round(float(doc.get("amount") or 0), 2),
                    "category": doc.get("category") or "",
                    "date": _iso(doc.get("date")),
                }
            )
        return {"expenses": items}
    except PyMongoError as exc:
        logger.error("analytics top expenses failed: %s", exc)
        return None
