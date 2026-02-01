import os
import httpx
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        # Use provided token, or fallback to environment variable
        auth_token = token or os.getenv("GITHUB_TOKEN")
        
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            # Good to have a warning so you know why it's slow/failing
            print("Warning: No GitHub token found. Using unauthenticated requests.")

        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=30,
            follow_redirects=True,
        )

    async def get(self, url: str):
        resp = await self.client.get(url)
        # Helpful for debugging rate limits
        if resp.status_code == 403:
            limit = resp.headers.get("x-ratelimit-remaining")
            print(f"Rate limit hit. Remaining: {limit}")
            
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()