# app/ingestion/content_fetcher.py
import base64
from app.ingestion.github_client import GitHubClient
from app.ingestion.binary_rules import is_binary_path


MAX_BASE64_SIZE = 1_000_000   # 1 MB
MAX_TEXT_SIZE   = 2_000_000   # hard stop


async def fetch_file_content(
    client: GitHubClient,
    owner: str,
    repo: str,
    path: str,
    size: int,
) -> str | None:
    if is_binary_path(path):
        return None

    # Large text → raw
    headers = {}
    if size > MAX_BASE64_SIZE:
        headers["Accept"] = "application/vnd.github.raw+json"

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    resp = await client.client.get(url, headers=headers)
    resp.raise_for_status()

    # Raw mode
    if headers:
        text = resp.text
        if len(text) > MAX_TEXT_SIZE:
            return None
        return text

    # Base64 mode
    data = resp.json()
    if data.get("encoding") != "base64":
        return None

    decoded = base64.b64decode(data["content"]).decode(
        "utf-8", errors="ignore"
    )

    return decoded
