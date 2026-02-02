# main.py - FastAPI server for gitEQ
"""
FastAPI server exposing the gitEQ analysis pipeline and chatbot as REST endpoints.
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import uuid
import os
from datetime import datetime

# Import existing pipeline components
from app.graphs.ingestion_graph import build_ingestion_graph
from app.models.state import RepoState
from app.llm.chat.chat_engine import answer_question
from app.analysis.archetype_detection import detect_architecture
from app.stress.stress_models import RepoContext, TechStack

# Latest Unified Google GenAI SDK
from google import genai

# ============================================================================
# FastAPI App Configuration
# ============================================================================

app = FastAPI(
    title="gitEQ API",
    description="AI-powered GitHub repository analysis, documentation, and stress testing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Storage
analyses_store: Dict[str, dict] = {}
chat_history: Dict[str, List[dict]] = {}

# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    repo_url: str
    api_key: str 

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str 
    repo_url: str
    created_at: str
    result: Optional[dict] = None
    error: Optional[str] = None

class ChatRequest(BaseModel):
    analysis_id: str
    question: str
    api_key: str

class ChatResponse(BaseModel):
    answer: str
    intent: str
    timestamp: str

class AnalysisSummary(BaseModel):
    analysis_id: str
    repo_url: str
    status: str
    created_at: str
    owner: Optional[str] = None
    repo: Optional[str] = None
    archetype: Optional[str] = None

# ============================================================================
# Transformation Logic
# ============================================================================

SECTION_CONFIG = {
    "overview": {"title": "Overview", "icon": "📋", "order": 0},
    "architecture": {"title": "Architecture", "icon": "🏗️", "order": 1},
    "core_modules": {"title": "Core Modules", "icon": "⚙️", "order": 2},
    "system_boundaries": {"title": "System Boundaries", "icon": "🔒", "order": 3},
    "assumptions": {"title": "Assumptions", "icon": "💡", "order": 4},
    "stress_analysis": {"title": "Stress Analysis", "icon": "⚡", "order": 5},
}

def transform_result_for_frontend(raw_result: dict) -> dict:
    if not raw_result:
        return None
    
    stats = raw_result.get("stats", {})
    repository = {
        "owner": raw_result.get("owner", ""),
        "name": raw_result.get("repo", ""),
        "branch": raw_result.get("branch", "main"),
        "architecture": raw_result.get("archetype", "Unknown"),
        "files_analyzed": stats.get("files_loaded", 0),
        "symbols_extracted": stats.get("symbols_extracted", 0),
    }
    
    generated_docs = raw_result.get("generated_docs", {})
    sections = []
    
    for section_id, config in sorted(SECTION_CONFIG.items(), key=lambda x: x[1]["order"]):
        content = generated_docs.get(section_id, "")
        if content:
            # Skip stress_analysis if content indicates it's not applicable
            if section_id == "stress_analysis":
                content_lower = content.lower()
                if "not applicable" in content_lower or "is_applicable: false" in content_lower:
                    continue
            
            sections.append({
                "id": section_id,
                "title": config["title"],
                "icon": config["icon"],
                "content": content,
            })
    
    full_markdown_parts = [f"# {s['icon']} {s['title']}\n\n{s['content']}" for s in sections]
    full_markdown = "\n\n---\n\n".join(full_markdown_parts)
    
    return {
        "repository": repository,
        "sections": sections,
        "full_markdown": full_markdown,
    }

# ============================================================================
# Background Task: Run Analysis Pipeline
# ============================================================================

async def run_analysis_pipeline(analysis_id: str, repo_url: str, api_key: str):
    try:
        analyses_store[analysis_id]["status"] = "processing"
        
        # Set API key in environment for internal modules to use
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Build and run the LangGraph ingestion pipeline
        graph = build_ingestion_graph()
        raw_state = await graph.ainvoke({"repo_url": repo_url})
        
        state = RepoState(**raw_state)
        
        if not state.repo_context:
            file_list = list(state.files_content.keys())
            arch_info = detect_architecture(file_list, state.symbols, state.files_content)
            state.repo_context = RepoContext(
                architecture_type=arch_info['architecture_type'],
                tech_stack=TechStack(**arch_info['tech_stack']),
                total_files=len(file_list)
            )
        
        result = {
            "owner": state.owner,
            "repo": state.repo,
            "branch": state.branch,
            "archetype": state.archetype,
            "stats": state.stats,
            "layers": state.layers,
            "graph_metrics": state.graph_metrics,
            "generated_docs": state.generated_docs,
            "stress_results": state.stress_results,
            "dependency_graph": {
                "nodes": list(state.dependency_graph.keys()),
                "edges": state.dependency_graph
            }
        }
        
        analyses_store[analysis_id].update({
            "_state": state,
            "result": result,
            "status": "completed"
        })
        
    except Exception as e:
        analyses_store[analysis_id].update({
            "status": "failed",
            "error": str(e)
        })

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {"status": "ok", "service": "gitEQ API"}

@app.post("/api/analyze", response_model=AnalysisSummary)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    analyses_store[analysis_id] = {
        "analysis_id": analysis_id,
        "repo_url": request.repo_url,
        "status": "pending",
        "created_at": created_at,
        "api_key": request.api_key, # Store for chat requests
        "result": None,
        "error": None,
        "_state": None
    }
    
    background_tasks.add_task(run_analysis_pipeline, analysis_id, request.repo_url, request.api_key)
    
    return AnalysisSummary(
        analysis_id=analysis_id,
        repo_url=request.repo_url,
        status="pending",
        created_at=created_at
    )

@app.get("/api/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str):
    if analysis_id not in analyses_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    data = analyses_store[analysis_id]
    result = data["result"]
    
    if data["status"] == "completed" and result:
        result = transform_result_for_frontend(result)
    
    return AnalysisResponse(
        analysis_id=data["analysis_id"],
        status=data["status"],
        repo_url=data["repo_url"],
        created_at=data["created_at"],
        result=result,
        error=data["error"]
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_repo(request: ChatRequest):
    if request.analysis_id not in analyses_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses_store[request.analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not ready")
    
    state = analysis.get("_state")
    if not state:
        raise HTTPException(status_code=500, detail="Analysis state not available")
    
    # Set API key in environment for internal modules
    os.environ["GEMINI_API_KEY"] = request.api_key
    
    from app.llm.chat.chat_engine import classify_intent_fast
    
    answer = answer_question(state, request.question)
    intent = classify_intent_fast(request.question)
    timestamp = datetime.utcnow().isoformat()
    
    history = chat_history.setdefault(request.analysis_id, [])
    history.append({"role": "user", "content": request.question, "timestamp": timestamp})
    history.append({"role": "assistant", "content": answer, "intent": intent, "timestamp": timestamp})
    
    return ChatResponse(answer=answer, intent=intent, timestamp=timestamp)

@app.get("/api/graph/{analysis_id}")
async def get_dependency_graph(analysis_id: str):
    if analysis_id not in analyses_store or analyses_store[analysis_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="Analysis not found or incomplete")
    
    res = analyses_store[analysis_id]["result"]
    dep_graph = res.get("dependency_graph", {}).get("edges", {})
    layers = res.get("layers", {})
    
    nodes, edges = [], []
    for i, (file_path, imports) in enumerate(dep_graph.items()):
        layer = next((l for l, files in layers.items() if file_path in files), "unknown")
        nodes.append({
            "id": file_path, 
            "label": file_path.split("/")[-1],
            "layer": layer, 
            "position": {"x": (i % 10) * 200, "y": (i // 10) * 150}
        })
        for imp in imports:
            edges.append({"source": file_path, "target": imp, "id": f"{file_path}-{imp}"})
            
    return {"nodes": nodes, "edges": edges, "metrics": res.get("graph_metrics", {})}

if __name__ == "__main__":
    import uvicorn
    # Killing the port 8000 process before starting is recommended if you see Address already in use
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)