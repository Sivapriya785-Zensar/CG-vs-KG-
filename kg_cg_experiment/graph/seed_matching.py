"""
Deterministic query -> seed node matching, shared by both conditions.

Pure substring/alias matching against the static KG's node aliases. No LLM,
no fuzzy scoring -- this keeps traversal reproducible and keeps the "same
graph regardless of query" property honest: the graph never changes, only
the deterministic activation of it does.
"""
import networkx as nx


def match_seed_nodes(query: str, g: nx.DiGraph) -> list[str]:
    """Leftmost-longest substring matching: find every alias occurrence,
    then greedily accept matches left-to-right, taking the longest match
    starting at the earliest unclaimed position and skipping anything that
    overlaps an already-accepted span. This resolves cases like "basic
    economy ticket", where "basic economy" (starts earlier) must win over
    the coincidentally-overlapping "economy ticket" alias of a different
    node (which starts mid-word, one token later)."""
    q = query.lower()
    occurrences = []  # (start, end, node_id)
    for node_id, data in g.nodes(data=True):
        for alias in data.get("aliases", []):
            start = 0
            while True:
                idx = q.find(alias, start)
                if idx == -1:
                    break
                occurrences.append((idx, idx + len(alias), node_id))
                start = idx + 1

    occurrences.sort(key=lambda o: (o[0], -(o[1] - o[0])))

    matched: list[str] = []
    seen_nodes = set()
    next_free = 0
    for start, end, node_id in occurrences:
        if start < next_free:
            continue
        next_free = end
        if node_id not in seen_nodes:
            matched.append(node_id)
            seen_nodes.add(node_id)
    return matched


def expand_around(g: nx.DiGraph, seeds: list[str], hops: int) -> set[str]:
    """BFS both directions, `hops` steps, from `seeds`. Pure structural
    expansion of the static graph -- used both for query-seeded traversal
    (Condition A) and for expanding the neighborhood of a fail-fast-confirmed
    evidence-linked node (Condition B), since once a link to a specific KG
    node is confirmed, walking its immediate policy neighborhood is no
    longer a guess."""
    reached = set(seeds)
    frontier = set(seeds)
    undirected = g.to_undirected(as_view=True)
    for _ in range(hops):
        next_frontier = set()
        for node in frontier:
            if node in undirected:
                next_frontier.update(undirected.neighbors(node))
        next_frontier -= reached
        reached.update(next_frontier)
        frontier = next_frontier
    return reached


def traverse(query: str, g: nx.DiGraph, hops: int = 1) -> nx.DiGraph:
    """Return the induced subgraph reached by expanding `hops` hops (both
    directions) out from every seed node matched in `query`. Empty if no
    seeds matched."""
    seeds = match_seed_nodes(query, g)
    if not seeds:
        return nx.DiGraph()

    reached = expand_around(g, seeds, hops)
    sub = g.subgraph(reached).copy()
    for node_id in seeds:
        if node_id in sub.nodes:
            sub.nodes[node_id]["is_seed"] = True
    return sub
