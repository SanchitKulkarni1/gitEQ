# app/stress/stress_propagation.py
from collections import deque
from typing import List, Dict, Set, Tuple


def propagate_stress(
    dep_graph: dict,
    start_nodes: list,
    max_depth: int = 3,
    propagation_type: str = "traffic"
) -> List[str]:
    """
    Breadth-first stress propagation through dependency graph.
    
    Args:
        dep_graph: Dependency graph {file: [dependencies]}
        start_nodes: Starting files to propagate from
        max_depth: Maximum propagation depth
        propagation_type: Type of propagation (traffic, dependency, data, auth)
    
    Returns:
        List of impacted files in order of impact
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

        # Find downstream dependencies
        for downstream, deps in dep_graph.items():
            if node in deps and downstream not in visited:
                # Apply propagation rules based on type
                if _should_propagate(node, downstream, propagation_type):
                    queue.append((downstream, depth + 1))

    return impacted


def propagate_critical_path(
    dep_graph: dict,
    start_nodes: list,
    architecture_type: str
) -> List[Tuple[str, str]]:
    """
    Find critical path through the dependency graph that would cause cascading failures.
    
    Returns:
        List of (node, reason) tuples representing critical path
    """
    critical_path = []
    visited = set()

    for start in start_nodes:
        path = _trace_critical_dependencies(dep_graph, start, architecture_type, visited)
        critical_path.extend(path)

    return critical_path[:10]  # Return top 10 critical components


def _trace_critical_dependencies(
    dep_graph: dict,
    node: str,
    architecture_type: str,
    visited: set,
    depth: int = 0
) -> List[Tuple[str, str]]:
    """Recursively trace critical dependencies"""
    if node in visited or depth > 5:
        return []

    visited.add(node)
    critical = []

    # Determine if this node is critical based on architecture
    if _is_critical_component(node, architecture_type):
        critical.append((node, _get_criticality_reason(node, architecture_type)))

    # Find dependents (who depends on this node)
    dependents = [k for k, v in dep_graph.items() if node in v]

    # If many files depend on this, it's a critical shared component
    if len(dependents) > 5:
        critical.append((node, f"Shared dependency used by {len(dependents)} components"))

    for dependent in dependents[:3]:  # Limit breadth
        critical.extend(_trace_critical_dependencies(dep_graph, dependent, architecture_type, visited, depth + 1))

    return critical


def _should_propagate(from_node: str, to_node: str, propagation_type: str) -> bool:
    """Determine if stress should propagate based on file types and propagation type"""

    if propagation_type == "traffic":
        # Traffic flows from UI -> API -> Database
        traffic_flow = [
            (".tsx", ".ts"),  # Component to hook/service
            (".jsx", ".js"),  # Component to service
            (".ts", ".ts"),   # Service to service
            ("api/", "models/"),  # API to models
        ]
        return any(from_node.endswith(src) and to_node.endswith(dst) for src, dst in traffic_flow)

    elif propagation_type == "dependency":
        # Dependency propagation is bidirectional
        return True

    elif propagation_type == "data":
        # Data flows Database -> API -> UI
        return "model" in from_node.lower() or "db" in from_node.lower()

    elif propagation_type == "auth":
        # Auth flows through middleware and guards
        auth_keywords = ["auth", "middleware", "guard", "session"]
        return any(keyword in from_node.lower() for keyword in auth_keywords)

    return True


def _is_critical_component(node: str, architecture_type: str) -> bool:
    """Determine if a component is critical based on architecture"""
    
    critical_patterns = {
        "static_spa": ["App.tsx", "index.tsx", "main.tsx", "router"],
        "ssr_app": ["app.tsx", "_app.tsx", "server.ts", "api/", "middleware"],
        "backend_api": ["server.ts", "app.ts", "main.py", "database", "auth"],
        "full_stack": ["api/", "server", "database", "_app"],
    }

    patterns = critical_patterns.get(architecture_type, [])
    return any(pattern.lower() in node.lower() for pattern in patterns)


def _get_criticality_reason(node: str, architecture_type: str) -> str:
    """Get reason why component is critical"""
    
    if "app.tsx" in node.lower() or "main.tsx" in node.lower():
        return "Application entry point"
    if "api/" in node.lower():
        return "API endpoint handling requests"
    if "server" in node.lower():
        return "Server-side logic"
    if "database" in node.lower() or "db" in node.lower():
        return "Database access layer"
    if "auth" in node.lower():
        return "Authentication/authorization"
    
    return "Critical shared component"


def calculate_blast_radius(dep_graph: dict, node: str, max_depth: int = 5) -> Dict[str, int]:
    """
    Calculate how many components would be affected if this node fails.
    
    Returns:
        Dictionary with statistics about blast radius
    """
    impacted = propagate_stress(dep_graph, [node], max_depth=max_depth)
    
    return {
        "total_impacted": len(impacted),
        "direct_dependents": len([k for k, v in dep_graph.items() if node in v]),
        "depth_reached": max_depth,
        "blast_radius_score": min(1.0, len(impacted) / 50.0),  # Normalized score
    }