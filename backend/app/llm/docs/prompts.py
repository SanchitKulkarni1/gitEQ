# app/llm/docs/prompts.py
"""
Enhanced prompts that leverage ALL the analysis data including rich evidence.
These prompts are designed to produce AUTHORITATIVE, DATA-DRIVEN documentation.
"""

from app.models.state import RepoState
from typing import Dict, List
from app.analysis.graph_metrics import compute_graph_metrics
import json


def get_top_hub(metrics: Dict):
    """
    Safely extract the most critical dependency hub.
    Returns (module_name, fan_in_count) or (None, 0).
    """
    if not metrics:
        return None, 0

    module = metrics.get("max_fan_in_module")
    if not module:
        return None, 0

    hub_details = metrics.get("hub_details", {})
    fan_in = hub_details.get(module, {}).get("fan_in", 0)

    return module, fan_in

# ============================================================================
# ENHANCED FORMATTING HELPERS - Make rich evidence readable for the LLM
# ============================================================================

def format_graph_metrics(metrics: Dict) -> str:
    """Format dependency graph metrics in a readable way."""
    if not metrics:
        return "No dependency metrics available."
    
    hubs = metrics.get('hubs', [])[:10]
    leaves = metrics.get('leaves', [])[:5]
    
    return f"""DEPENDENCY ANALYSIS:
• Total Modules: {metrics.get('total_nodes', 0)}
• Total Dependencies: {metrics.get('total_edges', 0)}
• Average Fan-in: {metrics.get('avg_fan_in', 0):.2f} (how many import each module)
• Average Fan-out: {metrics.get('avg_fan_out', 0):.2f} (how many each module imports)
• Max Fan-in: {metrics.get('max_fan_in', 0)} ({metrics.get('max_fan_in_module', 'unknown')})

TOP DEPENDENCY HUBS (Most Imported):
{chr(10).join([f"  {i+1}. {hub}" for i, hub in enumerate(hubs)])}

LEAF MODULES (Nothing Depends On):
{chr(10).join([f"  • {leaf}" for leaf in leaves])}
"""


def format_layers(layers: Dict) -> str:
    """Format layer information clearly."""
    if not layers:
        return "No architectural layers detected."
    
    result = []
    for layer_name, files in sorted(layers.items(), key=lambda x: len(x[1]), reverse=True):
        file_count = len(files)
        sample_files = files[:5]
        result.append(f"{layer_name.upper()} ({file_count} files):")
        result.append("  " + "\n  ".join([f"• {f}" for f in sample_files]))
        if file_count > 5:
            result.append(f"  ... and {file_count - 5} more")
    
    return "\n".join(result)


def format_hypotheses(hypotheses: List[Dict]) -> str:
    """
    Format architecture hypotheses with confidence scores and detailed evidence.
    Enhanced to handle the new rich hypothesis format with pattern_type and characteristics.
    """
    if not hypotheses:
        return "No architectural patterns detected."
    
    lines = []
    
    # Group by pattern type for better organization
    by_type = {}
    for h in hypotheses:
        pattern_type = h.get('pattern_type', 'General')
        if pattern_type not in by_type:
            by_type[pattern_type] = []
        by_type[pattern_type].append(h)
    
    for pattern_type, patterns in sorted(by_type.items()):
        lines.append(f"\n{pattern_type.upper()}:")
        for h in patterns:
            claim = h.get('claim', 'Unknown pattern')
            confidence = h.get('confidence', 0) * 100
            evidence = h.get('evidence', {})
            characteristics = h.get('characteristics', [])
            warning = h.get('warning', None)
            
            lines.append(f"\n• {claim} (Confidence: {confidence:.0f}%)")
            
            # Format evidence
            if evidence:
                lines.append("  Evidence:")
                for key, value in evidence.items():
                    if isinstance(value, list):
                        if value:
                            lines.append(f"    - {key}: {', '.join(str(v) for v in value[:3])}")
                            if len(value) > 3:
                                lines.append(f"      ... and {len(value) - 3} more")
                    else:
                        lines.append(f"    - {key}: {value}")
            
            # Format characteristics
            if characteristics:
                lines.append("  Characteristics:")
                for char in characteristics:
                    lines.append(f"    → {char}")
            
            # Add warning if present (for anti-patterns)
            if warning:
                lines.append(f"  {warning}")
    
    return "\n".join(lines)


def format_assumptions(assumptions: List[Dict]) -> str:
    """
    Format assumptions with full evidence detail, grouped by risk level.
    Enhanced to handle the new detailed assumption format with evidence dicts.
    """
    if not assumptions:
        return "No architectural assumptions detected."
    
    # Group by risk level
    critical = [a for a in assumptions if a.get('risk_level', '').upper() == 'CRITICAL']
    high = [a for a in assumptions if a.get('risk_level', '').upper() == 'HIGH']
    medium = [a for a in assumptions if a.get('risk_level', '').upper() == 'MEDIUM']
    low = [a for a in assumptions if a.get('risk_level', '').upper() == 'LOW']
    
    def format_group(items):
        if not items:
            return "  None detected"
        
        result = []
        for a in items:
            assumption = a.get('assumption', 'Unknown')
            impact = a.get('impact', 'Unknown impact')
            confidence = a.get('confidence', 0) * 100
            evidence = a.get('evidence', {})
            mitigation = a.get('mitigation', [])
            
            result.append(f"\n  • {assumption}")
            result.append(f"    Confidence: {confidence:.0f}%")
            result.append(f"    Impact: {impact}")
            
            # Format evidence details
            if evidence:
                result.append("    Evidence:")
                for key, value in evidence.items():
                    if isinstance(value, list):
                        if value and len(value) > 0:
                            result.append(f"      - {key}: {', '.join(str(v) for v in value[:3])}")
                    elif isinstance(value, dict):
                        result.append(f"      - {key}:")
                        for k, v in value.items():
                            result.append(f"          {k}: {v}")
                    else:
                        result.append(f"      - {key}: {value}")
            
            # Format mitigation strategies
            if mitigation:
                result.append("    Mitigation:")
                for m in mitigation[:3]:  # Show top 3
                    result.append(f"      → {m}")
                if len(mitigation) > 3:
                    result.append(f"      ... and {len(mitigation) - 3} more strategies")
        
        return "\n".join(result)
    
    sections = []
    
    if critical:
        sections.append(f"CRITICAL RISK ({len(critical)} assumptions):")
        sections.append(format_group(critical))
    
    if high:
        sections.append(f"\nHIGH RISK ({len(high)} assumptions):")
        sections.append(format_group(high))
    
    if medium:
        sections.append(f"\nMEDIUM RISK ({len(medium)} assumptions):")
        sections.append(format_group(medium))
    
    if low:
        sections.append(f"\nLOW RISK ({len(low)} assumptions):")
        sections.append(format_group(low))
    
    return "\n".join(sections)


def format_stress_results(stress_results: List[Dict]) -> str:
    """Format stress test results with detail."""
    if not stress_results:
        return "No stress test results available."
    
    sections = []
    for result in stress_results:
        name = result.get('stress', 'Unknown Test')
        applicable = result.get('is_applicable', False)
        
        if not applicable:
            continue  # Skip non-applicable tests
        
        # Extract key data
        failure = result.get('failure_mode', 'Unknown failure')
        affected = result.get('affected_files', [])
        bottlenecks = result.get('bottlenecks', [])
        confidence = result.get('confidence', 0) * 100
        
        section = f"""
TEST: {name}
Confidence: {confidence:.0f}%
Failure Mode: {failure}
Affected Files: {len(affected)} components
"""
        
        # Add bottlenecks if present
        if bottlenecks:
            section += "\nBOTTLENECKS IDENTIFIED:\n"
            for b in bottlenecks[:3]:  # Top 3
                section += f"  • {b.get('component', 'Unknown')}: {b.get('reason', 'Unknown')}\n"
                section += f"    Severity: {b.get('severity', 'unknown').upper()}\n"
                section += f"    Fix: {b.get('recommendation', 'No recommendation')}\n"
        
        sections.append(section)
    
    return "\n---\n".join(sections)


def format_detection_summary(state: RepoState) -> str:
    """
    Create a comprehensive summary of all detected patterns and evidence.
    This gives the LLM a bird's eye view of the codebase intelligence.
    """
    summary = []
    
    # Count detections
    hypothesis_count = len(state.architecture_hypotheses) if state.architecture_hypotheses else 0
    assumption_count = len(state.assumptions) if state.assumptions else 0
    layer_count = len(state.layers) if state.layers else 0
    
    summary.append("DETECTION SUMMARY:")
    summary.append(f"• Architecture Patterns Detected: {hypothesis_count}")
    summary.append(f"• Assumptions Identified: {assumption_count}")
    summary.append(f"• Architectural Layers: {layer_count}")
    
    # Technology stack detected
    if state.assumptions:
        tech_stack = []
        for a in state.assumptions:
            assumption_text = a.get('assumption', '')
            if 'database' in assumption_text.lower():
                evidence = a.get('evidence', {})
                if evidence.get('database_type'):
                    tech_stack.append(f"Database: {evidence['database_type']}")
                if evidence.get('orm_type'):
                    tech_stack.append(f"ORM: {evidence['orm_type']}")
            elif 'state management' in assumption_text.lower():
                evidence = a.get('evidence', {})
                if evidence.get('state_manager'):
                    tech_stack.append(f"State: {evidence['state_manager']}")
            elif 'authentication' in assumption_text.lower():
                evidence = a.get('evidence', {})
                if evidence.get('auth_type'):
                    tech_stack.append(f"Auth: {evidence['auth_type']}")
            elif 'testing' in assumption_text.lower():
                evidence = a.get('evidence', {})
                if evidence.get('test_framework'):
                    tech_stack.append(f"Testing: {evidence['test_framework']}")
            elif 'deployment' in assumption_text.lower():
                evidence = a.get('evidence', {})
                if evidence.get('platform'):
                    tech_stack.append(f"Deploy: {evidence['platform']}")
        
        if tech_stack:
            summary.append("\nDETECTED TECHNOLOGY STACK:")
            for tech in tech_stack:
                summary.append(f"  • {tech}")
    
    # Risk summary
    if state.assumptions:
        risk_counts = {
            'CRITICAL': len([a for a in state.assumptions if a.get('risk_level', '').upper() == 'CRITICAL']),
            'HIGH': len([a for a in state.assumptions if a.get('risk_level', '').upper() == 'HIGH']),
            'MEDIUM': len([a for a in state.assumptions if a.get('risk_level', '').upper() == 'MEDIUM']),
            'LOW': len([a for a in state.assumptions if a.get('risk_level', '').upper() == 'LOW']),
        }
        
        summary.append("\nRISK PROFILE:")
        for level, count in risk_counts.items():
            if count > 0:
                summary.append(f"  • {level}: {count} assumptions")
    
    return "\n".join(summary)


# ============================================================================
# BASE RULES
# ============================================================================

BASE_RULES = """You are a technical documentation writer analyzing a SPECIFIC GitHub repository.

CRITICAL RULES:
1. Use ONLY the analysis data provided - this is REAL data from the actual codebase
2. Do NOT make generic statements - be SPECIFIC to this repository
3. Do NOT guess or assume - if data is missing, state that explicitly
4. Do NOT write tutorial-style content - write ANALYSIS of THIS codebase
5. Use concrete numbers, file names, and metrics from the provided data
6. Write in present tense about what EXISTS, not what "could" or "might" exist
7. When evidence includes specific file paths, technology names, or numbers - USE THEM

BAD Example: "This project is a modern web application that likely uses React..."
GOOD Example: "This repository contains 65 TypeScript files implementing a React component library with Redux state management (12 store files detected) and Jest testing framework (test_ratio: 32.5%)."
"""


# ============================================================================
# ENHANCED PROMPT GENERATORS
# ============================================================================

def get_overview_prompt(state: RepoState) -> str:
    """Generate overview documentation prompt with rich context."""
    
    hypotheses_text = format_hypotheses(state.architecture_hypotheses)
    detection_summary = format_detection_summary(state)
    
    return f"""{BASE_RULES}

REPOSITORY FACTS (from analysis):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL: {state.repo_url}
Owner/Repo: {state.owner}/{state.repo}
Branch: {state.branch}
Total Files in Repo: {state.stats.get('files_total', 'unknown')}
Files Analyzed: {state.stats.get('files_selected', 'unknown')}
Code Symbols Extracted: {state.stats.get('symbols_extracted', 'unknown')}

ARCHITECTURE CLASSIFICATION:
Archetype: {state.archetype.upper() if state.archetype else 'UNKNOWN'}

{detection_summary}

DETECTED PATTERNS (detailed):
{hypotheses_text}

TECHNOLOGY INDICATORS:
{chr(10).join([f"• Layer: {name} ({len(files)} files)" for name, files in list(state.layers.items())[:5]])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK:
Write a 2-3 paragraph "Overview" section that explains:

1. **What This Repository Is**: State clearly if it's a library, application, API, etc.
   - Use the archetype and patterns above
   - Be SPECIFIC: "This is a React component library" not "This is a web project"
   - Reference specific technologies from the DETECTION SUMMARY

2. **Core Purpose**: What problem does this solve?
   - Infer from the patterns and layer structure
   - Example: "Provides 40+ reusable UI components with Redux state management" not "Helps build UIs"

3. **Scope & Scale**: How big and complex is it?
   - Use the file counts and symbol counts
   - Mention key statistics
   - Reference detected tech stack

OUTPUT REQUIREMENTS:
• Start with "## Overview"
• 2-3 paragraphs, approximately 150-250 words
• Use SPECIFIC numbers from the data above
• Mention specific technologies detected (e.g., "Redux", "PostgreSQL", "Jest")
• Do NOT use phrases like "likely", "probably", "appears to be"
• Do NOT include placeholder sections like "Getting Started" or "Installation"
• Focus on WHAT IT IS, not how to use it

EXAMPLE GOOD START:
"This repository is a TypeScript-based React component library containing 65 analyzed files and 362 exported symbols. The system implements a component library architecture pattern (95% confidence) with Redux state management (12 store files) and comprehensive Jest testing (test coverage: 32.5%). The codebase uses PostgreSQL with Prisma ORM and deploys via Docker..."

NOW WRITE THE OVERVIEW:"""


def get_architecture_prompt(state: RepoState) -> str:
    """Generate architecture documentation prompt with enhanced evidence."""
    
    layers_text = format_layers(state.layers)
    metrics_text = format_graph_metrics(state.graph_metrics)
    hypotheses_text = format_hypotheses(state.architecture_hypotheses)
    
    return f"""{BASE_RULES}

ARCHITECTURAL DATA (from dependency analysis):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{metrics_text}

LAYER STRUCTURE:
{layers_text}

DETECTED ARCHITECTURAL PATTERNS:
{hypotheses_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

METRIC INTERPRETATION GUIDE:
• Fan-in: How many modules IMPORT a given module (high = widely used)
• Fan-out: How many modules a given module IMPORTS (high = highly coupled)
• Hubs: Modules with high fan-in - these are CRITICAL dependencies
• Leaves: Modules with zero fan-in - safe to modify, nothing depends on them

TASK:
Write a comprehensive "Architecture" section that:

1. **Describes the Layer Structure**:
   - List each layer and its responsibility
   - Mention file counts (use the numbers above)
   - Explain the hierarchy (which layer depends on which)

2. **Analyzes Dependency Patterns**:
   - Identify which modules are dependency hubs
   - Explain why they're critical (use fan-in/fan-out numbers)
   - Note any concerning patterns (god modules with >20 dependents)

3. **Identifies Architectural Patterns**:
   - Reference the DETECTED PATTERNS above
   - Mention specific pattern types and their confidence scores
   - Use the characteristics listed for each pattern
   - Note any anti-patterns with their warnings

4. **Highlights Risks**:
   - Point out tightly coupled modules
   - Identify single points of failure
   - Note modules with high blast radius
   - Reference any anti-patterns detected (Hub-and-spoke, God modules, Circular dependencies)

OUTPUT REQUIREMENTS:
• Start with "## Architecture"
• Use ### subheadings for each layer
• Include specific file names from the hubs list
• Reference actual numbers (fan-in, fan-out counts)
• Mention specific patterns by name (e.g., "MVC Pattern", "Repository Pattern")
• Identify at least 2-3 architectural risks based on the metrics
• Reference pattern confidence scores when discussing architecture decisions

EXAMPLE GOOD PARAGRAPH:
"The codebase exhibits a layered architecture (Confidence: 80%) with 3 distinct tiers. The system implements the Repository Pattern (Confidence: 75%) for data access abstraction. The ui layer (40 files) contains presentational components following the Atomic Design methodology (Confidence: 80%) with 15 atoms, 12 molecules, and 8 organisms detected. However, src/lib/utils.ts emerges as a critical hub with 23 dependents (fan-in: 23), creating a single point of failure and exhibiting the Hub-and-Spoke anti-pattern. Any breaking change to this module would impact 35% of the codebase..."

NOW WRITE THE ARCHITECTURE ANALYSIS:"""


def get_stress_test_prompt(state: RepoState) -> str:
    """
    Generate stress test analysis prompt - YOUR DIFFERENTIATOR!
    Enhanced with full assumption evidence.
    """
    
    stress_text = format_stress_results(state.stress_results)
    assumptions_text = format_assumptions(state.assumptions)
    metrics = state.graph_metrics or {}
    top_hub, fan_in_count = get_top_hub(metrics)
    hubs = state.graph_metrics.get('hubs', [])[:5]
    archetype = state.archetype or 'unknown'
    
    return f"""{BASE_RULES}

THIS IS YOUR DIFFERENTIATING FEATURE - MAKE IT EXCELLENT!

STRESS TEST RESULTS (from analysis engine):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{stress_text}

ARCHITECTURAL CONTEXT:
• Archetype: {archetype}
• Core Dependency Hubs: {', '.join(hubs)}
• Total Modules: {state.graph_metrics.get('total_nodes', 'unknown')}
• Repository Type: {'LIBRARY' if archetype == 'library' else 'APPLICATION'}

ARCHITECTURAL ASSUMPTIONS (relevant to stress analysis):
{assumptions_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UNDERSTANDING "ARCHITECTURAL FRAGILITY":
Architectural fragility = structural weaknesses that make systems vulnerable under stress.
This includes:
• Synchronous bottlenecks (blocking operations)
• Shared mutable state (concurrency issues)
• Deep dependency chains (cascade failures)
• Singleton patterns (resource contention)
• God modules (single points of failure)
• Missing async boundaries

SPECIAL NOTE FOR LIBRARIES:
If this is a LIBRARY (not a deployed application), stress tests apply to APPLICATIONS USING THIS LIBRARY:
• Bundle size stress: How much does this library add to consuming apps?
• Re-render cascades: Do shared hooks cause performance issues?
• Composition depth: Does nesting components cause problems?
• Tree-shaking: Can consumers import only what they need?

TASK:
Write a comprehensive "Stress Test Analysis" section with these MANDATORY sections:

### 1. Executive Summary Table
Create a table showing:
| Test Scenario | Applicable? | Breaking Point | Primary Bottleneck | Risk Level |

### 2. Detailed Analysis (for each APPLICABLE test)
For each test that shows is_applicable=true:

**A. What Breaks & When**
- State the specific breaking point (use exact numbers from results)
- Describe the failure mode (from the data)
- Explain immediate symptoms

**B. Root Cause Analysis** 
- Link failure to SPECIFIC architecture decisions
- Reference actual modules from the dependency hubs list
- Use evidence from ARCHITECTURAL ASSUMPTIONS section
- Explain WHY it breaks (architectural cause, not just symptom)

Example: "The bottleneck occurs in {top_hub} (a hub with {fan_in_count} dependents) because it uses synchronous operations without connection pooling (detected: no connection pooling in deployment config), creating a cascade when traffic exceeds 5000 requests/second."

**C. Code-Level Evidence**
- Point to specific layers where bottlenecks exist
- Reference dependency hubs if they're involved
- Connect to the architectural data and detected patterns
- Use specific tech stack info (e.g., "PostgreSQL without connection pooling", "Redux without normalization")

**D. Scaling Implications**
Predict what happens as load increases:
- At 2x current breaking point
- At 10x traffic
- During traffic spikes

**E. Architectural Recommendations**
Suggest STRUCTURAL fixes (not implementation details):
- Pattern changes ("introduce async boundaries")
- Architectural refactoring ("implement queue-based processing")
- Isolation strategies ("add connection pooling layer")
- Reference detected patterns and suggest improvements

DO NOT suggest code-level fixes like "add async/await" - suggest architecture changes like "introduce message queue pattern"

### 3. Assumption-Related Risks
Link stress test findings to the ARCHITECTURAL ASSUMPTIONS:
- Which HIGH/CRITICAL risk assumptions amplify stress test failures?
- How do detected technology choices (DB, state management, auth) affect resilience?

### 4. Non-Applicable Tests (if any)
Briefly list which tests don't apply and why, but don't dwell on them.

### 5. Overall Risk Assessment
Summarize the overall architectural fragility level: LOW, MEDIUM, HIGH, CRITICAL
Base this on both stress test results AND assumption risk levels.

OUTPUT REQUIREMENTS:
• Start with "## Stress Test Analysis"
• Use the table format for the summary
• Write in PRESENT tense ("the system breaks when..." not "would break")
• Be SPECIFIC with numbers from the test results
• Link EVERY bottleneck to actual code structure and detected evidence
• Reference specific technologies detected (PostgreSQL, Redis, etc.)
• For libraries: explain impact on consuming applications
• Cross-reference architectural assumptions section
• Minimum 800 words for applicable tests
• Do NOT say "more testing needed" - analyze what you have

CRITICAL: This section differentiates your product from competitors. Make it:
✓ Detailed and technical
✓ Actionable (clear recommendations)
✓ Evidence-based (tied to architecture AND assumptions)
✓ Specific (actual file names, numbers, patterns, technologies)

NOW WRITE THE STRESS TEST ANALYSIS:"""


def get_core_modules_prompt(state: RepoState) -> str:
    """Generate core modules analysis prompt."""
    
    metrics = state.graph_metrics
    hubs = metrics.get('hubs', [])[:10]
    
    # Try to get hub details if available
    hub_details_text = ""
    if hubs:
        hub_details_text = "MODULE CRITICALITY ANALYSIS:\n"
        for i, hub in enumerate(hubs):
            # Try to calculate dependents
            dependents = [k for k, v in state.dependency_graph.items() if hub in v]
            fan_in = len(dependents)
            hub_details_text += f"{i+1}. {hub}\n"
            hub_details_text += f"   • Imported by: {fan_in} modules\n"
            hub_details_text += f"   • Blast radius: {fan_in / max(metrics.get('total_nodes', 1), 1) * 100:.1f}% of codebase\n"
    
    return f"""{BASE_RULES}

DEPENDENCY HUB ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{hub_details_text}

CONTEXT:
• Total modules: {metrics.get('total_nodes', 'unknown')}
• Average fan-in: {metrics.get('avg_fan_in', 0):.2f}
• Total dependencies: {metrics.get('total_edges', 'unknown')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK:
Write a "Core Modules" section identifying the 5-7 most critical modules:

For EACH core module, provide:
1. **Module Name & Location**: Full path from the hubs list
2. **Why It's Critical**: Use fan-in numbers and percentage
3. **Blast Radius**: How many files affected if it changes (use the numbers above)
4. **Risk Assessment**: HIGH/MEDIUM/LOW based on coupling
5. **Responsibilities**: Infer from name and layer

Use this priority framework:
• Fan-in > 15: CRITICAL (god module risk)
• Fan-in 8-15: HIGH (important shared component)  
• Fan-in 3-7: MEDIUM (commonly used utility)

OUTPUT REQUIREMENTS:
• Start with "## Core Modules"
• Analyze only the modules in the hubs list above
• Use actual numbers (don't say "many" - say "23 dependents")
• Rank by criticality (most critical first)
• Include a summary paragraph about modularity health

NOW WRITE THE CORE MODULES ANALYSIS:"""


def get_system_boundaries_prompt(state: RepoState) -> str:
    """Generate system boundaries documentation prompt with enhanced evidence."""
    
    assumptions_text = format_assumptions(state.assumptions)
    archetype = state.archetype or 'unknown'
    
    # Detect what's present
    layers = state.layers.keys()
    has_ui = any('ui' in str(l).lower() or 'component' in str(l).lower() for l in layers)
    has_api = any('api' in str(l).lower() or 'server' in str(l).lower() for l in layers)
    has_db = any('db' in str(l).lower() or 'database' in str(l).lower() for l in layers)
    
    # Extract tech stack from assumptions
    tech_details = {}
    if state.assumptions:
        for a in state.assumptions:
            evidence = a.get('evidence', {})
            if 'database_type' in evidence:
                tech_details['database'] = evidence['database_type']
            if 'orm_type' in evidence:
                tech_details['orm'] = evidence['orm_type']
            if 'state_manager' in evidence:
                tech_details['state'] = evidence['state_manager']
            if 'auth_type' in evidence:
                tech_details['auth'] = evidence['auth_type']
            if 'platform' in evidence:
                tech_details['deployment'] = evidence['platform']
    
    tech_summary = "\n".join([f"• {k.title()}: {v}" for k, v in tech_details.items()])
    
    return f"""{BASE_RULES}

SYSTEM CLASSIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Archetype: {archetype.upper()}

DETECTED PRESENCE:
• Frontend/UI layer: {'YES' if has_ui else 'NO'}
• API/Backend layer: {'YES' if has_api else 'NO'}  
• Database layer: {'YES' if has_db else 'NO'}

DETECTED TECHNOLOGIES:
{tech_summary if tech_summary else '• No specific technologies detected'}

ARCHITECTURAL ASSUMPTIONS (from analysis):
{assumptions_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK:
Write a "System Boundaries" section that clearly defines what IS and ISN'T in this repository:

### What IS Included (THIS Repository)
List EXACTLY what's in this repo based on detected layers and technologies:
- Reference specific tech stack (e.g., "✅ React UI components with Redux state management")
- Use detected technology names from DETECTED TECHNOLOGIES above

### What IS NOT Included (External Dependencies)
Based on the archetype and assumptions, state what's EXTERNAL:
- If no backend detected: "❌ No backend - business logic external"
- If no database: "❌ No database - data persistence external"
- Be specific about what's missing using the assumptions evidence

### Integration Requirements
What must external systems provide for this to work?
- Use evidence from assumptions (e.g., "Requires external PostgreSQL database")
- Reference specific auth requirements if detected

### Key Assumptions About Boundaries
Use the assumptions data above to explain:
- What responsibilities are delegated externally
- What this system expects to exist outside itself
- Include risk levels from assumptions

OUTPUT REQUIREMENTS:
• Start with "## System Boundaries"
• Use ✅ and ❌ for clarity
• Be definitive based on the detected layers and technologies
• Reference specific technologies by name (PostgreSQL, Redis, JWT, etc.)
• Reference the assumptions data with their evidence
• Do NOT speculate - use only detected information

EXAMPLE:
"### What IS Included
✅ React frontend with 45 UI components implementing Atomic Design (Confidence: 80%)
✅ Redux state management with 12 store files
✅ JWT authentication layer (detected in 8 auth files)
✅ Jest testing framework with 32.5% coverage

### What IS NOT Included  
❌ Backend API - assumes external REST API (HIGH RISK - see assumptions)
❌ PostgreSQL database - data layer external (detected PostgreSQL usage without local DB)
..."

NOW WRITE THE SYSTEM BOUNDARIES:"""


def get_assumptions_prompt(state: RepoState) -> str:
    """Generate assumptions documentation prompt with full evidence detail."""
    
    assumptions_text = format_assumptions(state.assumptions)
    
    return f"""{BASE_RULES}

DETECTED ARCHITECTURAL ASSUMPTIONS (from code analysis):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{assumptions_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: These are DETECTED assumptions, not guesses!
The evidence field shows exactly what was found in the codebase.

TASK:
Write an "Architectural Assumptions" section analyzing these assumptions:

For EACH assumption (grouped by risk level):
1. **The Assumption**: State it clearly
2. **Evidence**: Why we know this (use the detailed evidence field)
   - Include specific file counts, technology names, configuration presence
   - Example: "Evidence: 12 Redux store files detected, state_manager: Redux"
3. **Impact**: What happens because of this assumption (from impact field)
4. **When It Breaks**: Specific conditions that invalidate it
5. **Mitigation**: How to reduce the risk (use the mitigation strategies provided)
   - List all mitigation strategies from the data

Focus on CRITICAL and HIGH risk first, but cover all levels.

OUTPUT REQUIREMENTS:
• Start with "## Architectural Assumptions"
• Group by risk level (### Critical Risk, ### High Risk, ### Medium Risk, ### Low Risk)
• Address each assumption in the data above with its full evidence
• Use specific numbers and technology names from evidence (e.g., "12 store files", "PostgreSQL", "Jest")
• Be specific about breaking conditions (numbers, thresholds)
• Include ALL mitigation strategies provided
• Do NOT invent new assumptions - analyze only what's provided
• Reference confidence scores

EXAMPLE GOOD SECTION:
"### High Risk

**No Centralized State Management Detected**
• Confidence: 75%
• Evidence: 45 UI components detected with no Redux, Zustand, MobX, Recoil, or Context Provider patterns found
• Impact: State likely managed via props drilling or local component state, leading to maintenance issues
• When It Breaks: When component tree depth exceeds 5 levels or when state needs to be shared across 10+ components
• Mitigation:
  → Consider adopting Redux, Zustand, or Context API
  → Audit prop drilling depth
  → Implement state management for complex flows"

NOW WRITE THE ASSUMPTIONS ANALYSIS:"""


def validate_state_for_docs(state: RepoState) -> Dict[str, List[str]]:
    """
    Validate that state has necessary data for documentation.
    Returns dict of {section_name: [warnings]}.
    Enhanced to check for evidence quality.
    """
    warnings = {}
    
    # Overview validation
    overview_warnings = []
    if not state.archetype:
        overview_warnings.append("No archetype detected - classification may be generic")
    if not state.architecture_hypotheses:
        overview_warnings.append("No architecture patterns detected")
    else:
        # Check if hypotheses have evidence
        hypotheses_without_evidence = [h for h in state.architecture_hypotheses if not h.get('evidence')]
        if hypotheses_without_evidence:
            overview_warnings.append(f"{len(hypotheses_without_evidence)} patterns detected without evidence")
    if overview_warnings:
        warnings['overview'] = overview_warnings
    
    # Architecture validation
    arch_warnings = []
    if not state.layers:
        arch_warnings.append("No layers detected - architecture analysis will be minimal")
    if not state.graph_metrics:
        arch_warnings.append("No graph metrics available")
    if arch_warnings:
        warnings['architecture'] = arch_warnings
    
    # Assumptions validation
    assumption_warnings = []
    if not state.assumptions:
        assumption_warnings.append("No assumptions detected - boundary analysis will be limited")
    else:
        # Check for evidence quality
        assumptions_without_evidence = [a for a in state.assumptions if not a.get('evidence')]
        if assumptions_without_evidence:
            assumption_warnings.append(f"{len(assumptions_without_evidence)} assumptions without evidence")
        
        # Check for mitigation strategies
        assumptions_without_mitigation = [a for a in state.assumptions if not a.get('mitigation')]
        if assumptions_without_mitigation:
            assumption_warnings.append(f"{len(assumptions_without_mitigation)} assumptions without mitigation strategies")
    
    if assumption_warnings:
        warnings['assumptions'] = assumption_warnings
    
    # Stress test validation
    stress_warnings = []
    if not state.stress_results:
        stress_warnings.append("CRITICAL: No stress test results!")
    elif all(not r.get('is_applicable', False) for r in state.stress_results):
        stress_warnings.append("WARNING: All stress tests marked non-applicable")
    if stress_warnings:
        warnings['stress_analysis'] = stress_warnings
    
    return warnings