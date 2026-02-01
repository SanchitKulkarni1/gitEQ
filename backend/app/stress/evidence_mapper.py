# app/stress/evidence_mapper.py

def map_evidence(layers: dict, impacted_files: list):
    evidence = []

    for layer, files in layers.items():
        for f in files:
            if f in impacted_files:
                evidence.append({
                    "file": f,
                    "layer": layer,
                    "reason": "Affected by stress propagation",
                })

    return evidence
