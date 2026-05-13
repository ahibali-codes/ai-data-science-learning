"""Flask route registration."""

from __future__ import annotations

from flask import Flask

from routes.analytics import register_analytics_routes
from routes.auth import register_auth_routes
from routes.expenses import register_expenses_routes


def register_routes(app: Flask) -> None:
    register_expenses_routes(app)
    register_analytics_routes(app)
    register_auth_routes(app)
