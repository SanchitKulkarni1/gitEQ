# app/analysis/python_extractor.py
import ast
from typing import List
from app.analysis.symbols import SymbolRecord


def extract_python_symbols(code: str, path: str) -> List[SymbolRecord]:
    tree = ast.parse(code)
    symbols: List[SymbolRecord] = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for n in node.names:
                symbols.append(SymbolRecord(
                    name=n.name,
                    kind="import",
                    file=path,
                    language="python",
                ))

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                symbols.append(SymbolRecord(
                    name=node.module,
                    kind="import",
                    file=path,
                    language="python",
                ))

        elif isinstance(node, ast.ClassDef):
            symbols.append(SymbolRecord(
                name=node.name,
                kind="class",
                file=path,
                language="python",
            ))

        elif isinstance(node, ast.FunctionDef):
            symbols.append(SymbolRecord(
                name=node.name,
                kind="function",
                file=path,
                language="python",
            ))

    return symbols
