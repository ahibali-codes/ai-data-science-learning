"""
Expense Tracker — Flask application entry point.
"""

from __future__ import annotations

import logging
import os
import sys

from flask import Flask

from routes import register_routes
from utils.db import log_connection_status


def create_app() -> Flask:
    """Application factory."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

    register_routes(app)
    log_connection_status()
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
