# app/analysis/symbols.py
from typing import List, Literal, Optional
from pydantic import BaseModel


SymbolKind = Literal[
    "module",
    "class",
    "function",
    "method",
    "variable",
    "import"
]


class SymbolRecord(BaseModel):
    name: str
    kind: SymbolKind
    file: str

    # Relationships
    defined_in: Optional[str] = None      # class / module
    imports: List[str] = []               # modules imported
    exports: List[str] = []               # public symbols

    # Metadata
    language: str
