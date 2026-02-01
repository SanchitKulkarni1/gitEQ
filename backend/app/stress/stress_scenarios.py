# app/stress/stress_scenarios.py
from app.stress.stress_models import StressVector, ArchitectureType


PRESET_STRESS_SCENARIOS = {
    # ========== FRONTEND / SPA SCENARIOS ==========
    "concurrent_users_spa": StressVector(
        name="concurrent_users_spa",
        description="5000+ concurrent users on static SPA",
        target_layers=["hosting", "cdn", "assets"],
        severity=0.3,  # Low severity for static sites
        propagation_type="traffic",
        architecture_types=[ArchitectureType.STATIC_SPA],
    ),

    "bundle_size_bloat": StressVector(
        name="bundle_size_bloat",
        description="Large JavaScript bundle causing slow initial load",
        target_layers=["components", "ui", "lib"],
        severity=0.7,
        propagation_type="dependency",
        architecture_types=[ArchitectureType.STATIC_SPA, ArchitectureType.SSR_APP],
    ),

    "memory_leak_client": StressVector(
        name="memory_leak_client",
        description="Client-side memory leaks from state management",
        target_layers=["hooks", "context", "store"],
        severity=0.8,
        propagation_type="dependency",
        architecture_types=[ArchitectureType.STATIC_SPA, ArchitectureType.SSR_APP],
    ),

    # ========== SSR / HYBRID SCENARIOS ==========
    "ssr_concurrent_load": StressVector(
        name="ssr_concurrent_load",
        description="5000+ concurrent users on SSR application",
        target_layers=["pages", "api", "server"],
        severity=0.9,  # High severity for SSR
        propagation_type="traffic",
        architecture_types=[ArchitectureType.SSR_APP, ArchitectureType.FULL_STACK],
    ),

    "api_route_overload": StressVector(
        name="api_route_overload",
        description="API routes receiving high request volume",
        target_layers=["api", "routes", "endpoints"],
        severity=0.85,
        propagation_type="traffic",
        architecture_types=[ArchitectureType.SSR_APP, ArchitectureType.BACKEND_API, ArchitectureType.FULL_STACK],
    ),

    # ========== BACKEND SCENARIOS ==========
    "database_connection_exhaustion": StressVector(
        name="database_connection_exhaustion",
        description="Database connection pool exhausted under load",
        target_layers=["database", "models", "repositories"],
        severity=0.95,
        propagation_type="data",
        architecture_types=[ArchitectureType.BACKEND_API, ArchitectureType.FULL_STACK],
    ),

    "n_plus_one_queries": StressVector(
        name="n_plus_one_queries",
        description="N+1 query problem causing database overload",
        target_layers=["models", "queries", "resolvers"],
        severity=0.9,
        propagation_type="data",
        architecture_types=[ArchitectureType.BACKEND_API, ArchitectureType.FULL_STACK],
    ),

    # ========== UNIVERSAL SCENARIOS ==========
    "external_api_instability": StressVector(
        name="external_api_instability",
        description="External APIs become unreliable or rate-limited",
        target_layers=["api", "services", "integrations"],
        severity=0.75,
        propagation_type="dependency",
        architecture_types=[
            ArchitectureType.STATIC_SPA,
            ArchitectureType.SSR_APP,
            ArchitectureType.BACKEND_API,
            ArchitectureType.FULL_STACK,
        ],
    ),

    "authentication_bottleneck": StressVector(
        name="authentication_bottleneck",
        description="Authentication service under heavy load",
        target_layers=["auth", "middleware", "guards"],
        severity=0.85,
        propagation_type="auth",
        architecture_types=[
            ArchitectureType.SSR_APP,
            ArchitectureType.BACKEND_API,
            ArchitectureType.FULL_STACK,
        ],
    ),

    "team_scale_conflicts": StressVector(
        name="team_scale_conflicts",
        description="Multiple teams causing merge conflicts and coupling",
        target_layers=["utils", "services", "shared"],
        severity=0.6,
        propagation_type="dependency",
        architecture_types=[
            ArchitectureType.STATIC_SPA,
            ArchitectureType.SSR_APP,
            ArchitectureType.BACKEND_API,
            ArchitectureType.FULL_STACK,
            ArchitectureType.MONOREPO,
        ],
    ),

    # ========== FORM / USER INPUT SCENARIOS ==========
    "form_submission_spike": StressVector(
        name="form_submission_spike",
        description="Sudden spike in form submissions (contact, signup, etc.)",
        target_layers=["forms", "api", "validation"],
        severity=0.8,
        propagation_type="traffic",
        architecture_types=[ArchitectureType.SSR_APP, ArchitectureType.FULL_STACK],
    ),

    # ========== DEPLOYMENT SCENARIOS ==========
    "cold_start_latency": StressVector(
        name="cold_start_latency",
        description="Serverless functions experiencing cold starts",
        target_layers=["api", "functions", "lambda"],
        severity=0.7,
        propagation_type="traffic",
        architecture_types=[ArchitectureType.SSR_APP, ArchitectureType.BACKEND_API],
    ),
}


def get_applicable_scenarios(architecture_type: ArchitectureType) -> dict:
    """
    Returns only stress scenarios applicable to the detected architecture.
    """
    return {
        name: scenario
        for name, scenario in PRESET_STRESS_SCENARIOS.items()
        if architecture_type in scenario.architecture_types
        or ArchitectureType.UNKNOWN in scenario.architecture_types
    }