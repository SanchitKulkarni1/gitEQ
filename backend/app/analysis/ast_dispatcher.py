# app/analysis/ast_dispatcher.py
from app.analysis.python_extractor import extract_python_symbols
from app.analysis.js_ts_extractor import extract_ts_symbols


def extract_symbols(path: str, content: str):
    if path.endswith(".py"):
        return extract_python_symbols(content, path)

    if path.endswith((".ts", ".tsx", ".js", ".jsx")):
        return extract_ts_symbols(content, path)

    return []
