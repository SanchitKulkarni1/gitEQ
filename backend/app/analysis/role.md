# Analysis Module

This module is responsible for **analyzing repository code** to understand its structure, architecture, and dependencies. It extracts meaningful information from source code files to enable documentation generation and chatbot responses in gitEQ.

---

## File Roles

### `symbols.py`
**Data Model for Code Symbols**  
Defines the `SymbolRecord` Pydantic model that represents code entities (classes, functions, imports, etc.) extracted from source files. Acts as the core data structure used throughout the analysis pipeline.

---

### `ast_dispatcher.py`
**Language Router for Symbol Extraction**  
Routes files to the appropriate language-specific extractor based on file extension. Dispatches `.py` files to the Python extractor and `.ts/.tsx/.js/.jsx` files to the TypeScript extractor.

---

### `python_extractor.py`
**Python AST Parser**  
Uses Python's built-in `ast` module to parse Python source code and extract symbols (imports, classes, functions). Returns a list of `SymbolRecord` objects.

---

### `js_ts_extractor.py`
**TypeScript/JavaScript Parser**  
Uses `tree-sitter` to parse TypeScript and JavaScript code, extracting imports, classes, and functions. Supports `.ts`, `.tsx`, `.js`, and `.jsx` files.

---

### `dependency_graph.py`
**Import Dependency Builder**  
Constructs a dependency graph from extracted symbols by mapping each file to its imports. Creates a dict of `{file: [imported_modules]}`.

---

### `graph_metrics.py`
**Graph Analysis Metrics**  
Computes structural metrics from the dependency graph:
- **fan_in**: how many files import a given module
- **fan_out**: how many modules a file imports
- **hubs**: most imported modules
- **leaves**: files with no incoming dependencies

---

### `archetype_detection.py`
**Project Type Classifier**  
Determines the repository archetype (`frontend`, `backend`, `fullstack`, or `unknown`) based on file extensions and import patterns (e.g., React imports → frontend, FastAPI/Flask imports → backend).

---

### `layer_inference.py`
**Architectural Layer Classifier**  
Categorizes files into architectural layers based on path patterns:
- **Frontend layers**: `ui`, `hooks`, `pages`, `utils`
- **Backend layers**: `api`, `services`, `models`, `db`, `utils`

---

### `architecture_hypotheses.py`
**Architecture Pattern Detector**  
Generates high-level hypotheses about the codebase architecture (e.g., "Component-centric SPA", "Layered backend service") with confidence scores and supporting evidence.

---

### `assumption_inference.py`
**Implicit Assumption Detector**  
Infers hidden assumptions about the codebase, such as:
- "Backend logic is external to this repository"
- "UI components act as architectural hubs"

Provides impact analysis for each assumption.