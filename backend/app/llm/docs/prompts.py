# app/prompts/prompts.py
"""
Improved prompt templates for GitEQ documentation generation.
Uses functions instead of module-level f-strings to avoid timing issues.
"""

from typing import List, Dict
from app.models.state import RepoState


# ============================================================================
# BASE RULES
# ============================================================================

BASE_RULES = """You are writing technical documentation for a GitHub repository.

Rules:
- Use ONLY the facts provided
- Do NOT invent components, APIs, or behavior
- If information is missing, say so explicitly
- Avoid best-practice preaching
- Use precise engineering language"""


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_hypotheses(hypotheses: List[Dict]) -> str:
    """Format architecture hypotheses for LLM consumption."""
    if not hypotheses:
        return "No architectural hypotheses generated."
    
    lines = []
    for h in hypotheses:
        pattern = h.get('pattern', 'Unknown')
        confidence = h.get('confidence', 0)
        evidence = h.get('evidence', 'none')
        lines.append(f"- **{pattern}** (confidence: {confidence:.0%})")
        lines.append(f"  Evidence: {evidence}")
    
    return "\n".join(lines)


def format_layers(layers: Dict) -> str:
    """Format layer information for LLM consumption."""
    if not layers:
        return "No layers detected."
    
    result = []
    for layer_name, files in layers.items():
        file_count = len(files)
        sample_files = files[:5]
        
        files_text = "\n    ".join([f"- {f}" for f in sample_files])
        more_text = f"\n    ... and {file_count - 5} more" if file_count > 5 else ""
        
        result.append(f"  {layer_name} ({file_count} files):\n    {files_text}{more_text}")
    
    return "\n".join(result)


def format_metrics(metrics: Dict) -> str:
    """Format graph metrics for LLM consumption."""
    avg_fan_in = metrics.get('avg_fan_in', 0)
    avg_fan_out = metrics.get('avg_fan_out', 0)
    
    return f"""  - Total modules: {metrics.get('total_nodes', 0)}
  - Total dependencies: {metrics.get('total_edges', 0)}
  - Average fan-in: {avg_fan_in:.2f}
  - Average fan-out: {avg_fan_out:.2f}
  - Max fan-in: {metrics.get('max_fan_in', 0)} ({metrics.get('max_fan_in_module', 'unknown')})
  - Top dependency hubs: {', '.join(metrics.get('hubs', [])[:5])}
  - Leaf modules (no dependents): {len(metrics.get('leaves', []))}"""


def format_assumptions(assumptions: List[Dict]) -> str:
    """Format assumptions grouped by risk level."""
    if not assumptions:
        return "No assumptions detected."
    
    high_risk = [a for a in assumptions if a.get('risk_level') == 'high']
    medium_risk = [a for a in assumptions if a.get('risk_level') == 'medium']
    low_risk = [a for a in assumptions if a.get('risk_level') == 'low']
    
    def format_group(items):
        if not items:
            return "  None"
        return "\n".join([
            f"  - {a['assumption']}\n"
            f"    Impact: {a.get('impact', 'unknown')}\n"
            f"    Evidence: {a.get('evidence', 'none')}"
            for a in items
        ])
    
    return f"""
HIGH RISK:
{format_group(high_risk)}

MEDIUM RISK:
{format_group(medium_risk)}

LOW RISK:
{format_group(low_risk)}"""


def format_stress_results(stress_results: List[Dict]) -> str:
    """Format stress test results for detailed analysis."""
    if not stress_results:
        return "No stress test results available."
    
    sections = []
    for result in stress_results:
        scenario = result.get('scenario_name', 'unknown')
        breaking_point = result.get('breaking_point', 'unknown')
        symptoms = result.get('symptoms', [])
        bottlenecks = result.get('bottlenecks', [])
        
        symptoms_text = "\n    ".join([f"- {s}" for s in symptoms]) if symptoms else "None detected"
        bottlenecks_text = "\n    ".join([f"- {b}" for b in bottlenecks]) if bottlenecks else "None detected"
        
        sections.append(f"""
  Scenario: {scenario}
  Breaking Point: {breaking_point}
  
  Symptoms:
    {symptoms_text}
  
  Architectural Bottlenecks:
    {bottlenecks_text}
  
  ---""")
    
    return "\n".join(sections)


# ============================================================================
# PROMPT GENERATORS
# ============================================================================

def get_overview_prompt(state: RepoState) -> str:
    """Generate overview documentation prompt."""
    hypotheses_text = format_hypotheses(state.architecture_hypotheses)
    
    return f"""{BASE_RULES}

REPOSITORY CONTEXT:
- URL: {state.repo_url}
- Owner: {state.owner}
- Repository: {state.repo}
- Default Branch: {state.branch}
- Repository Size: {state.stats.get('repo_size_kb', 'unknown')} KB
- Total Files: {state.stats.get('files_total', 'unknown')}
- Files Analyzed: {state.stats.get('files_selected', 'unknown')}
- Symbols Extracted: {state.stats.get('symbols_extracted', 'unknown')}

ARCHITECTURAL CLASSIFICATION:
- Archetype: {state.archetype}

Architecture Hypotheses:
{hypotheses_text}

TASK:
Write a 2-3 paragraph overview explaining:
1. What problem this repository solves
2. What type of system it is (based on the archetype and hypotheses above)
3. Its intended scope and primary use case

Focus on INTENT and PURPOSE, not implementation details.

OUTPUT FORMAT:
- Start with ## Overview heading
- Use Markdown formatting
- Keep it concise (2-3 paragraphs, ~150-300 words)
- Do not invent features or capabilities not evidenced above"""


def get_architecture_prompt(state: RepoState) -> str:
    """Generate architecture documentation prompt."""
    layers_text = format_layers(state.layers)
    metrics_text = format_metrics(state.graph_metrics)
    
    return f"""{BASE_RULES}

ARCHITECTURAL LAYERS:
{layers_text}

DEPENDENCY METRICS:
{metrics_text}

DEPENDENCY GRAPH INTERPRETATION GUIDE:
- **Hubs**: Most imported modules (high fan-in) - these are core dependencies
- **Fan-in**: Number of modules that import a given module
- **Fan-out**: Number of modules a given module imports
- **Leaves**: Modules nothing depends on - likely UI components or entry points

TASK:
Write a comprehensive architecture section that:
1. Describes the layer structure and what each layer's responsibility is
2. Explains how layers interact (dependency direction, coupling)
3. Identifies architectural patterns visible in the structure (e.g., layered, hexagonal, flat)
4. Highlights any architectural concerns (e.g., high coupling, circular dependencies, god modules)

OUTPUT FORMAT:
- Start with ## Architecture heading
- Use ### subheadings for each major layer
- Include a brief paragraph on layer interactions
- End with a "Architectural Patterns" subsection
- Use Markdown formatting"""


def get_core_modules_prompt(state: RepoState) -> str:
    """Generate core modules documentation prompt."""
    metrics = state.graph_metrics
    hubs = metrics.get('hubs', [])[:10]
    
    # Try to get detailed hub information if available
    hub_details = metrics.get('hub_details', {})
    
    hubs_text = ""
    for hub in hubs:
        if hub in hub_details:
            fan_in = hub_details[hub].get('fan_in', '?')
            fan_out = hub_details[hub].get('fan_out', '?')
            hubs_text += f"\n  - {hub} (imported by {fan_in} modules, imports {fan_out} modules)"
        else:
            hubs_text += f"\n  - {hub}"
    
    return f"""{BASE_RULES}

TOP DEPENDENCY HUBS (Most Imported Modules):
{hubs_text}

CONTEXT:
- Total modules analyzed: {metrics.get('total_nodes', 'unknown')}
- Average fan-in: {metrics.get('avg_fan_in', 0):.2f}
- Average fan-out: {metrics.get('avg_fan_out', 0):.2f}

TASK:
Write a "Core Modules" section that:
1. Lists the 5-7 most critical modules (from the hubs above)
2. Explains WHY each is central (based on import counts and position)
3. Describes the "blast radius" - how many files would be affected if this module's interface changed
4. Identifies potential risks (e.g., single points of failure, god modules, tight coupling)

For each core module, include:
- Module name and location
- Number of dependents (direct change impact)
- Inferred primary responsibility (based on name, layer, and dependencies)
- Risk assessment (high/medium/low based on coupling)

OUTPUT FORMAT:
- Start with ## Core Modules heading
- Use a list or table format for clarity
- Include a summary paragraph about overall modularity
- Use Markdown formatting"""


def get_system_boundaries_prompt(state: RepoState) -> str:
    """Generate system boundaries documentation prompt."""
    assumptions_text = format_assumptions(state.assumptions)
    
    # Detect layer presence
    layer_names = [str(l).lower() for l in state.layers.keys()]
    frontend_layers = [l for l in layer_names if any(x in l for x in ['ui', 'component', 'view', 'page'])]
    backend_layers = [l for l in layer_names if any(x in l for x in ['api', 'service', 'db', 'data', 'model'])]
    
    boundary_hint = ""
    if state.archetype == "fullstack":
        boundary_hint = "This appears to be a fullstack repository containing both frontend and backend code."
    elif state.archetype == "frontend":
        boundary_hint = "This appears to be a frontend-only repository."
    elif state.archetype == "backend":
        boundary_hint = "This appears to be a backend-only repository."
    else:
        boundary_hint = "The system archetype could not be conclusively determined."
    
    return f"""{BASE_RULES}

SYSTEM CLASSIFICATION:
- Archetype: {state.archetype}
- {boundary_hint}

DETECTED LAYERS:
- Frontend layers: {', '.join(frontend_layers) or 'None detected'}
- Backend layers: {', '.join(backend_layers) or 'None detected'}

ARCHITECTURAL ASSUMPTIONS:
{assumptions_text}

TASK:
Write a "System Boundaries" section that:
1. Clearly states what IS included in this repository vs what ISN'T
2. If backend is missing: explain where backend logic likely resides (API, microservices, etc.)
3. If frontend is missing: explain how this system is consumed (REST API, library, CLI tool, etc.)
4. Describes integration points (external APIs, databases, message queues, external services)
5. Identifies responsibilities that are ASSUMED to be handled elsewhere

Base your analysis EXCLUSIVELY on the assumptions and layer information provided above.
Do not speculate about technologies or services not evidenced in the data.

OUTPUT FORMAT:
- Start with ## System Boundaries heading
- Use subheadings: ### What's Included, ### What's External, ### Integration Points
- Be explicit about unknowns
- Use Markdown formatting"""


def get_assumptions_prompt(state: RepoState) -> str:
    """Generate architectural assumptions documentation prompt."""
    assumptions_text = format_assumptions(state.assumptions)
    
    return f"""{BASE_RULES}

ARCHITECTURAL ASSUMPTIONS (grouped by risk level):
{assumptions_text}

TASK:
Write an "Architectural Assumptions" section that:
1. Lists the key assumptions the codebase makes about its environment, infrastructure, or usage
2. Explains WHY each assumption likely exists (infer from architectural context and evidence)
3. Describes WHEN these assumptions become risky or invalid (scaling thresholds, usage patterns, environment changes)
4. Prioritizes by risk level (address high-risk assumptions first with more detail)

For each assumption, structure your explanation as:
- **The Assumption**: State it clearly
- **Why It Exists**: Technical or business rationale (inferred from evidence)
- **When It Breaks**: Specific conditions that invalidate it (user count, data volume, concurrent load, etc.)
- **Potential Impact**: What fails when this assumption is violated

OUTPUT FORMAT:
- Start with ## Architectural Assumptions heading
- Group by risk level (### High Risk, ### Medium Risk, ### Low Risk)
- Use a consistent structure for each assumption
- Include a summary paragraph about overall architectural risk posture
- Use Markdown formatting"""


def get_stress_test_prompt(state: RepoState) -> str:
    """
    Generate stress test analysis documentation prompt.
    
    THIS IS THE DIFFERENTIATING FEATURE - make it count!
    """
    stress_text = format_stress_results(state.stress_results)
    hubs = state.graph_metrics.get('hubs', [])[:5]
    
    return f"""{BASE_RULES}

STRESS TEST RESULTS:
{stress_text}

ARCHITECTURAL CONTEXT:
- Core dependency hubs: {', '.join(hubs)}
- Archetype: {state.archetype}
- Total modules: {state.graph_metrics.get('total_nodes', 'unknown')}

WHAT IS "ARCHITECTURAL FRAGILITY"?
Architectural fragility refers to structural weaknesses in code organization that make the system 
vulnerable under stress. Common patterns include:
- Synchronous bottlenecks (single-threaded operations blocking concurrent requests)
- Shared mutable state (race conditions under concurrent access)
- Deep dependency chains (cascade failures when one component fails)
- Singleton patterns (resource contention at a single point)
- Missing async boundaries (blocking I/O operations)
- Over-coupling to core modules (changes ripple through many files)

TASK:
Write a comprehensive "Stress Test Analysis" section that explains what breaks under load and why.

Your analysis MUST include these sections:

### 1. Breaking Points Summary
For each stress scenario, state:
- WHAT breaks (which component/layer)
- AT WHAT THRESHOLD (specific number: requests/second, concurrent users, data volume)
- IMMEDIATE SYMPTOM (timeout, crash, data corruption)

### 2. Root Cause Analysis
For each breaking point, explain WHY it breaks by linking symptoms to architectural decisions:
- Is it a synchronous operation that should be async?
- Is it a shared resource without proper isolation/pooling?
- Is it a deeply nested dependency chain causing cascades?
- Is it a singleton creating a concurrency bottleneck?
- Is it missing error handling/circuit breakers?

Link each root cause to SPECIFIC modules or layers using the dependency hub information.

Example: "The `UserService` module (a dependency hub imported by 23 modules) likely handles 
authentication synchronously, creating a bottleneck under concurrent load in the API layer."

### 3. Scaling Implications
For each breaking point, predict what happens as load increases:
- What happens if traffic doubles from the breaking point?
- What happens if concurrent users increase 10x?
- What happens during traffic spikes (2x-5x normal load for short bursts)?

### 4. Architectural Recommendations
Suggest STRUCTURAL changes (not implementation details) to address fragility:
- Pattern changes (e.g., "introduce async boundaries between API and database layers")
- Architectural refactoring (e.g., "consider event-driven architecture for notification system")
- Isolation strategies (e.g., "implement connection pooling pattern in data access layer")
- Decoupling suggestions (e.g., "extract caching logic into separate layer to reduce database coupling")

Base recommendations on the actual architectural structure (layers, hubs, dependencies).

OUTPUT REQUIREMENTS:
- Start with ## Stress Test Analysis heading
- Use ### subheadings for each major section
- Include a summary table at the top:
  | Scenario | Breaking Point | Primary Bottleneck | Affected Layer |
- Write in present tense ("the system breaks at..." not "would break...")
- Be specific with numbers from the test results
- Link EVERY bottleneck to actual code structure (layers, modules, dependency hubs)
- Make recommendations actionable and architecture-focused

CRITICAL: This is the DIFFERENTIATING FEATURE of this documentation system.
Make it detailed, specific, actionable, and directly tied to the codebase architecture.
This section should provide value that generic load testing tools cannot.

Use Markdown formatting throughout."""


# ============================================================================
# VALIDATION
# ============================================================================

def validate_state_for_docs(state: RepoState) -> Dict[str, List[str]]:
    """
    Validate that state has necessary data for each documentation section.
    Returns a dict of {section_name: [warnings]}.
    """
    warnings = {}
    
    # Overview validation
    overview_warnings = []
    if not state.archetype:
        overview_warnings.append("No archetype detected - overview will be generic")
    if not state.architecture_hypotheses:
        overview_warnings.append("No architecture hypotheses - overview will lack depth")
    if overview_warnings:
        warnings['overview'] = overview_warnings
    
    # Architecture validation
    arch_warnings = []
    if not state.layers:
        arch_warnings.append("No layers detected - architecture section will be minimal")
    if not state.graph_metrics:
        arch_warnings.append("No graph metrics - cannot analyze dependencies")
    if arch_warnings:
        warnings['architecture'] = arch_warnings
    
    # Core modules validation
    core_warnings = []
    if not state.graph_metrics.get('hubs'):
        core_warnings.append("No dependency hubs found - core modules section will be empty")
    if core_warnings:
        warnings['core_modules'] = core_warnings
    
    # System boundaries validation
    boundaries_warnings = []
    if not state.assumptions:
        boundaries_warnings.append("No assumptions detected - boundaries analysis will be limited")
    if boundaries_warnings:
        warnings['system_boundaries'] = boundaries_warnings
    
    # Stress test validation
    stress_warnings = []
    if not state.stress_results:
        stress_warnings.append("CRITICAL: No stress test results - this is your differentiating feature!")
    if not state.graph_metrics.get('hubs'):
        stress_warnings.append("No dependency hubs - cannot link stress results to architecture")
    if stress_warnings:
        warnings['stress_test'] = stress_warnings
    
    return warnings
