import json
from google.genai import types

# 1. Correct Imports
from app.llm.chat.intent_classifier import comprehend_query
from app.llm.chat.retrieval import (
    get_structure_context,
    get_change_impact_context,
    get_stress_context,
    get_code_context,
    answer_prompt
)
from app.llm.gemini_client import client
from app.stress.stress_engine import run_stress_test
from app.stress.stress_models import StressVector

# 2. Configuration for Extraction Tools (Use Lite for Speed/Quota)
TOOL_MODEL = "gemini-flash-latest"
GEN_CONFIG = types.GenerateContentConfig(temperature=0.0)

# 3. Configuration for Final Answer (Use Smartest Available)
CHAT_MODEL = "gemini-flash-latest"

def infer_stress_config(question: str) -> dict:
    """
    Uses LLM to smartly determine the physics of the stress test.
    """
    prompt = f"""
    Analyze this engineering question and extract stress test parameters.
    
    Question: "{question}"
    
    Rules:
    1. 'layers': Extract architectural layers mentioned (ui, api, database, auth, etc).
    2. 'type': 
       - "dependency": if asking about FAILURE, CRASH, BREAKING, or MISSING components.
       - "traffic": if asking about LOAD, USERS, SCALE, LATENCY, or CONCURRENCY.
    3. 'severity': 0.1 (low) to 1.0 (extreme) based on words like "huge", "spike", "kill".
    
    Return JSON ONLY: {{ "layers": ["..."], "type": "traffic" or "dependency", "severity": 0.8 }}
    """
    try:
        response = client.models.generate_content(
            model=TOOL_MODEL, 
            contents=prompt, 
            config=GEN_CONFIG
        )
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        print(f"DEBUG: Stress config inference failed: {e}")
        return {"layers": [], "type": "traffic", "severity": 0.5}

def answer_question(state, question: str):
    # 1. OPTIMIZED COMPREHENSION (1 Call instead of 2)
    intent, entities = comprehend_query(question)
    
    print(f"DEBUG: Intent='{intent}', Entities={entities}")

    context = ""
    
    # 2. ROUTING LOGIC
    if intent == "stress":
        config = infer_stress_config(question)
        
        if config["layers"]:
            print(f"DEBUG: Running Dynamic Stress Test: {config}")
            vector = StressVector(
                name="dynamic_user_chat_test",
                description=question,
                target_layers=config["layers"],
                severity=config["severity"],
                propagation_type=config["type"] 
            )
            
            result = run_stress_test(state, vector)
            context = result.dict()
        else:
            context = get_stress_context(state)

    elif intent == "structure":
        context = get_structure_context(state)

    elif intent == "change_impact":
        if entities["files"]:
            target_file = entities["files"][0] 
            context = get_change_impact_context(state, target_file)
        else:
            return "I understood you want to check change impact, but I couldn't identify which file you're asking about."

    elif intent == "code_lookup":
        if entities["files"]:
            context = get_code_context(state, entities["files"][0])
        else:
            return "Which file would you like me to look up?"

    else:
        context = "No specific repository context available for this query type."

    # 3. FINAL GENERATION
    prompt = answer_prompt(question, context)
    try:
        response = client.models.generate_content(
            model=CHAT_MODEL, 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"I encountered an error generating the final response: {str(e)}"