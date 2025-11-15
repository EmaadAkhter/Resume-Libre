from fastmcp import FastMCP
import subprocess

mcp = FastMCP("github_fetch")

@mcp.tool
def get_github_readme(user_name: str) -> str:
    try:
        subprocess.run(f"git clone https://github.com/{user_name}/{user_name}.git", shell=True, check=True)

        with open(f'{user_name}/README.md', 'r', encoding='utf-8') as file:
            read_content = file.read()

        return read_content

    except Exception as e:
        print(f"Error: {e}")
        return ""
    finally:
        subprocess.run(f"rm -rf ./{user_name}", shell=True)


if __name__ == "__main__":
    mcp.run()