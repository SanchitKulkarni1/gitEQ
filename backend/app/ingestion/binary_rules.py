# app/ingestion/binary_rules.py

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".pdf", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".bin",
    ".woff", ".woff2", ".ttf",
}

def is_binary_path(path: str) -> bool:
    return any(path.lower().endswith(ext) for ext in BINARY_EXTENSIONS)
