# app/chat/chat_engine.py
import concurrent.futures
from app.llm.chat.intent_classifier import classify_intent, extract_entities
from app.llm.chat.retrieval import (
    get_structure_context,
    get_change_impact_context,
    get_stress_context,
    get_code_context,
    answer_prompt
)
from app.llm.gemini_client import client
from app.stress.stress_engine import run_stress_test # Connect your new engine!
from app.stress.stress_models import StressVector

def parallel_comprehension(question: str):
    """
    Runs Intent Classification and Entity Extraction simultaneously.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks at once
        intent_future = executor.submit(classify_intent, question)
        entities_future = executor.submit(extract_entities, question)
        
        # Wait for both to finish
        intent = intent_future.result()
        entities = entities_future.result()
        
    return intent, entities

def answer_question(state, question: str):
    # 1. PARALLEL COMPREHENSION STEP
    intent, entities = parallel_comprehension(question)
    
    print(f"DEBUG: Intent='{intent}', Entities={entities}")

    context = ""
    
    # 2. ROUTING LOGIC
    if intent == "structure":
        context = get_structure_context(state)

    elif intent == "change_impact":
        # FIX: Use the extracted entity instead of split()
        if entities["files"]:
            # Pick the best match from the extracted files
            target_file = entities["files"][0] 
            context = get_change_impact_context(state, target_file)
        else:
            return "I understood you want to check change impact, but I couldn't identify which file you're asking about."

    elif intent == "stress":
        # ADVANCED: If they mention a specific layer, run a DYNAMIC stress test
        if entities["layers"]:
            # Create a dynamic vector based on user chat
            vector = StressVector(
                name="user_manual_test",
                description=question,
                target_layers=entities["layers"], # LLM extracted "database" or "ui"
                severity=0.8
            )
            # Run the engine we built earlier!
            result = run_stress_test(state, vector)
            context = result.dict()
        else:
            # Otherwise return the pre-calculated results
            context = get_stress_context(state)

    elif intent == "code_lookup":
        if entities["files"]:
            context = get_code_context(state, entities["files"][0])
        else:
            return "Which file would you like me to look up?"

    else:
        return "I'm not sure how to answer that with the current data."

    # 3. FINAL GENERATION (Single Thread)
    prompt = answer_prompt(question, context)
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents=prompt
    )
    return response.text.strip()