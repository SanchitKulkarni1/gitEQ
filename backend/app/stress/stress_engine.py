# app/stress/stress_engine.py
from app.stress.stress_propagation import propagate_stress
from app.stress.evidence_mapper import map_evidence
from app.stress.stress_models import StressResult


def run_stress_test(state, stress_vector):
    violated = []

    for a in state.assumptions:
        if any(layer in stress_vector.target_layers for layer in state.layers):
            violated.append(a)

    # Start nodes = layer entry points
    start_nodes = []
    for layer in stress_vector.target_layers:
        start_nodes.extend(state.layers.get(layer, []))

    impacted = propagate_stress(
        state.dependency_graph,
        start_nodes=start_nodes,
    )

    evidence = map_evidence(state.layers, impacted)

    return StressResult(
        stress=stress_vector.name,
        violated_assumptions=violated,
        affected_files=impacted[:10],
        impact_path=impacted[:5],
        failure_mode="Structural fragility under stress conditions",
        confidence=min(0.95, 0.5 + stress_vector.severity / 2),
    )
