# app/analysis/js_ts_extractor.py
from tree_sitter_languages import get_parser
from app.analysis.symbols import SymbolRecord


parser = get_parser("typescript")


def extract_ts_symbols(code: str, path: str):
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node
    symbols = []

    def walk(node):
        # 1. IMPORTS: Extract the actual SOURCE path (e.g., './utils')
        if node.type == "import_statement":
            source_node = node.child_by_field_name("source")
            if source_node:
                # Remove quotes from the string (e.g., "'./utils'" -> "./utils")
                import_path = source_node.text.decode().strip("\"'")
                symbols.append(SymbolRecord(
                    name=import_path,
                    kind="import",
                    file=path,
                    language="typescript",
                ))

        # 2. CLASSES: Standard class definitions
        elif node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                symbols.append(SymbolRecord(
                    name=name_node.text.decode(),
                    kind="class",
                    file=path,
                    language="typescript",
                ))

        # 3. FUNCTIONS: Standard named functions
        elif node.type in ("function_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                symbols.append(SymbolRecord(
                    name=name_node.text.decode(),
                    kind="function",
                    file=path,
                    language="typescript",
                ))

        # 4. VARIABLES: Catches React Components (const Button = () => ...)
        elif node.type == "variable_declarator":
            name_node = node.child_by_field_name("name")
            value_node = node.child_by_field_name("value")

            if name_node and value_node:
                # Check if the value is a function (Arrow Function or Expression)
                # Also handles wrappers like React.memo(...) or forwardRef(...)
                is_function = value_node.type in ("arrow_function", "function_expression")
                is_wrapper = value_node.type == "call_expression" # e.g. React.memo(...)

                if is_function or is_wrapper:
                    symbols.append(SymbolRecord(
                        name=name_node.text.decode(),
                        kind="function", # We treat components as functions
                        file=path,
                        language="typescript",
                    ))

        for c in node.children:
            walk(c)

    walk(root)
    return symbols