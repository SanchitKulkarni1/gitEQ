# app/ingestion/repo_meta.py
from app.ingestion.github_client import GitHubClient


async def fetch_repo_meta(
    client: GitHubClient,
    owner: str,
    repo: str,
):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = await client.get(url)

    return {
        "default_branch": data["default_branch"],
        "size_kb": data["size"],
        "fork": data["fork"],
        "archived": data["archived"],
    }
