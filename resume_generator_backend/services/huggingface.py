import json
import logging
import re

import httpx

from services.cache import get_redis

logger = logging.getLogger("resume_libre")

HF_API = "https://huggingface.co/api"


def _normalize_username(username: str) -> str:
    """Accept a bare username or a pasted profile URL."""
    username = (username or "").strip()
    username = re.sub(r"^(?:https?://)?(?:www\.)?huggingface\.co/", "", username)
    return username.strip("/ ")


async def fetch_huggingface_profile(username: str) -> dict:
    username = _normalize_username(username)
    if not username:
        return {}

    try:
        redis = get_redis()
        cached = await redis.get(f"hf:{username}")
        if cached:
            return json.loads(cached)
    except Exception:
        redis = None

    data = await _fetch_from_huggingface(username)
    if data and redis:
        try:
            await redis.setex(f"hf:{username}", 86400, json.dumps(data))  # 24h TTL
        except Exception:
            pass
    return data


async def _fetch_from_huggingface(username: str) -> dict:
    endpoints = {
        "models": f"{HF_API}/models?author={username}&sort=downloads&direction=-1&limit=10",
        "datasets": f"{HF_API}/datasets?author={username}&limit=10",
        "spaces": f"{HF_API}/spaces?author={username}&limit=10",
    }

    data: dict = {}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            for section, url in endpoints.items():
                response = await client.get(url)
                if response.status_code != 200:
                    logger.warning(
                        f"HuggingFace {section} fetch failed: {response.status_code}"
                    )
                    continue
                items = [
                    {
                        "id": item["id"],
                        "downloads": item.get("downloads", 0) or 0,
                        "likes": item.get("likes", 0) or 0,
                    }
                    for item in response.json()
                    if isinstance(item, dict) and item.get("id")
                ]
                if items:
                    data[section] = items
    except Exception as e:
        logger.warning(f"HuggingFace fetch error: {e}")
        return {}

    # A nonexistent user yields empty lists on every endpoint, not a 404 —
    # all-empty means "no profile", so callers get the usual silent {}.
    return data
