# app/analysis/graph_metrics.py
"""
Enhanced graph metrics computation with comprehensive statistics.
Provides all metrics needed for documentation generation and stress testing.
"""

from collections import defaultdict
from typing import Dict, List, Tuple


def compute_graph_metrics(dep_graph: dict) -> dict:
    """
    Compute comprehensive dependency graph metrics.
    
    Args:
        dep_graph: Dictionary mapping files to their dependencies
                  {file: [dep1, dep2, ...]}
    
    Returns:
        Dictionary with comprehensive metrics:
        - fan_in: How many files import each file
        - fan_out: How many files each file imports
        - hubs: Most imported files (backward compatible list)
        - hubs_with_counts: Full hub data with counts
        - hub_details: Detailed info for each hub
        - leaves: Files with no dependents
        - total_nodes: Total number of files
        - total_edges: Total number of dependencies
        - avg_fan_in: Average number of importers per file
        - avg_fan_out: Average number of imports per file
        - max_fan_in: Highest number of importers
        - max_fan_in_module: File with most importers
        - coupling_score: Overall coupling metric (0-1)
        - god_modules: Files with excessive dependencies (>15)
    """
    if not dep_graph:
        # Return empty structure if no dependencies
        return {
            "fan_in": {},
            "fan_out": {},
            "hubs": [],
            "hubs_with_counts": [],
            "hub_details": {},
            "leaves": [],
            "total_nodes": 0,
            "total_edges": 0,
            "avg_fan_in": 0.0,
            "avg_fan_out": 0.0,
            "max_fan_in": 0,
            "max_fan_in_module": None,
            "coupling_score": 0.0,
            "god_modules": [],
        }
    
    fan_in = defaultdict(int)
    fan_out = {}

    # Calculate fan-in and fan-out for each file
    for src, deps in dep_graph.items():
        fan_out[src] = len(deps)
        for d in deps:
            fan_in[d] += 1
    
    # Ensure all nodes have fan_out (even if 0)
    for node in dep_graph.keys():
        if node not in fan_out:
            fan_out[node] = 0

    # Get hubs (files with highest fan-in - most imported)
    hubs_with_counts = sorted(fan_in.items(), key=lambda x: x[1], reverse=True)
    
    # Get leaves (files that import others but nothing imports them)
    leaves = [n for n, out in fan_out.items() if out > 0 and fan_in[n] == 0]
    
    # Calculate statistics
    total_nodes = len(dep_graph)
    total_edges = sum(len(deps) for deps in dep_graph.values())
    
    # Average fan-in (how many files typically import a given file)
    avg_fan_in = sum(fan_in.values()) / total_nodes if total_nodes > 0 else 0.0
    
    # Average fan-out (how many files a typical file imports)
    avg_fan_out = sum(fan_out.values()) / total_nodes if total_nodes > 0 else 0.0
    
    # Get max fan-in (most depended-upon file)
    max_fan_in_entry = hubs_with_counts[0] if hubs_with_counts else (None, 0)
    max_fan_in_module = max_fan_in_entry[0]
    max_fan_in = max_fan_in_entry[1]
    
    # Extract just the file names for hubs (backward compatibility)
    hub_names = [h[0] for h in hubs_with_counts[:10]]
    
    # Build detailed hub information for top 20 hubs
    hub_details = {}
    for file, count in hubs_with_counts[:20]:
        hub_details[file] = {
            "fan_in": count,
            "fan_out": fan_out.get(file, 0),
            "blast_radius_pct": (count / total_nodes * 100) if total_nodes > 0 else 0.0,
            "is_hub": True,
        }
    
    # Calculate coupling score (0-1 scale, higher = more coupled)
    # Based on average fan-in relative to a "normal" threshold of 5
    coupling_score = min(avg_fan_in / 5.0, 1.0) if avg_fan_in > 0 else 0.0
    
    # Identify "god modules" (files with excessive dependencies)
    # These are high-risk single points of failure
    god_modules = [f for f, c in hubs_with_counts if c > 15][:5]
    
    return {
        # Core metrics
        "fan_in": dict(fan_in),
        "fan_out": fan_out,
        
        # Hubs and leaves
        "hubs": hub_names,  # Just file names (backward compatible)
        "hubs_with_counts": hubs_with_counts[:10],  # Tuples: [(file, count), ...]
        "hub_details": hub_details,  # Detailed dict for easy lookup
        "leaves": leaves[:10],
        
        # Statistics
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "avg_fan_in": round(avg_fan_in, 2),
        "avg_fan_out": round(avg_fan_out, 2),
        "max_fan_in": max_fan_in,
        "max_fan_in_module": max_fan_in_module,
        
        # Additional metrics
        "coupling_score": round(coupling_score, 2),
        "god_modules": god_modules,
    }


def calculate_blast_radius(dep_graph: dict, module: str) -> Dict:
    """
    Calculate how many files would be affected if a module changes.
    
    Args:
        dep_graph: Dependency graph
        module: File path to analyze
    
    Returns:
        {
            "direct_dependents": [list of files that import this],
            "blast_radius": number of affected files,
            "blast_radius_pct": percentage of codebase affected
        }
    """
    # Find all files that import this module
    direct_dependents = [
        src for src, deps in dep_graph.items()
        if module in deps
    ]
    
    total_files = len(dep_graph)
    blast_radius_pct = (len(direct_dependents) / total_files * 100) if total_files > 0 else 0.0
    
    return {
        "direct_dependents": direct_dependents,
        "blast_radius": len(direct_dependents),
        "blast_radius_pct": round(blast_radius_pct, 1),
    }