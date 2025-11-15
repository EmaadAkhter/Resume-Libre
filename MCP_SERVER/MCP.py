from fastmcp import FastMCP
import requests

mcp = FastMCP("github_fetch")


@mcp.tool
def get_github_readme(user_name: str) -> str:
    url = f"https://api.github.com/repos/{user_name}/{user_name}/readme"
    response = requests.get(url, headers={"Accept": "application/vnd.github.raw"})

    if response.status_code == 200:
        return response.text
    else:
        return f"Error: Could not fetch README (status code: {response.status_code})"


if __name__ == "__main__":
    mcp.run()