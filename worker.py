import logging

import redis
from rq import Queue, Worker

from config import Config


def main():
    redis_connection = redis.Redis.from_url(
        Config.REDIS_URL,
        socket_timeout=Config.REDIS_SOCKET_TIMEOUT,
        socket_connect_timeout=Config.REDIS_SOCKET_CONNECT_TIMEOUT,
        health_check_interval=Config.REDIS_HEALTH_CHECK_INTERVAL,
    )
    queue = Queue("emails", connection=redis_connection)
    Worker([queue], connection=redis_connection).work()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
