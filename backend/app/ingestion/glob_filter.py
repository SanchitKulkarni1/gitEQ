# app/ingestion/glob_filter.py
import pathspec
from typing import List, Dict


class GlobFilter:
    def __init__(self, include: List[str], exclude: List[str]):
        self.include = pathspec.PathSpec.from_lines("gitwildmatch", include)
        self.exclude = pathspec.PathSpec.from_lines("gitwildmatch", exclude)

    def filter(self, items: List[Dict]) -> List[Dict]:
        results = []

        for item in items:
            if item["type"] != "blob":
                continue

            path = item["path"]

            if self.exclude.match_file(path):
                continue

            if self.include.match_file(path):
                results.append(item)

        return results
