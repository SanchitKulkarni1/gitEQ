# app/analysis/dependency_graph.py
from collections import defaultdict
from app.analysis.symbols import SymbolRecord

def build_dependency_graph(symbols: list[SymbolRecord]):
    graph = defaultdict(set)

    for s in symbols:
        if s.kind == "import":
            graph[s.file].add(s.name)

    # convert sets to lists
    return {k: list(v) for k, v in graph.items()}
