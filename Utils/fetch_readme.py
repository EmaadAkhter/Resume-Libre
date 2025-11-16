import os
import os
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from dotenv import load_dotenv
load_dotenv()

async def fetch_github_readme(username: str) -> str:

    if not username:
        return ""

    api_key = os.getenv("MCP_API")
    mcp_url = os.getenv("MCP_URL")

    if not api_key or not mcp_url:
        print("MCP credentials not configured")
        return ""

    auth = BearerAuth(token=api_key)
    async with Client(mcp_url, auth=auth) as client:
        result = await client.call_tool(
            name="get_github_readme",
            arguments={"user_name": username}
        )
        return str(result)