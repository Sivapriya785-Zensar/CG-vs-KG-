"""Turn a networkx subgraph into (a) LLM prompt text and (b) d3-ready JSON."""
import hashlib
import json

import networkx as nx


def graph_to_context_text(g: nx.DiGraph) -> str:
    if g.number_of_nodes() == 0:
        return "(no matching policy graph nodes found for this query)"

    lines = ["Relevant policy graph facts:"]
    for node_id, data in g.nodes(data=True):
        attrs = data.get("attrs", {})
        attrs_str = f" [{attrs}]" if attrs else ""
        tag = ""
        if data.get("is_evidence"):
            origin = attrs.get("origin", "this_session")
            origin_text = "this session" if origin == "this_session" else "a prior session"
            tag = f" (decision trace from {origin_text})"
        lines.append(f"- {data.get('type', 'Node')} '{data.get('label', node_id)}'{attrs_str}{tag}")

    lines.append("Relationships:")
    for src, dst, data in g.edges(data=True):
        src_label = g.nodes[src].get("label", src)
        dst_label = g.nodes[dst].get("label", dst)
        lines.append(f"- {src_label} --{data.get('relation')}--> {dst_label}")

    return "\n".join(lines)


def graph_to_json(g: nx.DiGraph, rejected_node_ids: list[str] | None = None, kg_full: nx.DiGraph | None = None) -> dict:
    nodes = []
    for node_id, data in g.nodes(data=True):
        attrs = data.get("attrs", {})
        nodes.append({
            "id": node_id,
            "type": data.get("type", "Node"),
            "label": data.get("label", node_id),
            "attrs": attrs,
            "is_seed": bool(data.get("is_seed")),
            "is_evidence": bool(data.get("is_evidence")),
            "origin": attrs.get("origin") if data.get("is_evidence") else None,
            "status": "active",
        })

    if rejected_node_ids and kg_full is not None:
        present = {n["id"] for n in nodes}
        for node_id in rejected_node_ids:
            if node_id in present or node_id not in kg_full.nodes:
                continue
            data = kg_full.nodes[node_id]
            nodes.append({
                "id": node_id,
                "type": data.get("type", "Node"),
                "label": data.get("label", node_id),
                "attrs": data.get("attrs", {}),
                "is_seed": False,
                "is_evidence": False,
                "status": "rejected",
            })

    links = [
        {"source": src, "target": dst, "relation": data.get("relation", "")}
        for src, dst, data in g.edges(data=True)
    ]
    return {"nodes": nodes, "links": links}


def graph_content_hash(g: nx.DiGraph) -> str:
    """Stable content hash of a subgraph's node/edge set -- used to make sure
    the opt-in answer cache only reuses an answer when the KG context that
    produced it is byte-identical, not just similar."""
    node_ids = sorted(g.nodes)
    edge_ids = sorted(f"{s}|{d}|{data.get('relation','')}" for s, d, data in g.edges(data=True))
    payload = json.dumps({"nodes": node_ids, "edges": edge_ids}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
