import asyncio
import time
from app.graphs.ingestion_graph import build_ingestion_graph
from app.models.state import RepoState

# CORRECTED IMPORTS (Based on your actual folder structure)
from app.llm.docs.docs_generator import generate_docs_sectionwise
from app.llm.chat.chat_engine import answer_question

async def main():
    # =========================================================================
    # PHASE 1: INGESTION
    # =========================================================================
    print("\n🚀 STARTING PIPELINE: INGESTION")
    graph = build_ingestion_graph()
    
    # Run the LangGraph ingestion pipeline
    raw_state = await graph.ainvoke({
        "repo_url": "https://github.com/SanchitKulkarni1/portfoliowebsite.git"
    })
    
    # Convert dictionary back to Pydantic object
    state = RepoState(**raw_state)
    print(f"✅ Ingestion Complete. {state.stats.get('files_selected', 0)} files analyzed.")

    # =========================================================================
    # PHASE 2: DOCUMENTATION GENERATION (Parallel)
    # =========================================================================
    print("\n📝 STARTING PIPELINE: DOCUMENTATION")
    
    # This runs the LLM calls in parallel
    docs_output = generate_docs_sectionwise(state)
    state.generated_docs = docs_output["docs"] 
    
    # --- UPDATED PRINT LOGIC: SHOW CONTENT ---
    print("\n📄 GENERATED DOCUMENTATION CONTENT:\n")
    for section, content in state.generated_docs.items():
        print(f"--- [ SECTION: {section.upper()} ] " + "-"*40)
        print(content)
        print("-" * 60 + "\n")
        
    if docs_output["warnings"]:
        print("\n⚠️  Warnings during generation:")
        for section, warns in docs_output["warnings"].items():
            print(f"  [{section}]: {warns}")

    # =========================================================================
    # SAFETY PAUSE (Prevent 429 Rate Limit Crash)
    # =========================================================================
    print("⏳ Cooling down for 30 seconds to reset Quota...")
    time.sleep(30) 

    # =========================================================================
    # PHASE 3: STRESS TEST (CHATBOT SIMULATION)
    # =========================================================================
    print("\n🤖 STARTING PIPELINE: CHATBOT STRESS TEST")
    
    # Scenario 1: Traffic Load
    user_question_1 = "What will happen if we get a sudden spike of 5000 concurrent users on the landing page?"
    print(f"\n❓ User Question: '{user_question_1}'")
    
    response_1 = answer_question(state, user_question_1)
    print(f"💡 Chatbot Answer:\n{response_1}")

    # Scenario 2: Dependency Failure
    user_question_2 = "What happens if the API layer crashes completely?"
    print(f"\n❓ User Question: '{user_question_2}'")
    
    response_2 = answer_question(state, user_question_2)
    print(f"💡 Chatbot Answer:\n{response_2}")

if __name__ == "__main__":
    asyncio.run(main())