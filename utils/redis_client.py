import logging
import time
from threading import Lock

import redis

from config.settings import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


class RedisClient:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._client = None
        return cls._instance

    def connect(self) -> redis.Redis:
        if self._client is not None:
            return self._client
        retries = 5
        for attempt in range(1, retries + 1):
            try:
                client = redis.Redis.from_url(
                    settings.REDIS_URL,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    health_check_interval=30,
                    decode_responses=True,
                )
                client.ping()
                self._client = client
                logger.info("Redis connection established")
                return self._client
            except Exception as exc:
                logger.error("Redis connection attempt %s/%s failed: %s", attempt, retries, exc)
                time.sleep(min(2**attempt, 10))
        raise RuntimeError("Unable to connect to Redis after retries")

    def get_client(self) -> redis.Redis:
        try:
            client = self.connect()
            client.ping()
            return client
        except Exception:
            self._client = None
            return self.connect()


redis_client = RedisClient()
