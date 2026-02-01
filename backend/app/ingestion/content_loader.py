# app/ingestion/content_loader.py
import asyncio
from typing import Dict
from app.ingestion.content_fetcher import fetch_file_content
from app.ingestion.github_client import GitHubClient


CONCURRENCY_LIMIT = 5


async def load_contents(
    client: GitHubClient,
    owner: str,
    repo: str,
    files: list[dict],
) -> Dict[str, str]:

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    results: Dict[str, str] = {}

    async def _fetch(f):
        async with semaphore:
            try:
                content = await fetch_file_content(
                    client,
                    owner,
                    repo,
                    f["path"],
                    f.get("size", 0),
                )
                if content:
                    results[f["path"]] = content
            except Exception:
                pass

    await asyncio.gather(*[_fetch(f) for f in files])
    return results
