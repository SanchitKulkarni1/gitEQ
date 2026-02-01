# app/analysis/archetype_detection.py

def detect_archetype(files: list[str], symbols: list) -> str:
    has_ts = any(f.endswith((".ts", ".tsx")) for f in files)
    has_py = any(f.endswith(".py") for f in files)

    imports = [s.name for s in symbols if s.kind == "import"]

    if has_ts and any("react" in i for i in imports):
        return "frontend"

    if has_py and any("fastapi" in i or "flask" in i for i in imports):
        return "backend"

    if has_py and has_ts:
        return "fullstack"

    return "unknown"
