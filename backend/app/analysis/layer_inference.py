# app/analysis/layer_inference.py
from app.analysis.archetype_detection import detect_archetype
from app.models.state import RepoState

def infer_frontend_layers(files):
    layers = {
        "ui": [],
        "hooks": [],
        "pages": [],
        "utils": [],
        "unknown": [],
    }

    for f in files:
        if "/ui/" in f or "/components/" in f:
            layers["ui"].append(f)
        elif "/hooks/" in f:
            layers["hooks"].append(f)
        elif "/pages/" in f:
            layers["pages"].append(f)
        elif "/lib/" in f or "/utils/" in f:
            layers["utils"].append(f)
        else:
            layers["unknown"].append(f)

    return layers

def infer_backend_layers(files):
    layers = {
        "api": [],
        "services": [],
        "models": [],
        "db": [],
        "utils": [],
        "unknown": [],
    }

    for f in files:
        if "/api/" in f or "/routes/" in f:
            layers["api"].append(f)
        elif "/service/" in f or "/services/" in f:
            layers["services"].append(f)
        elif "/model/" in f or "/models/" in f or "/schema/" in f:
            layers["models"].append(f)
        elif "/db/" in f or "/repository/" in f:
            layers["db"].append(f)
        elif "/utils/" in f or "/core/" in f:
            layers["utils"].append(f)
        else:
            layers["unknown"].append(f)

    return layers

def infer_fullstack_layers(files):
    return {
        "frontend": infer_frontend_layers(files),
        "backend": infer_backend_layers(files),
    }


def infer_layers(state: RepoState):
    # Now you can keep your code exactly the same using the . method
    files = list(state.dependency_graph.keys())
    
    # ---------------------------------------------------------
    # 🚨 FIX: Pass 3 arguments and extract ["archetype"] string
    # ---------------------------------------------------------
    detection_result = detect_archetype(
        files, 
        state.symbols, 
        state.files_content  # <--- NEW ARGUMENT REQUIRED
    )
    
    # The new detector returns a Dict, extract the string for backward compatibility
    archetype = detection_result["archetype"]

    state.archetype = archetype

    if archetype == "frontend":
        return {"layers": infer_frontend_layers(files), "archetype": archetype}

    if archetype == "backend":
        return {"layers": infer_backend_layers(files), "archetype": archetype}

    if archetype == "fullstack":
        return {"layers": infer_fullstack_layers(files), "archetype": archetype}

    return {"layers": {"unknown": files}, "archetype": archetype}