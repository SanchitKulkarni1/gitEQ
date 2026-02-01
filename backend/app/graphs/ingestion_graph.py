# app/graphs/ingestion_graph.py
from langgraph.graph import StateGraph
from app.models.state import RepoState
from app.graphs.ingestion_nodes import (
    parse_repo,
    resolve_branch,
    load_tree,
    apply_glob_filter,
    fetch_contents_node,
    universal_ast_node,
    dependency_graph_node,
    architecture_inference_node,
    stress_test_node,
)


def build_ingestion_graph():
    g = StateGraph(RepoState)

    g.add_node("parse_repo", parse_repo)
    g.add_node("resolve_branch", resolve_branch)
    g.add_node("load_tree", load_tree)
    g.add_node("apply_glob_filter", apply_glob_filter)
    g.add_node("fetch_contents_node", fetch_contents_node)
    g.add_node("universal_ast_node", universal_ast_node)
    g.add_node("dependency_graph_node", dependency_graph_node)
    g.add_node("architecture_inference_node", architecture_inference_node)
    g.add_node("stress_test_node", stress_test_node)

    g.set_entry_point("parse_repo")
    g.add_edge("parse_repo", "resolve_branch")
    g.add_edge("resolve_branch", "load_tree")
    g.add_edge("load_tree", "apply_glob_filter")
    g.add_edge("apply_glob_filter", "fetch_contents_node")
    g.add_edge("fetch_contents_node", "universal_ast_node")
    g.add_edge("universal_ast_node", "dependency_graph_node")
    g.add_edge("dependency_graph_node", "architecture_inference_node")
    g.add_edge("architecture_inference_node", "stress_test_node")

    g.set_finish_point("stress_test_node")
    return g.compile()
