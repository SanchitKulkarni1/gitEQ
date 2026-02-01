# app/analysis/graph_metrics.py
from collections import defaultdict

def compute_graph_metrics(dep_graph: dict):
    fan_in = defaultdict(int)
    fan_out = {}

    for src, deps in dep_graph.items():
        fan_out[src] = len(deps)
        for d in deps:
            fan_in[d] += 1

    hubs = sorted(fan_in.items(), key=lambda x: x[1], reverse=True)
    leaves = [n for n, out in fan_out.items() if out > 0 and fan_in[n] == 0]

    return {
        "fan_in": dict(fan_in),
        "fan_out": fan_out,
        "hubs": hubs[:10],
        "leaves": leaves[:10],
    }
