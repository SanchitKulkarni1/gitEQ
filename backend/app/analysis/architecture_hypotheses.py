# app/analysis/architecture_hypotheses.py

def infer_architecture_style(state):
    layers = state.layers
    metrics = state.graph_metrics
    archetype = state.archetype

    hypotheses = []

    # ---------------------------
    # Frontend architecture
    # ---------------------------
    if archetype == "frontend":
        ui_files = layers.get("ui", [])

        if len(ui_files) > 20:
            hypotheses.append({
                "claim": "Component-centric frontend SPA",
                "confidence": 0.85,
                "evidence": {
                    "ui_components": len(ui_files),
                    "dependency_hubs": metrics.get("hubs", [])[:3],
                },
            })

    # ---------------------------
    # Backend architecture
    # ---------------------------
    if archetype == "backend":
        api_files = layers.get("api", [])
        service_files = layers.get("services", [])

        if api_files and service_files:
            hypotheses.append({
                "claim": "Layered backend service (API → Services)",
                "confidence": 0.8,
                "evidence": {
                    "api_layers": len(api_files),
                    "service_layers": len(service_files),
                },
            })

    # ---------------------------
    # Fullstack architecture
    # ---------------------------
    if archetype == "fullstack":
        frontend = layers.get("frontend", {})
        backend = layers.get("backend", {})

        if frontend and backend:
            hypotheses.append({
                "claim": "Full-stack system with separated frontend and backend",
                "confidence": 0.8,
                "evidence": {
                    "frontend_layers": list(frontend.keys()),
                    "backend_layers": list(backend.keys()),
                },
            })

    return hypotheses
