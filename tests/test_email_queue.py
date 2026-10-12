import unittest
from unittest.mock import MagicMock, patch

from config import Config
from flask import Flask, session
from services.email_queue import EmailQueueUnavailable, enqueue_email
from services.email_tasks import send_email
from auth.services import process_registration


class EmailQueueTests(unittest.TestCase):
    def test_registration_enqueues_otp_and_keeps_existing_session_flow(self):
        application = Flask(__name__)
        application.secret_key = "test-secret"
        form_data = {
            "email": "buyer@example.test",
            "prenom": "Awa",
            "password": "StrongPass1",
        }

        with application.test_request_context("/"):
            with patch("auth.services._generer_code_verification", return_value="123456"):
                with patch("auth.services._enqueue_otp_email") as enqueue:
                    self.assertTrue(process_registration(form_data))
            self.assertEqual(session.get("otp", {}).get("code"), "123456")

        enqueue.assert_called_once_with("buyer@example.test", "Awa", "123456")

    def test_registration_reports_queue_unavailability(self):
        application = Flask(__name__)
        application.secret_key = "test-secret"
        form_data = {
            "email": "buyer@example.test",
            "prenom": "Awa",
            "password": "StrongPass1",
        }

        with application.test_request_context("/"):
            with patch("auth.services._enqueue_otp_email", side_effect=EmailQueueUnavailable):
                self.assertFalse(process_registration(form_data))
            self.assertNotIn("otp", session)


    def test_enqueue_uses_bounded_timeout_and_retries(self):
        redis_connection = MagicMock()
        queue = MagicMock()
        job = MagicMock()
        queue.enqueue.return_value = job

        with patch("services.email_queue.get_redis_client", return_value=redis_connection):
            with patch("services.email_queue.Queue", return_value=queue):
                result = enqueue_email("buyer@example.test", "subject", "<p>test</p>")

        self.assertIs(result, job)
        args, kwargs = queue.enqueue.call_args
        self.assertEqual(args[0], "services.email_tasks.send_email")
        self.assertEqual(kwargs["timeout"], Config.RQ_EMAIL_JOB_TIMEOUT)
        self.assertEqual(kwargs["retry"].max, 3)
        self.assertEqual(kwargs["retry"].intervals, [5, 15, 60])

    def test_brevo_delivery_uses_connect_and_read_timeouts(self):
        response = MagicMock(status_code=201)

        with patch.object(Config, "EMAIL_PROVIDER", "brevo"):
            with patch.object(Config, "BREVO_API_KEY", "test-key"):
                with patch.object(Config, "EMAIL_SENDER", "sender@example.test"):
                    with patch("services.email_tasks.requests.post", return_value=response) as post:
                        send_email("buyer@example.test", "subject", "<p>test</p>")

        self.assertEqual(
            post.call_args.kwargs["timeout"],
            (Config.EMAIL_TIMEOUT_CONNECT, Config.EMAIL_TIMEOUT_READ),
        )
        response.raise_for_status.assert_called_once_with()

    def test_smtp_provider_is_supported(self):
        smtp = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp

        with patch.object(Config, "EMAIL_PROVIDER", "smtp"):
            with patch.object(Config, "EMAIL_SENDER", "sender@example.test"):
                with patch.object(Config, "MAIL_USE_SSL", True):
                    with patch("services.email_tasks.smtplib.SMTP_SSL", return_value=smtp_context) as smtp_ssl:
                        send_email("buyer@example.test", "subject", "<p>test</p>")

        smtp_ssl.assert_called_once_with(
            Config.MAIL_SERVER,
            Config.MAIL_PORT,
            timeout=max(Config.EMAIL_TIMEOUT_CONNECT, Config.EMAIL_TIMEOUT_READ),
        )
        smtp.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
