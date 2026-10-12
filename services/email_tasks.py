from email.message import EmailMessage
import logging
import smtplib

import requests

from config import Config


logger = logging.getLogger(__name__)


def send_email(to, subject, html_content):
    provider = Config.EMAIL_PROVIDER
    if provider == "brevo":
        if not Config.BREVO_API_KEY or not Config.EMAIL_SENDER:
            raise ValueError("BREVO_API_KEY et EMAIL_SENDER sont requis pour le provider Brevo.")

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json={
                "sender": {"name": "Elikya", "email": Config.EMAIL_SENDER},
                "to": [{"email": to}],
                "subject": subject,
                "htmlContent": html_content,
            },
            headers={
                "accept": "application/json",
                "api-key": Config.BREVO_API_KEY,
                "content-type": "application/json",
            },
            timeout=(Config.EMAIL_TIMEOUT_CONNECT, Config.EMAIL_TIMEOUT_READ),
        )
        response.raise_for_status()
        if response.status_code != 201:
            raise RuntimeError(f"Brevo a répondu avec le statut {response.status_code}.")
        logger.info("Email transmis au fournisseur Brevo.")
        return

    if provider == "smtp":
        if not Config.EMAIL_SENDER:
            raise ValueError("EMAIL_SENDER est requis pour le provider SMTP.")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"Elikya <{Config.EMAIL_SENDER}>"
        message["To"] = to
        message.set_content(html_content, subtype="html")
        timeout = max(Config.EMAIL_TIMEOUT_CONNECT, Config.EMAIL_TIMEOUT_READ)
        smtp_class = smtplib.SMTP_SSL if Config.MAIL_USE_SSL else smtplib.SMTP
        with smtp_class(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=timeout) as client:
            if Config.MAIL_USE_TLS and not Config.MAIL_USE_SSL:
                client.starttls()
            if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                client.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            client.send_message(message)
        logger.info("Email transmis au fournisseur SMTP.")
        return

    raise ValueError(f"EMAIL_PROVIDER non pris en charge : {provider}")
