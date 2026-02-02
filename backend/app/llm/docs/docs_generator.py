# app/docs/docs_generator.py
import concurrent.futures
from typing import Dict, Any
from app.models.state import RepoState
from app.llm.gemini_client import client

# USE GEMMA (As per your working config)
MODEL_NAME = "gemini-2.5-flash-lite" 

def fetch_section(args):
    """
    Worker function for parallel execution.
    """
    section, state_dict = args
    # Reconstruct state from dict for the worker
    state = RepoState(**state_dict) 
    
    context = ""
    
    # --- BUILD CONTEXT BASED ON SECTION ---
    if section == "architecture":
        # FIX: Ensure we handle empty layers gracefully
        layer_summary = "\n".join([f"- {k}: {len(v)} files" for k, v in state.layers.items()])
        context = f"Layers:\n{layer_summary}\n\nDependency Stats: {state.stats}"

    elif section == "stress_analysis":
        # FIX: Ensure we are processing dictionaries, not tuples
        results = []
        for r in state.stress_results:
            # Check if 'r' is a dict or an object and convert to string safely
            r_str = str(r) if isinstance(r, (dict, str)) else r.json()
            results.append(r_str)
        context = "\n".join(results)

    # ... (Rest of context building logic for overview, etc. remains same) ...
    else:
        # Default context
        context = f"Files: {list(state.files_content.keys())[:50]}"

    prompt = f"Write a technical documentation section for '{section}' based on this context:\n{context}"
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt
        )
        return section, response.text.strip()
    except Exception as e:
        return section, f"Error generating section: {str(e)}"

def generate_docs_sectionwise(state: RepoState) -> Dict:
    # Define the sections we want
    sections = [
        "overview", 
        "architecture", 
        "core_modules", 
        "system_boundaries", 
        "assumptions", 
        "stress_analysis"
    ]
    
    # Serialize state ONCE to pass to workers
    state_dict = state.dict()
    worker_args = [(s, state_dict) for s in sections]
    
    docs = {}
    warnings = {}

    # Run in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_section, worker_args)
        
    for section, content in results:
        docs[section] = content
        if "Error" in content:
            warnings[section] = [content]

    return {"docs": docs, "warnings": warnings}