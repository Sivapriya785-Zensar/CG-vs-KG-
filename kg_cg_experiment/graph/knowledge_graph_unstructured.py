"""
Builds the KG for the unstructured-data-source track from the extraction
output (data/extracted_kg.json) instead of data/policy_dataset.py's
hand-authored NODES/EDGES. Same networkx.DiGraph shape as
graph/knowledge_graph.py's build_static_kg(), so graph/seed_matching.py,
graph/context_graph.py, and graph/serialize.py all work against it
unchanged -- only the source of the graph differs, never the mechanics that
traverse or query it.

Requires graph/extract_kg_from_text.py to have been run first (its own
docstring explains why that's a one-time step, not something done per
query). Fails loudly with instructions if the extraction file is missing --
never silently falls back to the hand-authored graph, which would make the
"unstructured source" comparison meaningless without you knowing it.
"""
import json
from pathlib import Path

import networkx as nx

EXTRACTED_JSON_PATH = Path(__file__).resolve().parents[1] / "data" / "extracted_kg.json"

_KG = None


def build_kg_from_unstructured() -> nx.DiGraph:
    global _KG
    if _KG is not None:
        return _KG

    if not EXTRACTED_JSON_PATH.exists():
        raise FileNotFoundError(
            f"{EXTRACTED_JSON_PATH} doesn't exist yet. Run the one-time extraction first:\n"
            f"  python -m kg_cg_experiment.graph.extract_kg_from_text"
        )

    data = json.loads(EXTRACTED_JSON_PATH.read_text(encoding="utf-8"))

    g = nx.DiGraph()
    for node in data["nodes"]:
        g.add_node(
            node["id"],
            type=node["type"],
            label=node.get("label", node["id"]),
            aliases=[a.lower() for a in node.get("aliases", [])],
            attrs=node.get("attrs", {}),
        )
    for edge in data["edges"]:
        if edge["source"] not in g.nodes or edge["target"] not in g.nodes:
            continue  # extraction referenced an id it didn't also define as a node -- skip rather than crash
        g.add_edge(edge["source"], edge["target"], relation=edge.get("relation", ""))

    _KG = g
    return g
