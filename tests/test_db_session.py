import unittest
from unittest.mock import MagicMock, patch

from mysql.connector.errors import PoolError
from werkzeug.exceptions import ServiceUnavailable

import ext


class DbSessionTests(unittest.TestCase):
    def test_closes_cursor_and_connection(self):
        connection = MagicMock()
        pool = MagicMock()
        pool.get_connection.return_value = connection

        with patch.object(ext, "db_pool", pool):
            with ext.db_session(dictionary=True) as (returned_connection, cursor):
                self.assertIs(returned_connection, connection)
                self.assertIs(cursor, connection.cursor.return_value)

        connection.cursor.assert_called_once_with(dictionary=True)
        connection.cursor.return_value.close.assert_called_once_with()
        connection.close.assert_called_once_with()

    def test_rolls_back_and_closes_after_query_error(self):
        connection = MagicMock()
        pool = MagicMock()
        pool.get_connection.return_value = connection

        with patch.object(ext, "db_pool", pool):
            with self.assertRaisesRegex(RuntimeError, "query failed"):
                with ext.db_session():
                    raise RuntimeError("query failed")

        connection.rollback.assert_called_once_with()
        connection.cursor.return_value.close.assert_called_once_with()
        connection.close.assert_called_once_with()

    def test_pool_exhaustion_returns_service_unavailable(self):
        pool = MagicMock()
        pool.get_connection.side_effect = PoolError("pool exhausted")

        with patch.object(ext, "db_pool", pool):
            with self.assertRaises(ServiceUnavailable) as context:
                ext.get_db_connection()

        self.assertEqual(context.exception.code, 503)


if __name__ == "__main__":
    unittest.main()
