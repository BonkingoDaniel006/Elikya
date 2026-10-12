import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from flask import Flask, abort
from redis.exceptions import ConnectionError as RedisConnectionError
from werkzeug.exceptions import ServiceUnavailable

from services.rate_limits import account_rate_limit_key


class RateLimitKeyTests(unittest.TestCase):
    def test_email_key_is_normalized_and_does_not_expose_email(self):
        application = Flask(__name__)
        anonymous_user = MagicMock(is_authenticated=False)
        with application.test_request_context(
            "/", method="POST", data={"email": " Seller@Example.test "}
        ):
            with patch("services.rate_limits.current_user", anonymous_user):
                first_key = account_rate_limit_key()

        with application.test_request_context(
            "/", method="POST", data={"email": "seller@example.test"}
        ):
            with patch("services.rate_limits.current_user", anonymous_user):
                second_key = account_rate_limit_key()

        self.assertEqual(first_key, second_key)
        self.assertNotIn("seller@example.test", first_key)
        self.assertTrue(first_key.startswith("account:"))


class HealthCheckTests(unittest.TestCase):
    def make_app(self):
        with patch("app.init_db_pool"), patch("app.init_redis_client"):
            from app import create_app

            application = create_app()
        application.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        return application

    def test_healthz_checks_mysql_and_redis_and_sets_request_id(self):
        application = self.make_app()
        cursor = MagicMock()
        db_context = MagicMock()
        db_context.__enter__.return_value = (MagicMock(), cursor)
        redis_client = MagicMock()

        with patch("app.db_session", return_value=db_context):
            with patch("app.get_redis_client", return_value=redis_client):
                response = application.test_client().get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["checks"], {"mysql": True, "redis": True})
        self.assertTrue(response.headers.get("X-Request-ID"))
        cursor.execute.assert_called_once_with("SELECT 1")
        redis_client.ping.assert_called_once_with()

    def test_healthz_returns_503_when_a_dependency_is_down(self):
        application = self.make_app()
        redis_client = MagicMock()
        redis_client.ping.side_effect = RedisConnectionError("unavailable")

        @contextmanager
        def unavailable_database():
            raise ServiceUnavailable("database unavailable")
            yield

        with patch("app.db_session", side_effect=unavailable_database):
            with patch("app.get_redis_client", return_value=redis_client):
                response = application.test_client().get("/healthz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["checks"], {"mysql": False, "redis": False})

    def test_rate_limit_errors_return_a_clean_429_response(self):
        application = self.make_app()
        application.add_url_rule(
            "/_test/rate-limit",
            view_func=lambda: abort(429),
        )

        response = application.test_client().get("/_test/rate-limit")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json["error"], "Trop de requêtes. Veuillez réessayer plus tard.")
        self.assertTrue(response.json["request_id"])


if __name__ == "__main__":
    unittest.main()
