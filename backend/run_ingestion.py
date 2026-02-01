import asyncio
import time
from app.graphs.ingestion_graph import build_ingestion_graph
from app.models.state import RepoState

# Imports
from app.llm.docs.docs_generator import generate_docs_sectionwise
from app.llm.chat.chat_engine import answer_question
from app.analysis.archetype_detection import detect_architecture
from app.stress.stress_models import RepoContext, TechStack

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
    # PHASE 1.5: ARCHITECTURE DETECTION
    # =========================================================================
    print("\n🧠 DETECTING ARCHITECTURE...")
    
    # ---------------------------------------------------------
    # 🚨 FIX: Extract file list from dictionary keys
    # ---------------------------------------------------------
    file_list = list(state.files_content.keys())

    arch_info = detect_architecture(
        file_list,           # <--- CHANGED from state.files to file_list
        state.symbols, 
        state.files_content
    )
    
    # Create the Context Object
    repo_context = RepoContext(
        architecture_type=arch_info['architecture_type'],
        tech_stack=TechStack(**arch_info['tech_stack']),
        total_files=len(file_list)
    )
    
    # Save to state
    state.repo_context = repo_context 
    
    print(f"   👉 Type: {repo_context.architecture_type.value}")
    print(f"   👉 Framework: {repo_context.tech_stack.framework}")
    print(f"   👉 Language: {repo_context.tech_stack.language}")

    # =========================================================================
    # PHASE 2: DOCUMENTATION GENERATION
    # =========================================================================
    print("\n📝 STARTING PIPELINE: DOCUMENTATION")
    
    docs_output = generate_docs_sectionwise(state)
    state.generated_docs = docs_output["docs"] 
    
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
    # SAFETY PAUSE
    # =========================================================================
    print("⏳ Cooling down for 30 seconds to reset Quota...")
    time.sleep(30) 

    # =========================================================================
    # PHASE 3: STRESS TEST
    # =========================================================================
    print("\n🤖 STARTING PIPELINE: CHATBOT STRESS TEST")
    
    user_question_1 = "What will happen if we get a sudden spike of 5000 concurrent users on the landing page?"
    print(f"\n❓ User Question: '{user_question_1}'")
    
    response_1 = answer_question(state, user_question_1)
    print(f"💡 Chatbot Answer:\n{response_1}")

    user_question_2 = "What happens if the API layer crashes completely?"
    print(f"\n❓ User Question: '{user_question_2}'")
    
    response_2 = answer_question(state, user_question_2)
    print(f"💡 Chatbot Answer:\n{response_2}")

if __name__ == "__main__":
    asyncio.run(main())