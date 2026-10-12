import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from werkzeug.exceptions import BadRequest

from produits.models import Produits
from services.pagination import parse_cursor


class CursorTests(unittest.TestCase):
    def test_parse_cursor(self):
        self.assertIsNone(parse_cursor(None))
        self.assertEqual(parse_cursor("42"), 42)

    def test_rejects_invalid_cursor(self):
        for value in ("invalid", "0", "-4"):
            with self.subTest(value=value):
                with self.assertRaises(BadRequest):
                    parse_cursor(value)

    def test_product_search_fetches_one_extra_row_for_next_cursor(self):
        rows = [
            {"id": 9, "name": "first"},
            {"id": 7, "name": "second"},
            {"id": 5, "name": "lookahead"},
        ]
        cursor = MagicMock()
        cursor.fetchall.return_value = rows

        @contextmanager
        def fake_db_session(dictionary=False):
            self.assertTrue(dictionary)
            yield None, cursor

        with patch("produits.models.db_session", fake_db_session):
            products, next_cursor = Produits.search_page(
                "phone", after_id=10, limit=2
            )

        self.assertEqual([product["id"] for product in products], [9, 7])
        self.assertEqual(next_cursor, 7)
        sql, params = cursor.execute.call_args.args
        self.assertIn("p.id < %s", sql)
        self.assertIn("LIMIT %s", sql)
        self.assertNotIn("p.*", sql)
        self.assertEqual(params, ("%phone%", "%phone%", 10, 3))


if __name__ == "__main__":
    unittest.main()
