import httpx


async def fetch_github_readme(username: str) -> str:
    if not username:
        return ""

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
