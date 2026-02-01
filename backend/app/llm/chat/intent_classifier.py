# app/chat/intent_classifier.py
import json
from app.llm.gemini_client import client
from google.genai import types

GEN_CONFIG = types.GenerateContentConfig(
    temperature=0.0,
    response_mime_type="application/json" # Force JSON output for reliability
)

# Use your High-Limit Model
MODEL_NAME = "gemini-2.5-flash-lite"

def comprehend_query(question: str):
    """
    Performs Intent Classification AND Entity Extraction in a single shot.
    Returns: (intent_string, entities_dict)
    """
    prompt = f"""
    Analyze the user question about a GitHub repository.
    
    1. CLASSIFY INTENT into ONE category:
       [structure, change_impact, architecture, stress, code_lookup, unknown]
    
    2. EXTRACT ENTITIES:
       - 'files': list of file paths (e.g. 'main.py', 'auth/login.ts')
       - 'layers': list of architectural layers (e.g. 'ui', 'database', 'api')

    Question: "{question}"
    
    Return JSON format:
    {{
        "intent": "category_name",
        "entities": {{
            "files": [],
            "layers": []
        }}
    }}
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt, 
            config=GEN_CONFIG
        )
        
        # Parse the JSON response
        data = json.loads(response.text.strip())
        
        # safely extract (defaults provided in case LLM hallucinates structure)
        intent = data.get("intent", "unknown").lower()
        entities = data.get("entities", {"files": [], "layers": []})
        
        return intent, entities

    except Exception as e:
        print(f"DEBUG: Comprehension failed: {e}")
        return "unknown", {"files": [], "layers": []}

def comprehend_query(question: str):
    """
    Performs Intent Classification AND Entity Extraction.
    """
    prompt = f"""
    You are a developer assistant. Analyze the query and return a JSON object.
    
    1. CLASSIFY INTENT (Choose ONE):
       - "stress": Questions about LOAD (users, traffic, spike) or FAILURE (crash, down, break, what happens if X fails).
       - "change_impact": Questions about editing code (modifying, changing, updating a file).
       - "structure": Questions about how code is organized or where things are.
       - "code_lookup": Questions asking to see specific code or functions.
       - "architecture": High-level questions about tech stack or design patterns.
    
    2. EXTRACT ENTITIES:
       - 'files': list of file paths (e.g. 'main.py').
       - 'layers': list of architectural layers (e.g. 'ui', 'api', 'database').

    Query: "{question}"
    
    Return ONLY raw JSON.
    Example: {{"intent": "stress", "entities": {{"files": [], "layers": ["api"]}}}}
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt, 
            config=GEN_CONFIG
        )
        
        # Clean up formatting
        text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(text)
        
        return data.get("intent", "unknown").lower(), data.get("entities", {"files": [], "layers": []})

    except Exception as e:
        print(f"DEBUG: Comprehension failed: {e}")
        return "unknown", {"files": [], "layers": []}