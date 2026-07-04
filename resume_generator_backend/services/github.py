import httpx

from services.cache import get_redis


async def fetch_github_readme(username: str) -> str:
    if not username:
        return ""

    try:
        redis = get_redis()
        cached = await redis.get(f"github:{username}")
        if cached:
            return cached.decode()
    except Exception:
        redis = None

    content = await _fetch_from_github(username)
    if content and redis:
        try:
            await redis.setex(f"github:{username}", 3600, content)  # 1h TTL
        except Exception:
            pass
    return content


async def _fetch_from_github(username: str) -> str:
    url = f"https://api.github.com/repos/{username}/{username}/readme"
    headers = {"Accept": "application/vnd.github.raw"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            return response.text
        else:
            print(f"GitHub README fetch failed: {response.status_code}")
            return ""
    except Exception as e:
        print(f"GitHub README fetch error: {e}")
        return ""
