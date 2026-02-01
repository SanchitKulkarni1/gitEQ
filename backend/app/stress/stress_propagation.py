# app/stress/stress_propagation.py
from collections import deque


def propagate_stress(dep_graph: dict, start_nodes: list, max_depth=3):
    """
    Breadth-first stress propagation through dependency graph.
    """
    visited = set()
    queue = deque([(n, 0) for n in start_nodes])
    impacted = []

    while queue:
        node, depth = queue.popleft()
        if node in visited or depth > max_depth:
            continue

        visited.add(node)
        impacted.append(node)

        for downstream, deps in dep_graph.items():
            if node in deps:
                queue.append((downstream, depth + 1))

    return impacted
