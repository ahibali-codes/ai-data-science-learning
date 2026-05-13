"""
Expense HTTP routes — request parsing, responses, templates only.
"""

from __future__ import annotations

from flask import Flask, flash, redirect, render_template, request, url_for

from models import expense as expense_model
from utils.helpers import (
    all_categories_sorted,
    category_totals_for,
    displayed_expenses,
    validate_expense_form,
)


def register_expenses_routes(app: Flask) -> None:
    """Register expense URLs on the app (endpoints match existing templates)."""

    @app.route("/")
    def home():
        all_expenses = expense_model.load_expenses()
        filter_category = (request.args.get("category") or "").strip()
        categories = all_categories_sorted(all_expenses)
        shown = displayed_expenses(all_expenses, filter_category)
        total = sum(float(row.get("amount", 0) or 0) for row in shown)
        totals_by_cat = category_totals_for(shown)

        return render_template(
            "index.html",
            expenses=shown,
            saved_count=len(all_expenses),
            total=total,
            category_totals=totals_by_cat,
            all_categories=categories,
            filter_category=filter_category,
        )

    @app.route("/add")
    def add_expense_page():
        return render_template("add.html")

    @app.route("/save", methods=["POST"])
    def save_expense():
        ok, payload, errors = validate_expense_form(
            request.form.get("name"),
            request.form.get("amount"),
            request.form.get("category"),
        )
        if not ok or payload is None:
            for message in errors:
                flash(message, "danger")
            return redirect(url_for("add_expense_page"))

        if not expense_model.insert_expense(
            payload["name"],
            payload["amount"],
            payload["category"],
        ):
            flash(
                "Could not save expense. Start MongoDB locally or set the "
                "MONGO_URI environment variable (Atlas connection string).",
                "danger",
            )
            return redirect(url_for("add_expense_page"))

        return redirect(url_for("home"))

    @app.route("/delete", methods=["POST"])
    def delete_expense():
        category_filter = (request.form.get("category_filter") or "").strip()

        def redirect_home():
            expenses = expense_model.load_expenses()
            if category_filter and category_filter in {
                (row.get("category") or "").strip()
                for row in expenses
                if isinstance(row, dict)
            }:
                return redirect(url_for("home", category=category_filter))
            return redirect(url_for("home"))

        expense_id = (request.form.get("id") or "").strip()
        index_raw = (request.form.get("index") or "").strip()

        if expense_id:
            if not expense_model.delete_expense_by_id(expense_id):
                flash(
                    "Could not delete expense. Check the id or database connection.",
                    "danger",
                )
            return redirect_home()

        if index_raw:
            try:
                idx = int(index_raw) - 1
            except ValueError:
                return redirect_home()
            if not expense_model.delete_expense_by_index(idx):
                flash("Could not delete expense. Is MongoDB running?", "danger")
            return redirect_home()

        return redirect_home()
