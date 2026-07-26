import base64
import json
import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def _user_or_ip(request) -> str:
    """Bucket by Supabase user id when a JWT is present, else by client IP.

    The JWT payload is decoded without signature verification — fine for
    bucketing only; require_user_or_demo rejects forged tokens before any
    LLM/compile work happens.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = auth.removeprefix("Bearer ").strip().split(".")[1]
            payload += "=" * (-len(payload) % 4)
            sub = json.loads(base64.urlsafe_b64decode(payload)).get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    return get_remote_address(request)


# Redis-backed so all uvicorn workers share one counter and limits survive
# restarts. RATE_LIMIT_STORAGE=memory:// opts out for keyless local dev.
_storage_uri = os.getenv(
    "RATE_LIMIT_STORAGE", os.getenv("REDIS_URL", "redis://localhost:6379")
)

limiter = Limiter(
    key_func=_user_or_ip,
    storage_uri=_storage_uri,
    in_memory_fallback_enabled=True,  # degrade, don't 500, if Redis is down
)
