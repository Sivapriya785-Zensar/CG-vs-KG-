"""
Condition A: the static Knowledge Graph.

Built once, at import time, from the design-time policy dataset. Traversed
as-is at runtime -- the graph structure never changes between queries; only
which seed nodes a query activates changes.
"""
import networkx as nx

from kg_cg_experiment.data.policy_dataset import NODES, EDGES

_KG = None


def build_static_kg() -> nx.DiGraph:
    """Build (or return the cached) static policy knowledge graph."""
    global _KG
    if _KG is not None:
        return _KG

    g = nx.DiGraph()
    for node in NODES:
        g.add_node(
            node["id"],
            type=node["type"],
            label=node["label"],
            aliases=node.get("aliases", []),
            attrs=node.get("attrs", {}),
        )
    for src, dst, relation in EDGES:
        g.add_edge(src, dst, relation=relation)

    _KG = g
    return g
