from backend.graphs.ingestion_graph import build_ingestion_graph


ingestion_graph = build_ingestion_graph()

def run_repo_analysis(repo_url: str):
    initial_state = {
        "repo_url": repo_url
    }

    final_state = ingestion_graph.invoke(initial_state)
    return final_state
