# app/graphs/ingestion_nodes.py
import yaml
from urllib.parse import urlparse
from app.ingestion.github_client import GitHubClient
from app.ingestion.repo_meta import fetch_repo_meta
from app.ingestion.tree_fetcher import fetch_repo_tree
from app.ingestion.tree_normalizer import normalize_tree
from app.ingestion.glob_filter import GlobFilter
from app.models.state import RepoState


client = GitHubClient()


def parse_repo(state: RepoState) -> RepoState:
    path = urlparse(state.repo_url).path.strip("/")
    parts = path.split("/")
    
    if len(parts) >= 2:
        state.owner = parts[0]
        state.repo = parts[1].removesuffix(".git")
        
    return state

async def resolve_branch(state: RepoState) -> RepoState:
    meta = await fetch_repo_meta(client, state.owner, state.repo)
    state.branch = meta["default_branch"]
    state.stats["repo_size_kb"] = meta["size_kb"]
    return state


async def load_tree(state: RepoState) -> RepoState:
    tree = await fetch_repo_tree(
        client,
        state.owner,
        state.repo,
        state.branch,
    )
    state.tree_raw = tree
    state.tree_normalized = normalize_tree(tree)
    state.stats["files_total"] = len(tree)
    return state


def apply_glob_filter(state: RepoState) -> RepoState:
    with open("app/configs/globs.yaml") as f:
        cfg = yaml.safe_load(f)

    gf = GlobFilter(cfg["include"], cfg["exclude"])
    selected = gf.filter(state.tree_normalized)

    state.files_selected = selected
    state.stats["files_selected"] = len(selected)
    state.stats["paths"] = [f["path"] for f in selected]

    return state
