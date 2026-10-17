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
        response = self.client.post(
            "/api/reservations",
            json={
                "name": "Asha",
                "email": "asha@example.com",
                "date": "10/20/2026",
                "time": "7:00 PM",
                "guests": 2,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["reservation_id"], 1)

    def test_order_is_saved_with_items(self):
        response = self.client.post(
            "/api/orders",
            json={
                "customer_name": "Asha",
                "email": "asha@example.com",
                "items": [
                    {"name": "Espresso", "quantity": 2},
                    {"name": "French Fries", "quantity": 1},
                ],
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["order_id"], 1)
        self.assertEqual(response.get_json()["total_rupees"], 297)

        import sqlite3

        connection = sqlite3.connect(self.database_path)
        try:
            saved_order = connection.execute(
                "SELECT items_json, total_rupees FROM orders WHERE id = 1"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(saved_order[1], 297)
        self.assertIn('"unit_price_rupees": 99', saved_order[0])
        self.assertIn('"name": "French Fries"', saved_order[0])

    def test_order_rejects_item_not_in_menu(self):
        response = self.client.post(
            "/api/orders",
            json={
                "customer_name": "Asha",
                "email": "asha@example.com",
                "items": [{"name": "Made-up drink", "quantity": 1}],
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_order_rejects_invalid_quantity(self):
        response = self.client.post(
            "/api/orders",
            json={
                "customer_name": "Asha",
                "email": "asha@example.com",
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
        self.assertGreater(len(self.client.get("/api/menu").get_json()["items"]), 0)


if __name__ == "__main__":
    unittest.main()