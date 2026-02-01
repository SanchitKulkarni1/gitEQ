def get_structure_context(state):
    return {
        "overview": state.generated_docs.get("overview"),
        "architecture": state.generated_docs.get("architecture"),
        "layers": state.layers,
    }

def get_change_impact_context(state, file_path: str):
    dependents = [
        src for src, deps in state.dependency_graph.items()
        if file_path in deps
    ]

    return {
        "file": file_path,
        "direct_dependents": dependents,
        "fan_in": len(dependents),
        "is_core_module": file_path in state.graph_metrics.get("hubs", []),
    }

def get_code_context(state, path):
    return state.files_content.get(path, "File not found")

def get_stress_context(state):
    return state.stress_results

def answer_prompt(question, context):
    return f"""
You are an engineering assistant answering questions about a GitHub repository.

Rules:
- Answer ONLY using the provided context
- Do NOT invent details
- If the answer is not in context, say so explicitly
- Reference files or modules when relevant

User question:
{question}

Context:
{context}

Answer clearly and concisely.
"""
