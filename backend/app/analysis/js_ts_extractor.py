# app/analysis/js_ts_extractor.py
from tree_sitter_languages import get_parser
from app.analysis.symbols import SymbolRecord


parser = get_parser("typescript")


def extract_ts_symbols(code: str, path: str):
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node
    symbols = []

    def walk(node):
        if node.type == "import_statement":
            text = code[node.start_byte:node.end_byte]
            symbols.append(SymbolRecord(
                name=text,
                kind="import",
                file=path,
                language="typescript",
            ))

        elif node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                symbols.append(SymbolRecord(
                    name=name_node.text.decode(),
                    kind="class",
                    file=path,
                    language="typescript",
                ))

        elif node.type in ("function_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                symbols.append(SymbolRecord(
                    name=name_node.text.decode(),
                    kind="function",
                    file=path,
                    language="typescript",
                ))

        for c in node.children:
            walk(c)

    walk(root)
    return symbols
