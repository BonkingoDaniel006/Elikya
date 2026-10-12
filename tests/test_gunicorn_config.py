import os
import runpy
import unittest
from pathlib import Path
from unittest.mock import patch


CONFIG_PATH = Path(__file__).resolve().parents[1] / "gunicorn.conf.py"


class GunicornConfigTests(unittest.TestCase):
    def load_config(self, environment):
        with patch.dict(os.environ, environment, clear=True):
            return runpy.run_path(str(CONFIG_PATH))

    def test_defaults(self):
        config = self.load_config({})

        self.assertEqual(config["bind"], "127.0.0.1:8000")
        self.assertEqual(config["worker_class"], "gthread")
        self.assertEqual(config["workers"], 4)
        self.assertEqual(config["threads"], 4)
        self.assertEqual(config["timeout"], 30)
        self.assertEqual(config["graceful_timeout"], 30)
        self.assertEqual(config["max_requests"], 1000)
        self.assertEqual(config["max_requests_jitter"], 100)

    def test_environment_overrides(self):
        config = self.load_config(
            {
                "GUNICORN_BIND": "127.0.0.1:9000",
                "GUNICORN_WORKERS": "2",
                "GUNICORN_THREADS": "8",
                "GUNICORN_TIMEOUT": "45",
                "GUNICORN_GRACEFUL_TIMEOUT": "40",
                "GUNICORN_MAX_REQUESTS": "750",
                "GUNICORN_MAX_REQUESTS_JITTER": "50",
            }
        )

        self.assertEqual(config["bind"], "127.0.0.1:9000")
        self.assertEqual(config["workers"], 2)
        self.assertEqual(config["threads"], 8)
        self.assertEqual(config["timeout"], 45)
        self.assertEqual(config["graceful_timeout"], 40)
        self.assertEqual(config["max_requests"], 750)
        self.assertEqual(config["max_requests_jitter"], 50)


if __name__ == "__main__":
    unittest.main()
