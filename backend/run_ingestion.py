# run_ingestion.py
import asyncio
from app.graphs.ingestion_graph import build_ingestion_graph


async def main():
    graph = build_ingestion_graph()

    # The graph returns a plain dictionary
    state = await graph.ainvoke({
        "repo_url": "https://github.com/SanchitKulkarni1/portfoliowebsite.git"
    })

    # 1️⃣ Always start with stats
    print("\n=== STATS ===")
    # Changed .stats to ["stats"]
    for k, v in state["stats"].items():
        print(f"{k}: {v}")

    # 2️⃣ Files fetched
    print("\n=== FILES FETCHED ===")
    # Changed .files_content to ["files_content"]
    print(f"Total files with content: {len(state['files_content'])}")
    print(list(state["files_content"].keys())[:10])  # sample

    # 3️⃣ Symbols extracted (AST result)
    print("\n=== SYMBOLS (sample) ===")
    # Changed .symbols to ["symbols"]
    # Note: If 'sym' itself is an object (from your Pydantic model), use dot notation on it.
    # But if 'symbols' is a list of dicts, use sym['kind']
    for sym in state.get("symbols", [])[:10]:
        print(
            f"{sym.kind:<10} | {sym.name:<30} | {sym.file}"
        )

    # 4️⃣ Dependency graph sanity check
    print("\n=== DEPENDENCY GRAPH (sample) ===")
    # Changed .dependency_graph to ["dependency_graph"]
    for src, deps in list(state.get("dependency_graph", {}).items())[:5]:
        print(f"{src} -> {deps}")


asyncio.run(main())