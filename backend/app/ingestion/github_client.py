# app/ingestion/github_client.py
import httpx
from typing import Optional


class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=30,
            follow_redirects=True,
        )

    async def get(self, url: str):
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
