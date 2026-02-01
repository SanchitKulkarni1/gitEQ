# app/stress/evidence_mapper.py
from typing import List, Dict
from app.stress.stress_models import BottleneckAnalysis


def map_evidence(layers: dict, impacted_files: list, architecture_type: str, tech_stack) -> List[Dict]:
    """
    Map impacted files to layers and provide evidence for stress analysis.
    
    Args:
        layers: Dictionary mapping layer names to files
        impacted_files: List of files impacted by stress
        architecture_type: Detected architecture type
        tech_stack: Detected tech stack
    
    Returns:
        List of evidence dictionaries
    """
    evidence = []

    for layer, files in layers.items():
        for f in files:
            if f in impacted_files:
                evidence.append({
                    "file": f,
                    "layer": layer,
                    "reason": _determine_impact_reason(f, layer, architecture_type),
                    "severity": _calculate_severity(f, layer, impacted_files),
                })

    return evidence


def identify_bottlenecks(
    impacted_files: List[str],
    dep_graph: dict,
    architecture_type: str,
    tech_stack,
    stress_type: str
) -> List[BottleneckAnalysis]:
    """
    Identify specific bottlenecks from impacted files.
    
    Returns:
        List of BottleneckAnalysis objects with detailed recommendations
    """
    bottlenecks = []

    # Analyze each impacted file for bottlenecks
    for file in impacted_files[:10]:  # Focus on most impacted
        bottleneck = _analyze_file_bottleneck(
            file, dep_graph, architecture_type, tech_stack, stress_type
        )
        if bottleneck:
            bottlenecks.append(bottleneck)

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    bottlenecks.sort(key=lambda x: severity_order[x.severity])

    return bottlenecks


def _analyze_file_bottleneck(
    file: str,
    dep_graph: dict,
    architecture_type: str,
    tech_stack,
    stress_type: str
) -> BottleneckAnalysis:
    """Analyze a single file for bottlenecks"""

    # Count how many files depend on this one
    dependents = [k for k, v in dep_graph.items() if file in v]
    dependent_count = len(dependents)

    # API Route bottlenecks
    if "api/" in file or "/routes/" in file or "/endpoints/" in file:
        if stress_type in ["concurrent_users_spa", "ssr_concurrent_load", "api_route_overload"]:
            return BottleneckAnalysis(
                component=file,
                reason=f"API endpoint handling concurrent requests without rate limiting or caching",
                severity="critical" if dependent_count > 5 else "high",
                recommendation="Implement rate limiting, add caching layer (Redis), use connection pooling",
                file_path=file,
            )

    # Database/Model bottlenecks
    if any(keyword in file.lower() for keyword in ["model", "database", "db", "prisma", "repository"]):
        if stress_type in ["database_connection_exhaustion", "n_plus_one_queries"]:
            return BottleneckAnalysis(
                component=file,
                reason="Database queries without connection pooling or query optimization",
                severity="critical",
                recommendation="Add connection pooling, implement query caching, use read replicas, fix N+1 queries",
                file_path=file,
            )

    # Component bundle size
    if file.endswith((".tsx", ".jsx")) and dependent_count > 10:
        if stress_type == "bundle_size_bloat":
            return BottleneckAnalysis(
                component=file,
                reason=f"Shared component used by {dependent_count} files, contributing to bundle size",
                severity="medium",
                recommendation="Implement code splitting, lazy loading, or tree shaking for this component",
                file_path=file,
            )

    # State management bottlenecks
    if any(keyword in file.lower() for keyword in ["context", "store", "state", "reducer"]):
        if stress_type == "memory_leak_client":
            return BottleneckAnalysis(
                component=file,
                reason="Global state management could cause memory leaks if not properly cleaned",
                severity="medium",
                recommendation="Audit useEffect cleanup functions, implement proper unmount logic",
                file_path=file,
            )

    # Authentication bottlenecks
    if any(keyword in file.lower() for keyword in ["auth", "login", "session", "jwt"]):
        if stress_type == "authentication_bottleneck":
            return BottleneckAnalysis(
                component=file,
                reason="Authentication logic without proper caching or session management",
                severity="high",
                recommendation="Implement JWT with refresh tokens, use session caching, add rate limiting",
                file_path=file,
            )

    # Form submission bottlenecks
    if "form" in file.lower() or "contact" in file.lower():
        if stress_type == "form_submission_spike":
            return BottleneckAnalysis(
                component=file,
                reason="Form submission without rate limiting or queue system",
                severity="high",
                recommendation="Add rate limiting, implement queue system (Bull/BullMQ), add CAPTCHA",
                file_path=file,
            )

    # Generic high-dependency component
    if dependent_count > 15:
        return BottleneckAnalysis(
            component=file,
            reason=f"Highly coupled component with {dependent_count} dependents - single point of failure",
            severity="medium",
            recommendation="Refactor to reduce coupling, implement circuit breaker pattern",
            file_path=file,
        )

    return None


def _determine_impact_reason(file: str, layer: str, architecture_type: str) -> str:
    """Determine why a file is impacted by stress"""
    
    if architecture_type == "static_spa":
        if file.endswith((".tsx", ".jsx")):
            return "Client-side component - no server load impact"
        if "api" in file.lower():
            return "API call - potential rate limiting needed"
    
    elif architecture_type == "ssr_app":
        if file.endswith((".tsx", ".jsx")):
            return "SSR component - server CPU and memory impact"
        if "api/" in file:
            return "API route - concurrent request handling needed"
    
    elif architecture_type == "backend_api":
        if "route" in file.lower() or "controller" in file.lower():
            return "Request handler - direct traffic impact"
        if "model" in file.lower() or "db" in file.lower():
            return "Database layer - connection pool impact"

    return "Affected by stress propagation"


def _calculate_severity(file: str, layer: str, all_impacted: list) -> str:
    """Calculate severity of impact on this file"""
    
    # Critical if in top 5 impacted files
    if all_impacted.index(file) < 5:
        return "critical"
    
    # High if API, database, or auth related
    critical_keywords = ["api/", "database", "auth", "server"]
    if any(keyword in file.lower() for keyword in critical_keywords):
        return "high"
    
    # Medium for shared components
    if "component" in file.lower() or "util" in file.lower():
        return "medium"
    
    return "low"


def generate_safe_components_list(
    all_files: List[str],
    impacted_files: List[str],
    architecture_type: str
) -> List[str]:
    """
    Generate list of components that are safe under stress.
    
    Args:
        all_files: All files in the repository
        impacted_files: Files impacted by stress test
        architecture_type: Detected architecture type
    
    Returns:
        List of safe component descriptions
    """
    safe = []

    # For static SPAs, client components are generally safe
    if architecture_type == "static_spa":
        client_components = [f for f in all_files if f.endswith((".tsx", ".jsx"))]
        non_impacted = [f for f in client_components if f not in impacted_files]
        
        if len(non_impacted) > 0:
            safe.append(f"{len(non_impacted)} client-side React components (run in browser, no server load)")
        
        safe.append("Static assets (cached by CDN, infinite scalability)")
        safe.append("CSS/styling (no runtime impact)")

    # Cached assets are always safe
    safe.append("Properly cached API responses (if caching implemented)")
    
    return safe