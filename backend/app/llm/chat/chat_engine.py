# app/llm/chat/chat_engine.py
"""
Improved chatbot engine with:
1. Rule-based intent classification (fast, free, reliable)
2. Better entity extraction
3. Context validation
4. Intent-specific prompts
"""

import re
import os
from typing import Tuple, Dict, List, Optional
from app.models.state import RepoState
from app.llm.chat.retrieval import (
    get_structure_context,
    get_change_impact_context,
    get_stress_context,
    get_code_context,
)
from app.llm.gemini_client import get_client
from app.stress.stress_engine import run_stress_test
from app.stress.stress_models import StressVector, ArchitectureType

# Use fast model for final answer generation
CHAT_MODEL = "gemini-flash-latest"  # Fast and generous limits


# ============================================================================
# RULE-BASED INTENT CLASSIFICATION (No LLM needed!)
# ============================================================================

def classify_intent_fast(question: str) -> str:
    """
    Fast, deterministic intent classification using keywords.
    NO LLM call = 0ms latency, $0 cost, 100% reliable format.
    """
    q_lower = question.lower()
    
    # 1. STRESS/PERFORMANCE - highest priority
    stress_keywords = [
        'stress', 'load', 'performance', 'bottleneck', 'scale',
        'concurrent', 'users', 'break', 'crash', 'fail', 'down',
        'memory', 'slow', 'timeout', 'spike', 'traffic',
        'throughput', 'latency', 'capacity', '5000', '1000',
        'what happens if', 'what if', 'under load', 'heavy load'
    ]
    if any(kw in q_lower for kw in stress_keywords):
        return "stress"
    
    # 2. CHANGE IMPACT
    impact_keywords = [
        'impact', 'change', 'affect', 'modify', 'edit', 'update',
        'depend', 'break if', 'blast radius', 'ripple', 'consequence',
        'side effect', 'what happens if i change', 'what if i modify'
    ]
    # Also check for file mentions
    if any(kw in q_lower for kw in impact_keywords) or re.search(r'\.(py|ts|tsx|js|jsx)', question):
        return "change_impact"
    
    # 3. CODE LOOKUP
    code_keywords = [
        'show me', 'code for', 'implementation', 'how does',
        'show code', 'view', 'look at', 'see the'
    ]
    # Check for file extensions
    if any(kw in q_lower for kw in code_keywords) or re.search(r'\.(py|ts|tsx|js|jsx|java|go)', question):
        return "code_lookup"
    
    # 4. ARCHITECTURE
    arch_keywords = [
        'architecture', 'pattern', 'design', 'structure', 'organized',
        'layer', 'module', 'component', 'organize', 'coupling',
        'separation', 'tech stack', 'framework', 'technologies'
    ]
    if any(kw in q_lower for kw in arch_keywords):
        return "architecture"
    
    # 5. DEFAULT to STRUCTURE for general questions
    return "structure"


# ============================================================================
# ENTITY EXTRACTION (No LLM needed for most cases!)
# ============================================================================

def extract_entities(question: str, state: RepoState) -> Dict[str, List[str]]:
    """
    Extract files and layers from question using regex and fuzzy matching.
    Falls back to LLM only if regex fails.
    """
    entities = {"files": [], "layers": []}
    
    # Extract file paths using regex
    file_patterns = [
        r'[\w/\-]+\.(py|ts|tsx|js|jsx|java|go|rs|c|cpp)',  # Full paths
        r'(?:src|app|lib|components)/[\w/\-]+',  # Common prefixes
    ]
    
    for pattern in file_patterns:
        matches = re.findall(pattern, question, re.IGNORECASE)
        entities["files"].extend(matches)
    
    # Extract module/class names (PascalCase or camelCase)
    module_patterns = [
        r'\b[A-Z][a-zA-Z0-9]*(?:[A-Z][a-zA-Z0-9]*)+\b',  # PascalCase
        r'\b[a-z]+(?:[A-Z][a-z]+)+\b',  # camelCase
    ]
    
    modules = []
    for pattern in module_patterns:
        matches = re.findall(pattern, question)
        modules.extend(matches)
    
    # Try to find files containing these modules
    if modules and not entities["files"]:
        for module in modules:
            file = find_file_by_symbol(state, module)
            if file:
                entities["files"].append(file)
    
    # Extract layer keywords
    layer_keywords = {
        'ui': ['ui', 'frontend', 'client', 'components', 'views'],
        'api': ['api', 'backend', 'server', 'routes', 'endpoints'],
        'database': ['database', 'db', 'models', 'data', 'storage'],
        'auth': ['auth', 'authentication', 'login', 'security'],
        'services': ['services', 'business logic', 'domain'],
    }
    
    for layer, keywords in layer_keywords.items():
        if any(kw in question.lower() for kw in keywords):
            entities["layers"].append(layer)
    
    return entities


def find_file_by_symbol(state: RepoState, symbol_name: str) -> Optional[str]:
    """Find file containing a given symbol name."""
    for symbol in state.symbols:
        if symbol.name == symbol_name:
            return symbol.file
    
    # Fuzzy match in file paths
    symbol_lower = symbol_name.lower()
    for path in state.files_content.keys():
        if symbol_lower in path.lower():
            return path
    
    return None


# ============================================================================
# DYNAMIC STRESS TEST GENERATION
# ============================================================================

def infer_stress_params(question: str, entities: Dict) -> Dict:
    """
    Infer stress test parameters from question WITHOUT LLM.
    Uses keyword analysis.
    """
    q_lower = question.lower()
    
    # Determine severity
    severity = 0.5  # default medium
    if any(word in q_lower for word in ['huge', 'massive', 'extreme', '10000', '5000']):
        severity = 0.9
    elif any(word in q_lower for word in ['spike', 'sudden', 'burst']):
        severity = 0.8
    elif any(word in q_lower for word in ['moderate', 'normal']):
        severity = 0.5
    elif any(word in q_lower for word in ['small', 'minor', '10', '100']):
        severity = 0.3
    
    # Determine type
    if any(word in q_lower for word in ['crash', 'break', 'fail', 'down', 'missing']):
        prop_type = "dependency"
    elif any(word in q_lower for word in ['data', 'database', 'query']):
        prop_type = "data"
    elif any(word in q_lower for word in ['auth', 'login', 'session']):
        prop_type = "auth"
    else:
        prop_type = "traffic"
    
    # Use extracted layers or infer
    layers = entities.get("layers", [])
    if not layers:
        # Infer from question
        if any(word in q_lower for word in ['landing', 'page', 'ui', 'frontend']):
            layers = ['ui', 'components']
        elif any(word in q_lower for word in ['api', 'server', 'backend']):
            layers = ['api', 'routes']
        elif any(word in q_lower for word in ['database', 'db']):
            layers = ['database', 'models']
        else:
            layers = ['ui']  # default
    
    return {
        "layers": layers,
        "type": prop_type,
        "severity": severity
    }


# ============================================================================
# INTENT-SPECIFIC PROMPTS
# ============================================================================

def build_stress_prompt(question: str, context: Dict) -> str:
    """Build prompt specifically for stress questions."""
    return f"""You are analyzing STRESS TEST RESULTS for a software repository.

The user asked: "{question}"

STRESS TEST ANALYSIS:
{context}

Your task:
1. Explain WHAT breaks and AT WHAT THRESHOLD (use specific numbers)
2. Explain WHY it breaks (architectural root cause, not symptoms)
3. Link failures to specific modules or layers
4. Provide architectural recommendations (not code fixes)

Rules:
- Use ONLY the stress test data provided
- Be specific with numbers (don't say "many" - say "47 users")
- Reference actual file names if provided
- Focus on ARCHITECTURE, not implementation
- If the test shows "not applicable", explain why and what WOULD apply

Answer in 2-3 paragraphs, technically detailed but clear:"""


def build_change_impact_prompt(question: str, context: Dict) -> str:
    """Build prompt specifically for change impact questions."""
    file = context.get('file', 'unknown')
    dependents = context.get('direct_dependents', [])
    fan_in = context.get('fan_in', 0)
    is_core = context.get('is_core_module', False)
    
    return f"""You are analyzing CHANGE IMPACT for a software repository.

The user asked: "{question}"

FILE ANALYSIS:
• Target file: {file}
• Direct dependents: {fan_in} files
• Is core module: {'YES - HIGH RISK' if is_core else 'NO'}
• Risk level: {context.get('risk_level', 'unknown')}

Dependent files (what imports this):
{chr(10).join([f'  • {d}' for d in dependents[:10]])}

Your task:
1. State the blast radius (how many files affected)
2. List the actual dependent files
3. Assess risk level (HIGH/MEDIUM/LOW)
4. Suggest safer ways to make changes if high risk

Rules:
- Use the EXACT file names and numbers provided
- Don't invent dependencies not in the list
- Be specific about the impact
- Provide actionable advice

Answer in 2-3 paragraphs:"""


def build_structure_prompt(question: str, context: Dict) -> str:
    """Build prompt for structure/architecture questions."""
    return f"""You are explaining REPOSITORY STRUCTURE.

The user asked: "{question}"

REPOSITORY CONTEXT:
{context}

Your task:
Explain the structure clearly, focusing on:
- Layer organization
- Key components
- Technology stack (if available)
- Overall architecture pattern

Rules:
- Use ONLY information from the context
- Be concise but informative
- Don't make assumptions

Answer in 2-3 paragraphs:"""


# ============================================================================
# MAIN CHAT ENGINE
# ============================================================================

def answer_question(state: RepoState, question: str) -> str:
    """
    Main chat engine with improved intent classification and context building.
    
    Flow:
    1. Fast rule-based intent classification (no LLM)
    2. Entity extraction using regex (no LLM)
    3. Context retrieval based on intent
    4. Single LLM call with intent-specific prompt
    """
    
    # Step 1: Classify intent (FAST - no LLM)
    intent = classify_intent_fast(question)
    print(f"DEBUG: Intent='{intent}'")
    
    # Step 2: Extract entities (FAST - mostly regex)
    entities = extract_entities(question, state)
    print(f"DEBUG: Entities={entities}")
    
    # Step 3: Get context based on intent
    context = None
    prompt = ""
    
    if intent == "stress":
        # Check if we should run dynamic stress test
        if entities.get("layers"):
            print(f"DEBUG: Running dynamic stress test for layers: {entities['layers']}")
            
            # Generate stress params WITHOUT LLM
            stress_params = infer_stress_params(question, entities)
            
            # Create stress vector
            vector = StressVector(
                name="dynamic_user_query",
                description=question,
                target_layers=stress_params["layers"],
                severity=stress_params["severity"],
                propagation_type=stress_params["type"],
                architecture_types=[ArchitectureType.LIBRARY]  # Will be validated in engine
            )
            
            # Run stress test
            if hasattr(state, 'repo_context') and state.repo_context:
                result = run_stress_test(state, vector, repo_context=state.repo_context)
                context = result.dict()
            else:
                context = "Error: Architecture context missing"
        else:
            # Use pre-computed stress results
            context = get_stress_context(state)
        
        prompt = build_stress_prompt(question, context)
    
    elif intent == "change_impact":
        # Try to find the target file
        target_file = None
        
        if entities.get("files"):
            target_file = entities["files"][0]
        else:
            # Try to extract from question manually
            # Look for mentions of components or files
            words = question.split()
            for word in words:
                if word.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                    target_file = word
                    break
                # Try fuzzy match
                file = find_file_by_symbol(state, word)
                if file:
                    target_file = file
                    break
        
        if target_file:
            context = get_change_impact_context(state, target_file)
            prompt = build_change_impact_prompt(question, context)
        else:
            return "I couldn't identify which file or component you're asking about. Could you specify the file path or component name?"
    
    elif intent == "code_lookup":
        if entities.get("files"):
            context = get_code_context(state, entities["files"][0])
            if context != "File not found":
                prompt = f"Show the code for {entities['files'][0]}:\n\n```\n{context}\n```\n\nThis is the implementation."
            else:
                return f"File '{entities['files'][0]}' not found in the analyzed codebase."
        else:
            return "Which file would you like me to show you? Please specify the file path."
    
    elif intent in ["structure", "architecture"]:
        context = get_structure_context(state)
        prompt = build_structure_prompt(question, context)
    
    else:
        # Unknown intent
        context = get_structure_context(state)
        prompt = f"User question: {question}\n\nContext: {context}\n\nProvide a helpful answer based on the available context."
    
    # Step 4: Generate answer with ONE LLM call
    if not prompt:
        return "I don't have enough context to answer that question. Could you be more specific?"
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        client = get_client(api_key)
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"I encountered an error: {str(e)}\n\nPlease try rephrasing your question."


# ============================================================================
# HELPER: Context validation
# ============================================================================

def validate_context(context: any) -> bool:
    """Check if context has useful data."""
    if context is None:
        return False
    if isinstance(context, str) and context in ["File not found", ""]:
        return False
    if isinstance(context, dict) and not context:
        return False
    if isinstance(context, list) and len(context) == 0:
        return False
    return True