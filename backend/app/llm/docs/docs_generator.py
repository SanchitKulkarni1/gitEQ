# app/docs/docs_generator.py
import concurrent.futures
from typing import Dict, Tuple, Callable
from google.genai import types
from app.llm.gemini_client import client  # Importing the client from your setup
from app.models.state import RepoState
from app.llm.docs.prompts import (
    get_overview_prompt,
    get_architecture_prompt,
    get_core_modules_prompt,
    get_system_boundaries_prompt,
    get_assumptions_prompt,
    get_stress_test_prompt,
    validate_state_for_docs,
)

# Configuration for the LLM calls
GEN_CONFIG = types.GenerateContentConfig(
    temperature=0.2,
    top_p=0.9,
    max_output_tokens=2048,
)
MODEL_NAME = "gemini-1.5-flash"  # Using Flash for speed/cost, switch to Pro if needed

def fetch_section(task_args: Tuple[str, Callable, RepoState]) -> Tuple[str, str]:
    """
    Worker function to generate a single documentation section.
    Args:
        task_args: Tuple of (section_key, prompt_generator_func, state)
    Returns:
        Tuple of (section_key, generated_text)
    """
    key, prompt_func, state = task_args
    
    # 1. Generate the prompt (CPU bound, fast)
    try:
        prompt = prompt_func(state)
        
        # 2. Call LLM (I/O bound, slow - this benefits from parallelism)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=GEN_CONFIG
        )
        return key, response.text.strip()
        
    except Exception as e:
        # Graceful failure: return the error as the section content so the pipeline doesn't crash
        return key, f"Error generating section: {str(e)}"

def generate_docs_sectionwise(state: RepoState) -> Dict:
    """
    Generates all documentation sections in parallel.
    """
    # 1. Run Validation First
    warnings = validate_state_for_docs(state)

    # 2. Define the work to be done
    # Format: (output_key, prompt_function)
    tasks_map = [
        ("overview", get_overview_prompt),
        ("architecture", get_architecture_prompt),
        ("core_modules", get_core_modules_prompt),
        ("system_boundaries", get_system_boundaries_prompt),
        ("assumptions", get_assumptions_prompt),
        ("stress_analysis", get_stress_test_prompt),
    ]

    # Prepare arguments for the workers
    # We pass 'state' to every worker
    worker_args = [(key, func, state) for key, func in tasks_map]

    docs = {}
    
    # 3. Execute in Parallel
    # We use 6 workers because you have exactly 6 sections. 
    # This ensures maximum concurrency without queuing.
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # map returns results in the order they were submitted, 
        # but execution happens concurrently
        results = executor.map(fetch_section, worker_args)
        
        # Collect results
        for key, content in results:
            docs[key] = content

    return {
        "docs": docs,
        "warnings": warnings,
    }