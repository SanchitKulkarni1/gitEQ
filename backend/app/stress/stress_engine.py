# app/stress/stress_engine.py
from collections import defaultdict
from typing import List, Dict, Optional

# Import the detectors and models correctly
from app.stress.stress_propagation import propagate_stress
from app.stress.evidence_mapper import (
    map_evidence,
    identify_bottlenecks,
    generate_safe_components_list
)
from app.stress.stress_models import StressResult, BottleneckAnalysis, ArchitectureType

# -------------------------------------------------------------------------
# 1. HELPER FUNCTIONS
# -------------------------------------------------------------------------

def build_directed_graph(dep_graph: dict, direction: str) -> Dict[str, List[str]]:
    """Build a directed dependency graph based on propagation direction."""
    adjacency_map = defaultdict(list)
    
    for downstream, deps in dep_graph.items():
        if direction == "dependency":
            for dep in deps:
                adjacency_map[dep].append(downstream)
        elif direction in ["traffic", "data", "auth"]:
            adjacency_map[downstream].extend(deps)
    
    return adjacency_map

def find_matching_files(state, target_layer_name: str, architecture_type: ArchitectureType) -> List[str]:
    """SMART LOOKUP: Maps abstract layer names to actual files based on architecture."""
    target = target_layer_name.lower()
    found_files = []
    
    # Architecture-specific aliases (Simplified for brevity)
    aliases = {
        "static_spa": {"ui": ["components", "pages", "src"], "assets": ["public"]},
        "ssr_app": {"ui": ["components", "app"], "api": ["api", "server"]},
        "backend_api": {"api": ["routes", "controllers"], "database": ["models", "db"]},
    }
    
    # Get aliases
    arch_aliases = aliases.get(architecture_type.value, {}) if architecture_type else {}
    possible_names = arch_aliases.get(target, [target])
    
    # Generic fallback
    generic_aliases = {
        "ui": ["frontend", "client", "components", "src"],
        "api": ["backend", "server", "controllers", "routes"],
        "database": ["db", "models", "prisma", "sql"],
        "auth": ["login", "user", "auth"]
    }
    if target in generic_aliases:
        possible_names.extend(generic_aliases[target])
    
    # Search in state.layers keys
    for layer_key, files in state.layers.items():
        if any(alias in layer_key.lower() for alias in possible_names):
            found_files.extend(files)
            
    return list(set(found_files))

# -------------------------------------------------------------------------
# 2. MAIN ENGINE (Merged & Fixed)
# -------------------------------------------------------------------------

def run_stress_test(state, stress_vector, repo_context) -> StressResult:
    """
    Run stress test with architecture awareness.
    """
    
    # 1. CRITICAL CHECK: Ensure Architecture Context exists
    if repo_context is None:
        raise ValueError(
            "repo_context is missing! You must detect architecture BEFORE running stress tests.\n"
            "Fix: In your main pipeline, call 'detect_architecture' and pass the result here."
        )
    
    architecture_type = repo_context.architecture_type
    tech_stack = repo_context.tech_stack

    # 2. Validate Applicability
    # If the stress test isn't relevant for this architecture (e.g. "Database" test on "Frontend" app)
    if architecture_type not in stress_vector.architecture_types:
        return StressResult(
            stress=stress_vector.name,
            architecture_type=architecture_type,
            tech_stack=tech_stack,
            is_applicable=False,
            violated_assumptions=[],
            affected_files=[],
            impact_path=[],
            failure_mode=f"Not applicable to {architecture_type.value} architecture",
            confidence=0.0,
            recommendations=[f"This test targets: {', '.join(t.value for t in stress_vector.architecture_types)}"],
        )

    # 3. Resolve Start Nodes
    start_nodes = []
    for layer_name in stress_vector.target_layers:
        files = find_matching_files(state, layer_name, architecture_type)
        start_nodes.extend(files)

    if not start_nodes:
        return StressResult(
            stress=stress_vector.name,
            architecture_type=architecture_type,
            tech_stack=tech_stack,
            is_applicable=False,
            violated_assumptions=[],
            affected_files=[],
            impact_path=[],
            failure_mode=f"Configuration Error: Could not map layers {stress_vector.target_layers} to any files.",
            confidence=0.0,
        )

    # 4. Build Graph & Propagate
    direction = getattr(stress_vector, "propagation_type", "traffic")
    graph = build_directed_graph(state.dependency_graph, direction)
    impacted = propagate_stress(graph, start_nodes=start_nodes, propagation_type=direction)

    # 5. Analyze Bottlenecks
    bottlenecks = identify_bottlenecks(
        impacted, state.dependency_graph, architecture_type.value, tech_stack, stress_vector.name
    )

    # 6. Map Evidence & Result
    evidence = map_evidence(state.layers, impacted, architecture_type.value, tech_stack)
    safe_components = generate_safe_components_list(list(state.files_content.keys()), impacted, architecture_type.value)

    # Determine failure mode logic (simplified for brevity)
    failure_mode = "Cascading failure"
    if bottlenecks:
        failure_mode = f"Bottleneck at {bottlenecks[0].component}: {bottlenecks[0].reason}"
    
    return StressResult(
        stress=stress_vector.name,
        architecture_type=architecture_type,
        tech_stack=tech_stack,
        is_applicable=True,
        violated_assumptions=[],
        affected_files=impacted[:20],
        impact_path=impacted[:5],
        bottlenecks=bottlenecks,
        failure_mode=failure_mode,
        confidence=0.85, # Simplified calculation
        recommendations=[], # Populate using your existing _generate_recommendations logic
        safe_components=safe_components,
    )