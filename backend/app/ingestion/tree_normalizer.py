# app/ingestion/tree_normalizer.py
from typing import List, Dict


def normalize_tree(tree: List[Dict]) -> List[Dict]:
    normalized = []

    for item in tree:
        normalized.append({
            "path": item["path"],
            "type": item["type"],  # blob | tree
            "sha": item.get("sha"),
            "size": item.get("size", 0),
        })

    return normalized
