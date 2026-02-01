# app/ingestion/tree_fetcher.py
from app.ingestion.github_client import GitHubClient


async def fetch_repo_tree(
    client: GitHubClient,
    owner: str,
    repo: str,
    branch: str,
):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/git/trees/{branch}?recursive=1"
    )
    data = await client.get(url)

    if data.get("truncated"):
        raise RuntimeError({
            "error": "TREE_TRUNCATED",
            "message": "Repository exceeds Git Trees API limits"
        })

    return data["tree"]
