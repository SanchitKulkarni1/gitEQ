# app/chat/intent_classifier.py
from app.llm.gemini_client import client # Using your updated client
from google.genai import types

GEN_CONFIG = types.GenerateContentConfig(temperature=0.0)

def classify_intent(question: str) -> str:
    prompt = f"""
    Classify the user question into ONE category:
    [structure, change_impact, architecture, stress, code_lookup, unknown]
    
    Question: {question}
    
    Return ONLY the category name (lowercase).
    """
    response = client.models.generate_content(
        model="gemini-1.5-flash", contents=prompt, config=GEN_CONFIG
    )
    return response.text.strip().lower()

def extract_entities(question: str) -> dict:
    """
    Extracts relevant file paths, layer names, or component names.
    Parallelizing this saves time vs. doing it after intent.
    """
    prompt = f"""
    Analyze the question and extract targeted entities.
    Return a JSON with:
    - 'files': list of file paths mentioned (e.g. 'app/main.py', 'auth.py')
    - 'layers': list of architectural layers mentioned (e.g. 'ui', 'database')
    
    Question: {question}
    
    Return ONLY valid JSON.
    """
    # In a real app, ensure you request JSON mode if available
    response = client.models.generate_content(
        model="gemini-1.5-flash", contents=prompt, config=GEN_CONFIG
    )
    
    # Simple clean-up to ensure we get a dict
    try:
        import json
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except:
        return {"files": [], "layers": []}