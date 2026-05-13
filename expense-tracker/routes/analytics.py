"""
JSON analytics API routes.
"""

from __future__ import annotations

from flask import Flask, jsonify

from models import analytics as analytics_model


def register_analytics_routes(app: Flask) -> None:
    """Register /analytics/* endpoints."""

    @app.route("/analytics/summary")
    def analytics_summary():
        data = analytics_model.get_summary()
        if data is None:
            return jsonify({"error": "database_unavailable"}), 503
        return jsonify(data)

    @app.route("/analytics/category-breakdown")
    def analytics_category_breakdown():
        data = analytics_model.get_category_breakdown()
        if data is None:
            return jsonify({"error": "database_unavailable"}), 503
        return jsonify(data)

    @app.route("/analytics/monthly-trend")
    def analytics_monthly_trend():
        data = analytics_model.get_monthly_trend(6)
        if data is None:
            return jsonify({"error": "database_unavailable"}), 503
        return jsonify(data)

    @app.route("/analytics/top-expenses")
    def analytics_top_expenses():
        data = analytics_model.get_top_expenses(5)
        if data is None:
            return jsonify({"error": "database_unavailable"}), 503
        return jsonify(data)
