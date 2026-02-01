# app/models/state.py
from pydantic import BaseModel
from typing import List, Dict, Optional



class RepoState(BaseModel):
    repo_url: str

    owner: Optional[str] = None
    repo: Optional[str] = None
    branch: Optional[str] = None

    tree_raw: Optional[List[Dict]] = None
    tree_normalized: Optional[List[Dict]] = None
    files_selected: Optional[List[Dict]] = None
    files_content: Dict[str, str] = {}
    symbols: list = []
    dependency_graph: dict = {}
    archetype: Optional[str] = None
    layers: Dict = {}
    graph_metrics: Dict = {}
    architecture_hypotheses: List[Dict] = []
    assumptions: List[Dict] = []
    stress_results: list = []

    stats: Dict = {}
