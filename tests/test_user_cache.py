import json
import unittest
from unittest.mock import MagicMock, patch

from redis.exceptions import RedisError

from auth.models import User


class UserCacheTests(unittest.TestCase):
    def test_cache_hit_avoids_database_read(self):
        cached_user = {
            "id": 12,
            "email": "buyer@example.test",
            "prenom": "Awa",
            "nom": "Test",
        }
        cache = MagicMock()
        cache.get.return_value = json.dumps(cached_user)

        with patch("auth.models.get_redis_client", return_value=cache):
            with patch.object(User, "get_by_id") as get_by_id:
                user = User.get_cached_by_id(12)

        self.assertEqual(user.id, 12)
        self.assertEqual(user.email, "buyer@example.test")
        self.assertIsNone(user.password)
        get_by_id.assert_not_called()

    def test_cache_miss_stores_only_non_secret_user_fields(self):
        cache = MagicMock()
        cache.get.return_value = None
        user = User(
            id=5,
            email="seller@example.test",
            password="must-not-be-cached",
            prenom="Lina",
            nom="Seller",
        )

        with patch("auth.models.get_redis_client", return_value=cache):
            with patch.object(User, "get_by_id", return_value=user):
                returned_user = User.get_cached_by_id(5)

        self.assertIs(returned_user, user)
        cache.setex.assert_called_once()
        stored_data = json.loads(cache.setex.call_args.args[2])
        self.assertEqual(stored_data["id"], 5)
        self.assertNotIn("password", stored_data)

    def test_redis_failure_falls_back_to_database(self):
        cache = MagicMock()
        cache.get.side_effect = RedisError("unavailable")
        user = User(id=9, email="user@example.test")

        with patch("auth.models.get_redis_client", return_value=cache):
            with patch.object(User, "get_by_id", return_value=user) as get_by_id:
                returned_user = User.get_cached_by_id(9)

        self.assertIs(returned_user, user)
        get_by_id.assert_called_once_with(9)


if __name__ == "__main__":
    unittest.main()
