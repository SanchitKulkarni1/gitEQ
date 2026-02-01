# app/analysis/assumption_inference.py

def infer_assumptions(state):
    assumptions = []

    layers = state.layers
    metrics = state.graph_metrics
    archetype = state.archetype

    # Backend absence assumption
    if archetype == "frontend" and not layers.get("backend"):
        assumptions.append({
            "assumption": "Backend logic is external to this repository",
            "evidence": {
                "archetype": archetype,
                "backend_layers": False,
            },
            "impact": "Frontend is tightly coupled to external API contracts",
            "confidence": 0.9,
        })

    # High UI centrality assumption
    ui_files = layers.get("ui", [])
    if ui_files:
        high_fan_in_ui = [
            f for f in ui_files
            if metrics["fan_in"].get(f, 0) > 5
        ]

        if high_fan_in_ui:
            assumptions.append({
                "assumption": "UI components act as architectural hubs",
                "evidence": {
                    "high_fan_in_files": high_fan_in_ui[:3],
                },
                "impact": "Changes to shared UI components have wide blast radius",
                "confidence": 0.8,
            })

    return assumptions
