from rq import Queue, Retry
from redis.exceptions import RedisError

from config import Config
from ext import get_redis_client


class EmailQueueUnavailable(Exception):
    """Signale que Redis n'est pas disponible pour accepter un email."""


def enqueue_email(to, subject, html_content):
    redis_connection = get_redis_client()
    if redis_connection is None:
        raise EmailQueueUnavailable("Redis n'est pas initialisé.")

    queue = Queue("emails", connection=redis_connection)
    retry = Retry(max=3, interval=[5, 15, 60])
    try:
        return queue.enqueue(
            "services.email_tasks.send_email",
            to,
            subject,
            html_content,
            timeout=Config.RQ_EMAIL_JOB_TIMEOUT,
            retry=retry,
        )
    except RedisError:
        raise
