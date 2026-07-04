import asyncio
import json
import os

import httpx

from services.cache import get_redis

APIFY_BASE = "https://api.apify.com/v2"
ACTOR_ID = "datadoping~linkedin-profile-scraper"


async def fetch_linkedin_profile(profile_url: str) -> dict:
    if not profile_url:
        return {}

    try:
        redis = get_redis()
        cached = await redis.get(f"linkedin:{profile_url}")
        if cached:
            return json.loads(cached)
    except Exception:
        redis = None

    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        return {}

    data = await _fetch_from_apify(profile_url, token)
    if data and redis:
        try:
            await redis.setex(f"linkedin:{profile_url}", 86400, json.dumps(data))
        except Exception:
            pass
    return data


async def _fetch_from_apify(profile_url: str, token: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Start actor run
        resp = await client.post(
            f"{APIFY_BASE}/acts/{ACTOR_ID}/runs",
            params={"token": token},
            json={"profiles": [profile_url]},
        )
        if resp.status_code not in (200, 201):
            print(f"Apify run start failed: {resp.status_code} - {resp.text[:200]}")
            return {}

        run_data = resp.json().get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")
        if not run_id:
            print(f"Apify: no run ID in response: {resp.text[:200]}")
            return {}

        print(f"Apify: run {run_id} started, polling...")

        # 2. Poll until SUCCEEDED or timeout (~3 min)
        for _ in range(36):
            await asyncio.sleep(5)
            status_resp = await client.get(
                f"{APIFY_BASE}/actor-runs/{run_id}",
                params={"token": token},
            )
            if status_resp.status_code == 200:
                status = status_resp.json().get("data", {}).get("status", "")
                print(f"Apify: run status = {status}")
                if status == "SUCCEEDED":
                    break
                if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    print(f"Apify run {status}: {run_id}")
                    return {}

        # 3. Fetch dataset items
        items_resp = await client.get(
            f"{APIFY_BASE}/datasets/{dataset_id}/items",
            params={"token": token},
        )
        if items_resp.status_code == 200:
            items = items_resp.json()
            print(f"Apify: got {len(items) if isinstance(items, list) else 0} items")
            if (
                isinstance(items, list)
                and items
                and items[0].get("success") is not False
            ):
                return items[0]
        else:
            print(
                f"Apify dataset fetch failed: {items_resp.status_code} - {items_resp.text[:200]}"
            )

    return {}
