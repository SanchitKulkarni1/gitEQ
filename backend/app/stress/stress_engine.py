# app/stress/stress_engine.py
from collections import defaultdict
from app.stress.stress_propagation import propagate_stress
from app.stress.evidence_mapper import map_evidence
from app.stress.stress_models import StressResult

def build_directed_graph(dep_graph: dict, direction: str):
    adjacency_map = defaultdict(list)
    for downstream, deps in dep_graph.items():
        if direction == "dependency":
            for dep in deps:
                adjacency_map[dep].append(downstream)
        elif direction == "traffic":
            adjacency_map[downstream].extend(deps)
    return adjacency_map

def find_matching_files(state, target_layer_name):
    """
    SMART LOOKUP: Maps 'ui' -> 'frontend', 'components', etc.
    """
    target = target_layer_name.lower()
    found_files = []
    
    # Aliases to help the engine find files
    aliases = {
        "ui": ["frontend", "web", "client", "pages", "components", "views", "app", "src"], # Added 'src' for small repos
        "api": ["backend", "server", "controllers", "routes", "endpoints"],
        "database": ["db", "data", "storage", "models", "prisma", "sql"],
        "auth": ["login", "security", "user", "session"]
    }

    possible_names = [target]
    if target in aliases:
        possible_names.extend(aliases[target])

    # Search in state.layers keys
    for layer_key, files in state.layers.items():
        if any(alias in layer_key.lower() for alias in possible_names):
            found_files.extend(files)
            
    # Fallback: If no layers match, and it's a "UI" query on a frontend repo, return EVERYTHING.
    if not found_files and target in ["ui", "frontend"]:
        # Gather all files that end in .tsx, .jsx, .css
        for f in state.files_content.keys():
            if f.endswith(('.tsx', '.jsx', '.css', '.html')):
                found_files.append(f)

    return list(set(found_files))

def run_stress_test(state, stress_vector):
    violated = []
    
    # 1. Resolve Start Nodes (Using Smart Lookup)
    start_nodes = []
    for layer_name in stress_vector.target_layers:
        files = find_matching_files(state, layer_name)
        start_nodes.extend(files)

    # If still no nodes, we can't run the test
    if not start_nodes:
        return StressResult(
            stress=stress_vector.name,
            violated_assumptions=[], 
            affected_files=[], 
            impact_path=[], 
            failure_mode=f"Configuration Error: Could not map layers {stress_vector.target_layers} to any files. (Available layers: {list(state.layers.keys())})", 
            confidence=0.0
        )

    # 2. Build Graph & Propagate
    direction = getattr(stress_vector, "propagation_type", "traffic")
    graph = build_directed_graph(state.dependency_graph, direction)
    
    impacted = propagate_stress(graph, start_nodes=start_nodes)
    evidence = map_evidence(state.layers, impacted)

    return StressResult(
        stress=stress_vector.name,
        violated_assumptions=violated,
        affected_files=impacted[:15],
        impact_path=impacted[:5],
        failure_mode=f"Cascading {direction} failure",
        confidence=min(0.95, 0.5 + stress_vector.severity / 2),
    )