import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from notifications.models import Notification
from panier.models import Panier
from profils.models import Seller


class ModelPaginationTests(unittest.TestCase):
    def run_page_query(self, module, method, rows, *args, **kwargs):
        cursor = MagicMock()
        cursor.fetchall.return_value = rows

        @contextmanager
        def fake_db_session(dictionary=False):
            self.assertTrue(dictionary)
            yield None, cursor

        with patch(f"{module}.db_session", fake_db_session):
            page, next_cursor = method(*args, **kwargs)
        return page, next_cursor, cursor

    def test_seller_product_page_uses_cursor_and_bounded_query(self):
        page, next_cursor, cursor = self.run_page_query(
            "profils.models",
            Seller.get_produits_page,
            [{"id": 8}, {"id": 5}, {"id": 2}],
            17,
            after_id=10,
            limit=2,
        )

        self.assertEqual(page, [{"id": 8}, {"id": 5}])
        self.assertEqual(next_cursor, 5)
        sql, params = cursor.execute.call_args.args
        self.assertIn("id < %s", sql)
        self.assertIn("LIMIT %s", sql)
        self.assertNotIn("SELECT *", sql)
        self.assertEqual(params, (17, 10, 3))

    def test_notification_page_is_bounded_and_returns_next_cursor(self):
        page, next_cursor, cursor = self.run_page_query(
            "notifications.models",
            Notification.get_for_user_page,
            [{"id": 12}, {"id": 9}, {"id": 7}],
            4,
            after_id=15,
            limit=2,
        )

        self.assertEqual(page, [{"id": 12}, {"id": 9}])
        self.assertEqual(next_cursor, 9)
        sql, params = cursor.execute.call_args.args
        self.assertIn("ORDER BY id DESC LIMIT %s", sql)
        self.assertEqual(params, (4, 15, 3))

    def test_cart_page_keeps_full_cart_total(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {"total": 125.5}
        cursor.fetchall.return_value = [{"id": 6}, {"id": 4}, {"id": 2}]

        @contextmanager
        def fake_db_session(dictionary=False):
            self.assertTrue(dictionary)
            yield None, cursor

        with patch("panier.models.db_session", fake_db_session):
            items, total, next_cursor = Panier.get_panier_page(
                3, after_id=8, limit=2
            )

        self.assertEqual(items, [{"id": 6}, {"id": 4}])
        self.assertEqual(total, 125.5)
        self.assertEqual(next_cursor, 4)
        self.assertEqual(cursor.execute.call_count, 2)


if __name__ == "__main__":
    unittest.main()
