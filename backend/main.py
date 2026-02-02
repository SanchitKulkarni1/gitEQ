# main.py - FastAPI server for gitEQ
"""
FastAPI server exposing the gitEQ analysis pipeline and chatbot as REST endpoints.
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import uuid
import asyncio
import os
from datetime import datetime

# Import existing pipeline components
from app.graphs.ingestion_graph import build_ingestion_graph
from app.models.state import RepoState
from app.llm.chat.chat_engine import answer_question
from app.analysis.archetype_detection import detect_architecture
from app.stress.stress_models import RepoContext, TechStack
import google.generativeai as genai

# ============================================================================
# FastAPI App Configuration
# ============================================================================

app = FastAPI(
    title="gitEQ API",
    description="AI-powered GitHub repository analysis, documentation, and stress testing",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# In-Memory Storage (Replace with database in production)
# ============================================================================

analyses_store: Dict[str, dict] = {}
chat_history: Dict[str, List[dict]] = {}

# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    repo_url: str
    api_key: str  # User's Gemini API key (BYOK)

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str  # "pending", "processing", "completed", "failed"
    repo_url: str
    created_at: str
    result: Optional[dict] = None
    error: Optional[str] = None

class ChatRequest(BaseModel):
    analysis_id: str
    question: str
    api_key: str  # User's Gemini API key (BYOK)

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
# Background Task: Run Analysis Pipeline
# ============================================================================

async def run_analysis_pipeline(analysis_id: str, repo_url: str, api_key: str):
    """
    Runs the full analysis pipeline in the background.
    Updates analyses_store with progress and results.
    Uses user-provided Gemini API key (BYOK).
    """
    try:
        analyses_store[analysis_id]["status"] = "processing"
        
        # Configure Gemini with user's API key
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key)
        
        # Build and run the LangGraph ingestion pipeline
        graph = build_ingestion_graph()
        raw_state = await graph.ainvoke({"repo_url": repo_url})
        
        # Convert to Pydantic for easier serialization
        state = RepoState(**raw_state)
        
        # Detect architecture if not already done
        if not state.repo_context:
            file_list = list(state.files_content.keys())
            arch_info = detect_architecture(file_list, state.symbols, state.files_content)
            state.repo_context = RepoContext(
                architecture_type=arch_info['architecture_type'],
                tech_stack=TechStack(**arch_info['tech_stack']),
                total_files=len(file_list)
            )
        
        # Serialize the state for storage and frontend consumption
        result = {
            "owner": state.owner,
            "repo": state.repo,
            "branch": state.branch,
            "archetype": state.archetype,
            "stats": state.stats,
            "layers": state.layers,
            "graph_metrics": state.graph_metrics,
            "architecture_hypotheses": state.architecture_hypotheses,
            "assumptions": state.assumptions,
            "stress_results": state.stress_results,
            "generated_docs": state.generated_docs,
            "dependency_graph": {
                "nodes": list(state.dependency_graph.keys()),
                "edges": state.dependency_graph
            },
            "repo_context": {
                "architecture_type": state.repo_context.architecture_type.value if state.repo_context else None,
                "tech_stack": state.repo_context.tech_stack.dict() if state.repo_context else None,
                "total_files": state.repo_context.total_files if state.repo_context else 0
            }
        }
        
        # Store the full state for chat functionality
        analyses_store[analysis_id]["_state"] = state
        analyses_store[analysis_id]["result"] = result
        analyses_store[analysis_id]["status"] = "completed"
        
    except Exception as e:
        analyses_store[analysis_id]["status"] = "failed"
        analyses_store[analysis_id]["error"] = str(e)

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "gitEQ API", "version": "1.0.0"}


@app.post("/api/analyze", response_model=AnalysisSummary)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Start a new repository analysis.
    Returns immediately with an analysis_id, processing happens in background.
    """
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    analyses_store[analysis_id] = {
        "analysis_id": analysis_id,
        "repo_url": request.repo_url,
        "status": "pending",
        "created_at": created_at,
        "result": None,
        "error": None,
        "_state": None
    }
    
    # Store the API key for the analysis (for chat later)
    analyses_store[analysis_id]["api_key"] = request.api_key
    
    # Start background processing with user's API key
    background_tasks.add_task(run_analysis_pipeline, analysis_id, request.repo_url, request.api_key)
    
    return AnalysisSummary(
        analysis_id=analysis_id,
        repo_url=request.repo_url,
        status="pending",
        created_at=created_at
    )


@app.get("/api/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str):
    """Get the status and results of an analysis."""
    if analysis_id not in analyses_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    data = analyses_store[analysis_id]
    return AnalysisResponse(
        analysis_id=data["analysis_id"],
        status=data["status"],
        repo_url=data["repo_url"],
        created_at=data["created_at"],
        result=data["result"],
        error=data["error"]
    )


@app.get("/api/analyses", response_model=List[AnalysisSummary])
async def list_analyses():
    """List all analyses (most recent first)."""
    summaries = []
    for analysis_id, data in sorted(
        analyses_store.items(), 
        key=lambda x: x[1]["created_at"], 
        reverse=True
    ):
        summary = AnalysisSummary(
            analysis_id=analysis_id,
            repo_url=data["repo_url"],
            status=data["status"],
            created_at=data["created_at"],
            owner=data.get("result", {}).get("owner") if data["result"] else None,
            repo=data.get("result", {}).get("repo") if data["result"] else None,
            archetype=data.get("result", {}).get("archetype") if data["result"] else None
        )
        summaries.append(summary)
    return summaries


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_repo(request: ChatRequest):
    """
    Ask a question about a previously analyzed repository.
    Uses the AI chat engine for intelligent responses.
    """
    if request.analysis_id not in analyses_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses_store[request.analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis not ready. Status: {analysis['status']}"
        )
    
    state = analysis.get("_state")
    if not state:
        raise HTTPException(status_code=500, detail="Analysis state not available")
    
    # Configure Gemini with user's API key for this request
    os.environ["GOOGLE_API_KEY"] = request.api_key
    genai.configure(api_key=request.api_key)
    
    # Use the existing chat engine
    from app.llm.chat.chat_engine import classify_intent_fast
    
    answer = answer_question(state, request.question)
    intent = classify_intent_fast(request.question)
    timestamp = datetime.utcnow().isoformat()
    
    # Store in chat history
    if request.analysis_id not in chat_history:
        chat_history[request.analysis_id] = []
    
    chat_history[request.analysis_id].append({
        "role": "user",
        "content": request.question,
        "timestamp": timestamp
    })
    chat_history[request.analysis_id].append({
        "role": "assistant",
        "content": answer,
        "intent": intent,
        "timestamp": timestamp
    })
    
    return ChatResponse(
        answer=answer,
        intent=intent,
        timestamp=timestamp
    )


@app.get("/api/chat/history/{analysis_id}")
async def get_chat_history(analysis_id: str):
    """Get chat history for an analysis."""
    if analysis_id not in analyses_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {"history": chat_history.get(analysis_id, [])}


@app.get("/api/docs/{analysis_id}")
async def get_documentation(analysis_id: str):
    """Get the generated documentation for an analysis."""
    if analysis_id not in analyses_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses_store[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis not ready. Status: {analysis['status']}"
        )
    
    docs = analysis.get("result", {}).get("generated_docs", {})
    return {"documentation": docs}


@app.get("/api/stress/{analysis_id}")
async def get_stress_results(analysis_id: str):
    """Get stress test results for an analysis."""
    if analysis_id not in analyses_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses_store[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis not ready. Status: {analysis['status']}"
        )
    
    stress_results = analysis.get("result", {}).get("stress_results", [])
    return {"stress_results": stress_results}


@app.get("/api/graph/{analysis_id}")
async def get_dependency_graph(analysis_id: str):
    """Get the dependency graph data for visualization."""
    if analysis_id not in analyses_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses_store[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis not ready. Status: {analysis['status']}"
        )
    
    result = analysis.get("result", {})
    
    # Format for frontend graph visualization (React Flow format)
    dep_graph = result.get("dependency_graph", {}).get("edges", {})
    graph_metrics = result.get("graph_metrics", {})
    layers = result.get("layers", {})
    
    # Create nodes with positions and styling
    nodes = []
    edges = []
    
    for i, (file_path, imports) in enumerate(dep_graph.items()):
        # Determine layer for coloring
        layer = "unknown"
        for layer_name, files in layers.items():
            if file_path in files:
                layer = layer_name
                break
        
        # Calculate fan-in for node size
        fan_in = sum(1 for deps in dep_graph.values() if file_path in deps)
        
        nodes.append({
            "id": file_path,
            "label": file_path.split("/")[-1],  # Short name
            "full_path": file_path,
            "layer": layer,
            "fan_in": fan_in,
            "fan_out": len(imports),
            "position": {"x": (i % 10) * 200, "y": (i // 10) * 150}
        })
        
        # Create edges
        for imported_module in imports:
            edges.append({
                "source": file_path,
                "target": imported_module,
                "id": f"{file_path}->{imported_module}"
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "metrics": graph_metrics
    }


# ============================================================================
# Run with: uvicorn main:app --reload --port 8000
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
