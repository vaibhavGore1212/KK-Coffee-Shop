import os
import tempfile
import unittest

from backend.app import create_app


class BackendApiTests(unittest.TestCase):
    def setUp(self):
        database_file = tempfile.NamedTemporaryFile(delete=False)
        database_file.close()
        self.database_path = database_file.name
        self.app = create_app({"TESTING": True, "DATABASE": self.database_path})
        self.client = self.app.test_client()

    def tearDown(self):
        os.unlink(self.database_path)

    def create_account(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "name": "Asha Customer",
                "email": "asha@example.com",
                "phone": "9876543210",
                "password": "coffee-pass-123",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()["user"]

    def test_contact_message_is_saved(self):
        response = self.client.post(
            "/api/contact",
            json={
                "name": "Asha",
                "email": "asha@example.com",
                "subject": "Coffee question",
                "message": "Do you have decaf?",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["message_id"], 1)

    def test_contact_rejects_invalid_email(self):
        response = self.client.post(
            "/api/contact",
            json={"name": "Asha", "email": "not-an-email", "subject": "Hello", "message": "Hi"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_reservation_is_saved(self):
        user = self.create_account()
        response = self.client.post(
            "/api/reservations",
            json={
                "date": "10/20/2026",
                "time": "7:00 PM",
                "guests": 2,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["reservation_id"], 1)

        import sqlite3

        connection = sqlite3.connect(self.database_path)
        try:
            reservation = connection.execute(
                "SELECT name, email, reservation_date, reservation_time, guests FROM reservations WHERE id = 1"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(reservation, (user["name"], user["email"], "10/20/2026", "7:00 PM", 2))

    def test_reservation_requires_login(self):
        response = self.client.post(
            "/api/reservations",
            json={"date": "10/20/2026", "time": "7:00 PM", "guests": 2},
        )

        self.assertEqual(response.status_code, 401)

    def test_account_registration_login_and_logout(self):
        user = self.create_account()
        self.assertEqual(user["email"], "asha@example.com")
        self.assertTrue(self.client.get("/api/auth/me").get_json()["authenticated"])

        import sqlite3

        connection = sqlite3.connect(self.database_path)
        try:
            password_hash = connection.execute(
                "SELECT password_hash FROM users WHERE email = ?",
                ("asha@example.com",),
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertNotEqual(password_hash, "coffee-pass-123")

        logout_response = self.client.post("/api/auth/logout")
        self.assertEqual(logout_response.status_code, 200)
        self.assertFalse(self.client.get("/api/auth/me").get_json()["authenticated"])

        failed_login = self.client.post(
            "/api/auth/login",
            json={"email": "asha@example.com", "password": "incorrect-password"},
        )
        self.assertEqual(failed_login.status_code, 401)

        login_response = self.client.post(
            "/api/auth/login",
            json={"email": "asha@example.com", "password": "coffee-pass-123"},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(self.client.get("/api/auth/me").get_json()["authenticated"])

    def test_order_is_saved_with_items(self):
        user = self.create_account()
        response = self.client.post(
            "/api/orders",
            json={
                "customer_name": "Spoofed Name",
                "email": "spoof@example.com",
                "phone": "0000000000",
                "delivery_address": "10 Main Street, Pune",
                "items": [{"name": "Espresso", "quantity": 2}, {"name": "French Fries", "quantity": 1}],
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["order_id"], 1)
        self.assertEqual(response.get_json()["total_rupees"], 297)

        import sqlite3

        connection = sqlite3.connect(self.database_path)
        try:
            saved_order = connection.execute(
                "SELECT user_id, customer_name, email, phone, delivery_address, items_json, total_rupees "
                "FROM orders WHERE id = 1"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(saved_order[0], user["id"])
        self.assertEqual(saved_order[1:5], ("Asha Customer", "asha@example.com", "9876543210", "10 Main Street, Pune"))
        self.assertEqual(saved_order[6], 297)
        self.assertIn('"unit_price_rupees": 99', saved_order[5])
        self.assertIn('"name": "French Fries"', saved_order[5])

    def test_order_requires_login(self):
        response = self.client.post(
            "/api/orders",
            json={
                "delivery_address": "10 Main Street, Pune",
                "items": [{"name": "Espresso", "quantity": 1}],
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_order_rejects_item_not_in_menu(self):
        self.create_account()
        response = self.client.post(
            "/api/orders",
            json={
                "customer_name": "Asha",
                "email": "asha@example.com",
                "delivery_address": "10 Main Street, Pune",
                "items": [{"name": "Made-up drink", "quantity": 1}],
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_order_rejects_invalid_quantity(self):
        self.create_account()
        response = self.client.post(
            "/api/orders",
            json={
                "customer_name": "Asha",
                "email": "asha@example.com",
                "delivery_address": "10 Main Street, Pune",
                "items": [{"name": "Espresso", "quantity": 0}],
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_flask_serves_homepage_and_health_check(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertEqual(self.client.get("/api/health").get_json(), {"status": "ok"})
        order_page = self.client.get("/order.html")
        self.assertEqual(order_page.status_code, 200)
        order_page.close()
        login_page = self.client.get("/login.html")
        self.assertEqual(login_page.status_code, 200)
        login_page.close()
        self.assertGreater(len(self.client.get("/api/menu").get_json()["items"]), 0)


if __name__ == "__main__":
    unittest.main()