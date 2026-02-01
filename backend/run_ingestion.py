# run_ingestion.py
import asyncio
from app.graphs.ingestion_graph import build_ingestion_graph

async def main():
    graph = build_ingestion_graph()
    state = await graph.ainvoke({
        "repo_url": "https://github.com/SanchitKulkarni1/portfoliowebsite.git"
    })
    print(state['stats'])

asyncio.run(main())
