# run_ingestion.py
import asyncio
from app.graphs.ingestion_graph import build_ingestion_graph

async def main():
    graph = build_ingestion_graph()
    state = await graph.ainvoke({
        "repo_url": "https://github.com/SanchitKulkarni1/portfoliowebsite.git"
    })

    print(state["stats"]) 

    path = "src/main.tsx"
    # FIXED: Use dictionary access here
    if path in state["files_content"]:
        print(state["files_content"][path])
    else:
        print(f"{path} was not fetched. Available files:")
        # FIXED: Use dictionary access here
        print(list(state["files_content"].keys()))

asyncio.run(main())
