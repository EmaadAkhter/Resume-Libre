import os

import redis.asyncio as aioredis

_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            socket_connect_timeout=2,
        )
    return _client
