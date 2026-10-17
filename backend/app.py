import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory


PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_PAGES = {
    "index.html",
    "about.html",
    "contact.html",
    "menu.html",
    "order.html",
    "reservation.html",
    "service.html",
    "testimonial.html",
}
ASSET_DIRECTORIES = {"css", "img", "js", "lib"}
ALLOWED_MAIL_ASSETS = {"mail/contact.js", "mail/jqBootstrapValidation.min.js"}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MENU_PRICES = {
    "Espresso": 99,
    "Americano": 129,
    "Cappuccino": 149,
    "Caffe Latte": 159,
    "Caffe Mocha": 179,
    "Flat White": 169,
    "Macchiato": 139,
    "Filter Coffee": 109,
    "Black Coffee": 109,
    "Hazelnut Coffee": 199,
    "Vanilla Latte": 189,
    "Caramel Latte": 189,
    "Classic Cold Coffee": 129,
    "Iced Americano": 119,
    "Iced Latte": 149,
    "Iced Cappuccino": 159,
    "Chocolate Cold Coffee": 149,
    "Caramel Cold Coffee": 159,
    "Vanilla Cold Coffee": 159,
    "Hazelnut Cold Coffee": 169,
    "Oreo Cold Coffee": 179,
    "Cold Coffee with Ice Cream": 189,
    "Chocolate Frappe": 179,
    "Caramel Frappe": 189,
    "French Fries": 99,
    "Peri Peri Fries": 119,
    "Cheese Fries": 139,
    "Veg Sandwich": 129,
    "Cheese Sandwich": 139,
    "Grilled Veg Sandwich": 149,
    "Paneer Sandwich": 169,
    "Garlic Bread": 119,
    "Cheese Garlic Bread": 139,
}


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "COFFEE_SHOP_DATABASE",
            str(Path(__file__).resolve().parent / "data" / "coffee_shop.sqlite3"),
        ),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    initialize_database(app.config["DATABASE"])

    @app.get("/")
    def home():
        return send_from_directory(PROJECT_ROOT, "index.html")

    @app.get("/<path:filename>")
    def frontend_file(filename):
        normalized = filename.replace("\\", "/")
        first_part = normalized.split("/", 1)[0]
        if normalized in HTML_PAGES or first_part in ASSET_DIRECTORIES or normalized in ALLOWED_MAIL_ASSETS:
            return send_from_directory(PROJECT_ROOT, normalized)
        abort(404)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/menu")
    def menu_catalog():
        return jsonify(items=[{"name": name, "price_rupees": price} for name, price in MENU_PRICES.items()])

    @app.post("/api/contact")
    def create_contact_message():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return json_error("Send the form as JSON.", 400)

        name = clean_text(data.get("name"), 100)
        email = clean_text(data.get("email"), 254).lower()
        subject = clean_text(data.get("subject"), 150)
        message = clean_text(data.get("message"), 5000)
        if not name or not EMAIL_PATTERN.fullmatch(email) or not subject or not message:
            return json_error("Name, a valid email, subject, and message are required.", 400)

        with database_connection(app.config["DATABASE"]) as connection:
            cursor = connection.execute(
                """INSERT INTO contact_messages (name, email, subject, message, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, email, subject, message, current_timestamp()),
            )
            message_id = cursor.lastrowid
        return jsonify(message="Contact message saved.", message_id=message_id), 201

    @app.post("/api/reservations")
    def create_reservation():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return json_error("Send the form as JSON.", 400)

        name = clean_text(data.get("name"), 100)
        email = clean_text(data.get("email"), 254).lower()
        date = clean_text(data.get("date"), 40)
        time = clean_text(data.get("time"), 40)
        guests = data.get("guests")
        if (
            not name
            or not EMAIL_PATTERN.fullmatch(email)
            or not date
            or not time
            or isinstance(guests, bool)
            or not isinstance(guests, int)
            or not 1 <= guests <= 20
        ):
            return json_error("Provide a name, valid email, date, time, and guest count from 1 to 20.", 400)

        with database_connection(app.config["DATABASE"]) as connection:
            cursor = connection.execute(
                """INSERT INTO reservations (name, email, reservation_date, reservation_time, guests, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, email, date, time, guests, current_timestamp()),
            )
            reservation_id = cursor.lastrowid
        return jsonify(message="Reservation request saved.", reservation_id=reservation_id), 201

    @app.post("/api/orders")
    def create_order():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return json_error("Send the order as JSON.", 400)

        name = clean_text(data.get("customer_name"), 100)
        email = clean_text(data.get("email"), 254).lower()
        phone = clean_text(data.get("phone"), 40)
        items = data.get("items")
        instructions = clean_text(data.get("special_instructions", ""), 1000)
        if not name or not EMAIL_PATTERN.fullmatch(email) or not isinstance(items, list) or not items:
            return json_error("Customer name, valid email, and at least one order item are required.", 400)
        if len(items) > 50:
            return json_error("An order may contain no more than 50 line items.", 400)

        normalized_items = []
        total_rupees = 0
        for item in items:
            if not isinstance(item, dict):
                return json_error("Each item must include a name and quantity.", 400)
            item_name = clean_text(item.get("name"), 120)
            quantity = item.get("quantity")
            unit_price = MENU_PRICES.get(item_name)
            if (
                unit_price is None
                or isinstance(quantity, bool)
                or not isinstance(quantity, int)
                or not 1 <= quantity <= 99
            ):
                return json_error("Choose a menu item and provide a quantity from 1 to 99.", 400)
            line_total = unit_price * quantity
            normalized_items.append(
                {
                    "name": item_name,
                    "quantity": quantity,
                    "unit_price_rupees": unit_price,
                    "line_total_rupees": line_total,
                }
            )
            total_rupees += line_total

        with database_connection(app.config["DATABASE"]) as connection:
            cursor = connection.execute(
                """INSERT INTO orders
                   (customer_name, email, phone, items_json, total_rupees, special_instructions, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    name,
                    email,
                    phone,
                    json.dumps(normalized_items),
                    total_rupees,
                    instructions,
                    "received",
                    current_timestamp(),
                ),
            )
            order_id = cursor.lastrowid
        return jsonify(
            message="Order saved.",
            order_id=order_id,
            status="received",
            total_rupees=total_rupees,
        ), 201

    return app


def clean_text(value, max_length):
    if not isinstance(value, str):
        return ""
    cleaned = value.strip()
    return cleaned if cleaned and len(cleaned) <= max_length else ""


def current_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_error(message, status):
    return jsonify(error=message), status


@contextmanager
def database_connection(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path):
    with database_connection(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                reservation_date TEXT NOT NULL,
                reservation_time TEXT NOT NULL,
                guests INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                items_json TEXT NOT NULL,
                total_rupees INTEGER NOT NULL DEFAULT 0,
                special_instructions TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'received',
                created_at TEXT NOT NULL
            );
            """
        )
        order_columns = {row["name"] for row in connection.execute("PRAGMA table_info(orders)")}
        if "total_rupees" not in order_columns:
            connection.execute(
                "ALTER TABLE orders ADD COLUMN total_rupees INTEGER NOT NULL DEFAULT 0"
            )


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)