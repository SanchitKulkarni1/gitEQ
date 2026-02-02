# app/analysis/architecture_hypotheses.py

def infer_architecture_style(state):
    """
    Infer architectural patterns and styles with confidence scores.
    Detects 15+ patterns across frontend, backend, full-stack, and modern architectures.
    """
    layers = state.layers
    metrics = state.graph_metrics
    archetype = state.archetype
    files = getattr(state, 'files', [])

    hypotheses = []

    # ---------------------------
    # FRONTEND ARCHITECTURE PATTERNS
    # ---------------------------
    if archetype in ["frontend", "fullstack"]:
        _detect_frontend_patterns(hypotheses, layers, metrics, files)

    # ---------------------------
    # BACKEND ARCHITECTURE PATTERNS
    # ---------------------------
    if archetype in ["backend", "fullstack"]:
        _detect_backend_patterns(hypotheses, layers, metrics, files)

    # ---------------------------
    # FULL-STACK PATTERNS
    # ---------------------------
    if archetype == "fullstack":
        _detect_fullstack_patterns(hypotheses, layers, metrics, files)

    # ---------------------------
    # COUPLING & STRUCTURAL PATTERNS
    # ---------------------------
    _detect_coupling_patterns(hypotheses, layers, metrics, archetype)

    # ---------------------------
    # MODERN ARCHITECTURE PATTERNS
    # ---------------------------
    _detect_modern_patterns(hypotheses, layers, files)

    return hypotheses


# ---------------------------
# Frontend Pattern Detection
# ---------------------------

def _detect_frontend_patterns(hypotheses, layers, metrics, files):
    """Detect frontend architecture patterns"""
    ui_files = layers.get("ui", [])
    
    # Pattern 1: Component-centric SPA
    if len(ui_files) > 20:
        hypotheses.append({
            "claim": "Component-centric frontend SPA",
            "confidence": 0.85,
            "pattern_type": "Frontend Architecture",
            "evidence": {
                "ui_components": len(ui_files),
                "dependency_hubs": metrics.get("hubs", [])[:3],
            },
            "characteristics": [
                "Heavy component composition",
                "Modular UI structure",
                "Client-side rendering focus",
            ],
        })
    
    # Pattern 2: Atomic Design Pattern
    atomic_layers = _detect_atomic_design(ui_files)
    if atomic_layers["detected"]:
        hypotheses.append({
            "claim": "Atomic Design methodology",
            "confidence": 0.8,
            "pattern_type": "Component Organization",
            "evidence": {
                "atoms": len(atomic_layers["atoms"]),
                "molecules": len(atomic_layers["molecules"]),
                "organisms": len(atomic_layers["organisms"]),
                "templates": len(atomic_layers["templates"]),
                "pages": len(atomic_layers["pages"]),
            },
            "characteristics": [
                "Hierarchical component structure",
                "Reusable component library",
                "Design system approach",
            ],
        })
    
    # Pattern 3: Hooks-based React Architecture
    if _detect_hooks_pattern(files):
        hypotheses.append({
            "claim": "Hooks-based React architecture",
            "confidence": 0.85,
            "pattern_type": "Component Pattern",
            "evidence": {
                "custom_hooks_detected": True,
                "functional_components": "Primary pattern",
            },
            "characteristics": [
                "Functional programming approach",
                "Custom hooks for logic reuse",
                "Minimal class components",
            ],
        })
    
    # Pattern 4: Feature-based structure
    if _detect_feature_structure(layers, files):
        hypotheses.append({
            "claim": "Feature-based (vertical slice) architecture",
            "confidence": 0.75,
            "pattern_type": "Code Organization",
            "evidence": {
                "feature_folders": "Detected",
                "colocation": "Components with logic and styles",
            },
            "characteristics": [
                "Features self-contained",
                "Reduces coupling between features",
                "Easier to scale teams",
            ],
        })


# ---------------------------
# Backend Pattern Detection
# ---------------------------

def _detect_backend_patterns(hypotheses, layers, metrics, files):
    """Detect backend architecture patterns"""
    api_files = layers.get("api", [])
    service_files = layers.get("services", [])
    
    # Pattern 5: Layered Architecture (N-tier)
    if api_files and service_files:
        hypotheses.append({
            "claim": "Layered backend service (N-tier: API → Services → Data)",
            "confidence": 0.8,
            "pattern_type": "Backend Architecture",
            "evidence": {
                "api_layers": len(api_files),
                "service_layers": len(service_files),
                "separation_of_concerns": "Clear layer boundaries",
            },
            "characteristics": [
                "Horizontal layer separation",
                "Dependency flow from top to bottom",
                "Business logic in service layer",
            ],
        })
    
    # Pattern 6: MVC Pattern
    mvc_evidence = _detect_mvc_pattern(layers, files)
    if mvc_evidence["detected"]:
        hypotheses.append({
            "claim": "Model-View-Controller (MVC) pattern",
            "confidence": 0.8,
            "pattern_type": "Backend Architecture",
            "evidence": {
                "models": len(mvc_evidence["models"]),
                "views": len(mvc_evidence["views"]),
                "controllers": len(mvc_evidence["controllers"]),
            },
            "characteristics": [
                "Clear separation of data, UI, and logic",
                "Traditional web framework pattern",
                "Request-response oriented",
            ],
        })
    
    # Pattern 7: Repository Pattern
    if _detect_repository_pattern(files, layers):
        hypotheses.append({
            "claim": "Repository pattern for data access",
            "confidence": 0.75,
            "pattern_type": "Data Access Pattern",
            "evidence": {
                "repository_files": "Detected",
                "data_abstraction": "Present",
            },
            "characteristics": [
                "Abstraction over data layer",
                "Testable data access",
                "Decoupled from ORM specifics",
            ],
        })
    
    # Pattern 8: Service-oriented Architecture (SOA)
    if len(service_files) > 10 and _detect_service_boundaries(service_files):
        hypotheses.append({
            "claim": "Service-oriented architecture (SOA)",
            "confidence": 0.7,
            "pattern_type": "Backend Architecture",
            "evidence": {
                "service_count": len(service_files),
                "service_boundaries": "Well-defined",
            },
            "characteristics": [
                "Business capability organization",
                "Service isolation",
                "Potentially microservices-ready",
            ],
        })
    
    # Pattern 9: CQRS Pattern
    if _detect_cqrs_pattern(files, layers):
        hypotheses.append({
            "claim": "Command Query Responsibility Segregation (CQRS)",
            "confidence": 0.7,
            "pattern_type": "Backend Pattern",
            "evidence": {
                "command_handlers": "Detected",
                "query_handlers": "Detected",
                "separation": "Read/Write models separated",
            },
            "characteristics": [
                "Separate read and write models",
                "Optimized query paths",
                "Event-driven potential",
            ],
        })


# ---------------------------
# Full-stack Pattern Detection
# ---------------------------

def _detect_fullstack_patterns(hypotheses, layers, metrics, files):
    """Detect full-stack architecture patterns"""
    frontend = layers.get("frontend", {})
    backend = layers.get("backend", {})

    # Pattern 10: Separated Frontend/Backend
    if frontend and backend:
        hypotheses.append({
            "claim": "Full-stack system with separated frontend and backend",
            "confidence": 0.8,
            "pattern_type": "Full-stack Architecture",
            "evidence": {
                "frontend_layers": list(frontend.keys()),
                "backend_layers": list(backend.keys()),
                "api_gateway": "Likely REST or GraphQL",
            },
            "characteristics": [
                "Independent deployment possible",
                "Clear API contract",
                "Technology flexibility",
            ],
        })
    
    # Pattern 11: Monorepo Structure
    if _detect_monorepo(files):
        hypotheses.append({
            "claim": "Monorepo architecture",
            "confidence": 0.85,
            "pattern_type": "Code Organization",
            "evidence": {
                "workspace_config": "Detected",
                "shared_packages": "Present",
            },
            "characteristics": [
                "Unified versioning",
                "Shared tooling and dependencies",
                "Cross-project refactoring ease",
            ],
        })
    
    # Pattern 12: Backend-for-Frontend (BFF)
    if _detect_bff_pattern(layers, files):
        hypotheses.append({
            "claim": "Backend-for-Frontend (BFF) pattern",
            "confidence": 0.7,
            "pattern_type": "Full-stack Pattern",
            "evidence": {
                "client_specific_apis": "Detected",
                "aggregation_layer": "Present",
            },
            "characteristics": [
                "Client-optimized API endpoints",
                "Reduces over-fetching",
                "Frontend-driven backend design",
            ],
        })


# ---------------------------
# Coupling & Structural Patterns
# ---------------------------

def _detect_coupling_patterns(hypotheses, layers, metrics, archetype):
    """Detect coupling and structural anti-patterns"""
    
    # Pattern 13: Hub-and-Spoke (Centralized Dependencies)
    if metrics.get("hubs"):
        hub_count = len([h for h in metrics.get("hubs", []) if metrics.get("fan_in", {}).get(h, 0) > 8])
        if hub_count > 0:
            hypotheses.append({
                "claim": "Hub-and-spoke dependency pattern",
                "confidence": 0.85,
                "pattern_type": "Coupling Pattern",
                "evidence": {
                    "hub_modules": hub_count,
                    "high_centrality_files": metrics.get("hubs", [])[:3],
                },
                "characteristics": [
                    "Central modules with high fan-in",
                    "Risk of bottlenecks",
                    "Changes have wide impact",
                ],
                "warning": "⚠️ High coupling risk - consider refactoring hubs",
            })
    
    # Pattern 14: God Object/Module Anti-pattern
    god_modules = _detect_god_modules(layers, metrics)
    if god_modules:
        hypotheses.append({
            "claim": "God object/module anti-pattern detected",
            "confidence": 0.8,
            "pattern_type": "Anti-pattern",
            "evidence": {
                "god_modules": god_modules[:3],
                "responsibilities": "Too many concerns in single module",
            },
            "characteristics": [
                "Modules doing too much",
                "Low cohesion",
                "Difficult to maintain and test",
            ],
            "warning": "⚠️ CRITICAL: Refactor god modules to improve maintainability",
        })
    
    # Pattern 15: Circular Dependencies
    if _detect_circular_dependencies(metrics):
        hypotheses.append({
            "claim": "Circular dependency pattern detected",
            "confidence": 0.75,
            "pattern_type": "Anti-pattern",
            "evidence": {
                "circular_refs": "Detected in dependency graph",
            },
            "characteristics": [
                "Modules depend on each other",
                "Tight coupling",
                "Difficult to test in isolation",
            ],
            "warning": "⚠️ Break circular dependencies for better modularity",
        })


# ---------------------------
# Modern Architecture Patterns
# ---------------------------

def _detect_modern_patterns(hypotheses, layers, files):
    """Detect modern and emerging architecture patterns"""
    
    file_str = ' '.join(str(f).lower() for f in files)
    
    # Pattern 16: JAMstack Architecture
    if _detect_jamstack(files):
        hypotheses.append({
            "claim": "JAMstack architecture",
            "confidence": 0.8,
            "pattern_type": "Modern Architecture",
            "evidence": {
                "static_generation": "Detected",
                "api_integration": "Client-side or serverless",
                "cdn_optimized": "Likely",
            },
            "characteristics": [
                "Pre-rendered static files",
                "API-driven dynamic content",
                "High performance and scalability",
            ],
        })
    
    # Pattern 17: Serverless Architecture
    if _detect_serverless(files):
        hypotheses.append({
            "claim": "Serverless architecture (FaaS)",
            "confidence": 0.75,
            "pattern_type": "Modern Architecture",
            "evidence": {
                "lambda_functions": "Detected",
                "event_driven": "Likely",
            },
            "characteristics": [
                "Function-based deployment",
                "Event-driven execution",
                "Auto-scaling",
            ],
        })
    
    # Pattern 18: Micro-frontends
    if _detect_micro_frontends(files, layers):
        hypotheses.append({
            "claim": "Micro-frontend architecture",
            "confidence": 0.7,
            "pattern_type": "Modern Frontend",
            "evidence": {
                "independent_apps": "Multiple entry points detected",
                "module_federation": "Possible",
            },
            "characteristics": [
                "Independently deployable UIs",
                "Team autonomy",
                "Technology diversity possible",
            ],
        })
    
    # Pattern 19: Event-Driven Architecture
    if _detect_event_driven(files):
        hypotheses.append({
            "claim": "Event-driven architecture",
            "confidence": 0.75,
            "pattern_type": "Modern Architecture",
            "evidence": {
                "event_handlers": "Detected",
                "message_queue": "Likely present",
            },
            "characteristics": [
                "Asynchronous communication",
                "Loose coupling",
                "Scalable and resilient",
            ],
        })
    
    # Pattern 20: GraphQL API Architecture
    if 'graphql' in file_str:
        hypotheses.append({
            "claim": "GraphQL API architecture",
            "confidence": 0.9,
            "pattern_type": "API Pattern",
            "evidence": {
                "graphql_files": "Detected",
                "schema_definition": "Likely present",
            },
            "characteristics": [
                "Flexible data querying",
                "Single endpoint",
                "Type-safe API",
            ],
        })


# ---------------------------
# Helper Detection Functions
# ---------------------------

def _detect_atomic_design(ui_files):
    """Detect Atomic Design methodology"""
    evidence = {
        "detected": False,
        "atoms": [],
        "molecules": [],
        "organisms": [],
        "templates": [],
        "pages": [],
    }
    
    for f in ui_files:
        f_str = str(f).lower()
        if 'atom' in f_str:
            evidence["atoms"].append(f)
        elif 'molecule' in f_str:
            evidence["molecules"].append(f)
        elif 'organism' in f_str:
            evidence["organisms"].append(f)
        elif 'template' in f_str:
            evidence["templates"].append(f)
        elif 'page' in f_str:
            evidence["pages"].append(f)
    
    # Detected if at least 3 levels present
    levels_present = sum([
        len(evidence["atoms"]) > 0,
        len(evidence["molecules"]) > 0,
        len(evidence["organisms"]) > 0,
        len(evidence["templates"]) > 0,
        len(evidence["pages"]) > 0,
    ])
    
    evidence["detected"] = levels_present >= 3
    return evidence


def _detect_hooks_pattern(files):
    """Detect React Hooks usage"""
    file_str = ' '.join(str(f).lower() for f in files)
    return 'usehook' in file_str or 'hook' in file_str and 'react' in file_str


def _detect_feature_structure(layers, files):
    """Detect feature-based folder structure"""
    file_str = ' '.join(str(f).lower() for f in files)
    return 'features/' in file_str or 'feature/' in file_str


def _detect_mvc_pattern(layers, files):
    """Detect MVC pattern"""
    evidence = {
        "detected": False,
        "models": [],
        "views": [],
        "controllers": [],
    }
    
    for f in files:
        f_str = str(f).lower()
        if 'model' in f_str:
            evidence["models"].append(f)
        if 'view' in f_str:
            evidence["views"].append(f)
        if 'controller' in f_str:
            evidence["controllers"].append(f)
    
    evidence["detected"] = all([
        len(evidence["models"]) > 0,
        len(evidence["controllers"]) > 0,
    ])
    
    return evidence


def _detect_repository_pattern(files, layers):
    """Detect Repository pattern"""
    file_str = ' '.join(str(f).lower() for f in files)
    return 'repository' in file_str or 'repo' in file_str


def _detect_service_boundaries(service_files):
    """Detect well-defined service boundaries"""
    # Services are well-bounded if they're in separate folders/modules
    service_dirs = set()
    for f in service_files:
        parts = str(f).split('/')
        if len(parts) > 1:
            service_dirs.add(parts[-2])
    
    return len(service_dirs) > 3


def _detect_cqrs_pattern(files, layers):
    """Detect CQRS pattern"""
    file_str = ' '.join(str(f).lower() for f in files)
    has_commands = 'command' in file_str
    has_queries = 'query' in file_str or 'queries' in file_str
    return has_commands and has_queries


def _detect_monorepo(files):
    """Detect monorepo structure"""
    file_str = ' '.join(str(f).lower() for f in files)
    return (
        'lerna.json' in file_str or
        'pnpm-workspace' in file_str or
        'workspace' in file_str and 'package.json' in file_str or
        'nx.json' in file_str
    )


def _detect_bff_pattern(layers, files):
    """Detect Backend-for-Frontend pattern"""
    api_files = layers.get("api", [])
    # BFF indicated by multiple API versions or client-specific endpoints
    file_str = ' '.join(str(f).lower() for f in api_files)
    return 'mobile' in file_str and 'web' in file_str or 'v1' in file_str and 'v2' in file_str


def _detect_god_modules(layers, metrics):
    """Detect god modules (too many responsibilities)"""
    god_modules = []
    
    # A god module has high fan-in AND high fan-out
    for file in metrics.get("hubs", []):
        fan_in = metrics.get("fan_in", {}).get(file, 0)
        fan_out = metrics.get("fan_out", {}).get(file, 0)
        
        if fan_in > 10 and fan_out > 10:
            god_modules.append(file)
    
    return god_modules


def _detect_circular_dependencies(metrics):
    """Detect circular dependencies"""
    # This is a simplified check - real implementation would need graph analysis
    return metrics.get("circular_dependencies", False)


def _detect_jamstack(files):
    """Detect JAMstack architecture"""
    file_str = ' '.join(str(f).lower() for f in files)
    return (
        'next.js' in file_str or 'gatsby' in file_str or
        'nuxt' in file_str or '11ty' in file_str or
        'static' in file_str and 'generate' in file_str
    )


def _detect_serverless(files):
    """Detect serverless architecture"""
    file_str = ' '.join(str(f).lower() for f in files)
    return (
        'lambda' in file_str or 'serverless' in file_str or
        'function' in file_str and ('aws' in file_str or 'azure' in file_str or 'gcp' in file_str)
    )


def _detect_micro_frontends(files, layers):
    """Detect micro-frontend architecture"""
    file_str = ' '.join(str(f).lower() for f in files)
    return (
        'module-federation' in file_str or
        'single-spa' in file_str or
        len([f for f in files if 'main' in str(f).lower() or 'entry' in str(f).lower()]) > 2
    )


def _detect_event_driven(files):
    """Detect event-driven architecture"""
    file_str = ' '.join(str(f).lower() for f in files)
    return (
        'event' in file_str and ('handler' in file_str or 'bus' in file_str) or
        'kafka' in file_str or 'rabbitmq' in file_str or
        'message' in file_str and 'queue' in file_str
    )