# run_ingestion.py
import asyncio
from app.graphs.ingestion_graph import build_ingestion_graph
from app.models.state import RepoState


async def main():
    graph = build_ingestion_graph()

    raw_state = await graph.ainvoke({
        "repo_url": "https://github.com/SanchitKulkarni1/portfoliowebsite.git"
    })

    # ✅ Convert dict → RepoState
    state = RepoState(**raw_state)

    # 1️⃣ Stats
    print("\n=== STATS ===")
    for k, v in state.stats.items():
        print(f"{k}: {v}")

    # 2️⃣ Files fetched
    print("\n=== FILES FETCHED ===")
    print(f"Total files with content: {len(state.files_content)}")
    print(list(state.files_content.keys())[:10])

    # 3️⃣ Symbols extracted
    print("\n=== SYMBOLS (sample) ===")
    for sym in state.symbols[:10]:
        print(f"{sym.kind:<10} | {sym.name:<30} | {sym.file}")

    # 4️⃣ Dependency graph sanity check
    print("\n=== DEPENDENCY GRAPH (sample) ===")
    for src, deps in list(state.dependency_graph.items())[:5]:
        print(f"{src} -> {deps}")

    # 5️⃣ Architecture inference sanity
    print("\n=== ARCHETYPE ===")
    print(state.archetype)

    print("\n=== LAYERS ===")
    for layer, files in state.layers.items():
        print(layer, ":", len(files))

    print("\n=== ASSUMPTIONS ===")
    for a in state.assumptions:
        print("-", a)


asyncio.run(main())
