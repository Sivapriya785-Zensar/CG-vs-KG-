"""
Condition B: the per-query constructed Context Graph.

CG = KG traversal subgraph (same deterministic seed-matching as Condition A)
     + decision-trace evidence pulled from the *persistent* trace store
       (data/trace_store.py) -- from this session or any prior one belonging
       to the same user (traces are scoped by user_id, never pooled across
       unrelated customers).

Two independent, complementary ways a stored trace becomes relevant to a
query, both real, neither a hardcoded keyword list:

  1. KG-structural relevance: the query's own KG traversal reaches a node
     that maps to a known trace slot (data/slot_mapping.py), e.g. any
     tier:* node maps to the "loyalty_tier" slot. This is what lets "I'm
     Gold tier" apply to "will my change fee be waived?" even though those
     two sentences share almost no vocabulary (measured cosine similarity
     ~0.35 on this embedding model -- see README.md) -- the connection is a
     graph-structural one (tier -waives-> fee -applies_to-> change rule),
     not a textual one, so only the graph can find it.
  2. Direct embedding recall: the live query's embedding is compared against
     every stored trace's own statement embedding (real nomic-embed-text
     vectors, cosine similarity). This is what lets "did I buy insurance for
     my rental car?" recall a much earlier "I already declined the rental
     car insurance" statement (measured ~0.79-0.89) even when that fact has
     no KG node at all (car rental insurance isn't modeled in this schema).

Fail-fast: a slot only contributes evidence if every candidate trace for it
(from either path) agrees on the value. A conflict for the same slot (e.g.
two different loyalty tiers on record) is never resolved by guessing.
Fail-safe: no usable evidence, or a conflict -> fall back to exactly the
KG-static subgraph. Every fallback is returned as an explicit, loggable
event, and CG is never worse than KG-alone.

Two precision/recall fixes layered on top of the base mechanism (both found
by actually reading failures in the 50-question reasoning set, not
speculative hardening):

  - Recall fix: direct embedding recall used to embed the whole query as one
    vector, which let an unrelated clause dilute a genuinely relevant one
    below threshold (see graph/query_clauses.py docstring for the concrete
    failure). Now every clause is embedded and checked separately, taking
    the max similarity per trace across clauses.
  - Precision fix: a high-similarity direct hit is no longer accepted on
    embedding score alone -- its slot's topic keywords
    (data/slot_mapping.py SLOT_TOPIC_KEYWORDS) must actually appear
    somewhere in the query text. This guards against the real risk that two
    sentences can score highly similar for reasons unrelated to the slot
    they're nominally about.
"""
from dataclasses import dataclass, field

import networkx as nx

from kg_cg_experiment.agent.llm_client import embed
from kg_cg_experiment.config import GRAPH_TRAVERSAL_HOPS, TRACE_SIMILARITY_THRESHOLD
from kg_cg_experiment.data import trace_store
from kg_cg_experiment.data.slot_mapping import SLOT_TOPIC_KEYWORDS
from kg_cg_experiment.data.trace_store import TraceRow
from kg_cg_experiment.graph.query_clauses import split_into_clauses
from kg_cg_experiment.graph.seed_matching import expand_around, match_seed_nodes, traverse


@dataclass
class EvidenceUsed:
    trace: TraceRow
    origin: str  # "this_session" | "prior_session"
    matched_via: str  # "structural" | "direct_similarity" | "both"
    similarity: float | None


@dataclass
class ContextGraphResult:
    subgraph: nx.DiGraph
    fell_back: bool
    fallback_reason: str | None
    evidence_used: list[EvidenceUsed] = field(default_factory=list)
    rejected_candidates: list = field(default_factory=list)
    trace_fingerprint: str = ""  # stable summary of evidence values, for cache invalidation


def _structural_candidates(kg: nx.DiGraph, seeds: list[str]) -> set[tuple[str, str]]:
    """Which trace slots does this query's OWN seed match structurally
    implicate -- walked from the actual seed nodes, not from anything that
    merely happens to land in the wider 2-hop context ball.

    This distinction matters: e.g. asking about Furniture's return fee can
    seed `fee:restocking_fee_waiver` too (its alias list includes the
    generic phrase "restocking fee"), and that fee node has a `waives` edge
    from tier:platinum -- but whether that waiver is worth surfacing depends
    on which category's own return rule is actually in play. Walking from
    the *rule/category* seeds specifically (not every seed) keeps an
    irrelevant tier connection from being treated as "this query is about
    the user's tier" when it isn't.
    """
    slots = set()
    seed_types = {kg.nodes[s].get("type") for s in seeds if s in kg.nodes}
    category_seeds = [s for s in seeds if s in kg.nodes and kg.nodes[s].get("type") == "ProductCategory"]

    if category_seeds:
        # A specific category was named -- anchor ONLY on that category's
        # own rule(s). A generic rule alias (e.g. "exchange fee") can
        # co-match in the same query text; its unrelated tier-waiver
        # neighborhood must not leak in just because it happened to match.
        #
        # Direction-agnostic on purpose: the hand-authored graph always
        # writes category -> rule, but an LLM-extracted graph (see
        # graph/extract_kg_from_text.py) isn't guaranteed to pick the same
        # direction for a fact it phrased the other way round in its own
        # output -- the relation name was pinned in that prompt, direction
        # wasn't. Every other traversal in this codebase already treats the
        # graph as undirected (graph/seed_matching.py); this was the one
        # spot still assuming a fixed direction, which silently broke
        # structural relevance for every category-rule edge an extraction
        # happened to reverse.
        undirected = kg.to_undirected(as_view=True)
        anchor_seeds = [
            n for cat in category_seeds if cat in undirected for n in undirected.neighbors(cat)
            if kg.nodes[n].get("type") in ("ExchangeRule", "ReturnRule")
        ]
    else:
        # No specific category named -- a directly-seeded generic Fee node
        # (e.g. "is my restocking fee waived?" seeds fee:restocking_fee_waiver
        # via its own alias) is just as legitimate an anchor here as a
        # generic Rule alias: the query is genuinely about that fee in the
        # abstract, so its own tier-waiver edge is relevant.
        anchor_seeds = [
            s for s in seeds
            if s in kg.nodes and kg.nodes[s].get("type") in ("ExchangeRule", "ReturnRule", "Fee")
        ]

    # PromoBlackout seeds are always specific on their own (unlike the
    # generic rule aliases above, a given blackout window names itself), and
    # they connect directly to tier exemptions -- always anchor on them too.
    anchor_seeds += [s for s in seeds if s in kg.nodes and kg.nodes[s].get("type") == "PromoBlackout"]

    if anchor_seeds:
        neighborhood = expand_around(kg, anchor_seeds, GRAPH_TRAVERSAL_HOPS)
        for node_id in neighborhood:
            node_type = kg.nodes[node_id].get("type")
            if node_type == "LoyaltyTier":
                slots.add(("loyalty_tier", "tier"))
            elif node_type == "ProductCategory" and not category_seeds:
                # only relevant if the query itself didn't already specify
                # which category -- if it did, there's nothing to look up
                slots.add(("product", "category"))
            elif node_type == "WarrantyProduct":
                slots.add(("warranty", "status"))

    if "WarrantyProduct" in seed_types:
        slots.add(("warranty", "status"))

    return slots


def _slot_topic_plausible(query_text: str, slot: tuple[str, str]) -> bool:
    keywords = SLOT_TOPIC_KEYWORDS.get(slot)
    if not keywords:
        return True  # no keyword list defined for this slot -- don't block
    q = query_text.lower()
    return any(kw.lower() in q for kw in keywords)


def build_context_graph(query: str, user_id: str, session_id: str, kg: nx.DiGraph,
                         query_embedding: list[float]) -> ContextGraphResult:
    kg_sub = traverse(query, kg, hops=GRAPH_TRAVERSAL_HOPS)
    seeds = match_seed_nodes(query, kg)

    # Path 1: KG-structural relevance -- scoped to this user, so an
    # unrelated customer's stored tier/booking-type never leaks in.
    structural_slots = _structural_candidates(kg, seeds)
    structural_traces: dict[int, TraceRow] = {}
    for entity_key, attribute in structural_slots:
        for t in trace_store.traces_by_slot(user_id, entity_key, attribute):
            structural_traces[t.id] = t

    # Path 2: direct embedding recall against this user's stored traces,
    # per-clause (recall fix) and topic-filtered (precision fix).
    direct_traces: dict[int, float] = {}
    direct_rows: dict[int, TraceRow] = {}
    for clause in split_into_clauses(query):
        clause_embedding = query_embedding if clause == query.strip() else embed(clause)
        for t, score in trace_store.search_similar(user_id, clause_embedding, TRACE_SIMILARITY_THRESHOLD):
            if not _slot_topic_plausible(query, t.slot):
                continue
            if t.id not in direct_traces or score > direct_traces[t.id]:
                direct_traces[t.id] = score
                direct_rows[t.id] = t

    all_ids = set(structural_traces) | set(direct_traces)
    if not all_ids:
        return ContextGraphResult(
            subgraph=kg_sub,
            fell_back=True,
            fallback_reason="no stored decision trace matched this question, "
                             "structurally or by similarity",
        )

    all_rows = {**structural_traces, **direct_rows}

    by_slot: dict[tuple[str, str], list[TraceRow]] = {}
    for tid in all_ids:
        row = all_rows[tid]
        by_slot.setdefault(row.slot, []).append(row)

    conflicts = []
    rejected_ids = []
    winners: list[TraceRow] = []
    for slot, rows in by_slot.items():
        distinct_values = {r.value for r in rows}
        if len(distinct_values) > 1:
            conflicts.append(
                f"conflicting stored traces for {slot[0]}.{slot[1]}: "
                + ", ".join(sorted(f'{v!r}' for v in distinct_values))
            )
            rejected_ids.extend(r.id for r in rows)
        else:
            winners.append(max(rows, key=lambda r: r.created_at))

    if conflicts:
        return ContextGraphResult(
            subgraph=kg_sub,
            fell_back=True,
            fallback_reason="; ".join(conflicts),
            rejected_candidates=[all_rows[i].kg_node_id for i in rejected_ids if all_rows[i].kg_node_id],
        )

    cg = kg_sub.copy()
    link_targets = [w.kg_node_id for w in winners if w.kg_node_id and w.kg_node_id in kg.nodes]
    if link_targets:
        neighborhood = expand_around(kg, link_targets, GRAPH_TRAVERSAL_HOPS)
        for node_id in neighborhood:
            if node_id not in cg.nodes:
                cg.add_node(node_id, **kg.nodes[node_id])
        for src, dst, data in kg.subgraph(neighborhood).edges(data=True):
            if not cg.has_edge(src, dst):
                cg.add_edge(src, dst, **data)

    evidence_used = []
    for w in winners:
        origin = "this_session" if w.session_id == session_id else "prior_session"
        in_structural = w.id in structural_traces
        in_direct = w.id in direct_traces
        matched_via = "both" if (in_structural and in_direct) else ("structural" if in_structural else "direct_similarity")
        similarity = direct_traces.get(w.id)
        evidence_used.append(EvidenceUsed(trace=w, origin=origin, matched_via=matched_via, similarity=similarity))

        node_id = f"trace:{w.id}"
        cg.add_node(
            node_id,
            type="Evidence",
            label=f"{w.entity_key}.{w.attribute} = {w.value}",
            aliases=[],
            attrs={
                "raw_statement": w.raw_statement,
                "origin": origin,
                "matched_via": matched_via,
                "similarity": round(similarity, 3) if similarity is not None else None,
                "session_id": w.session_id,
            },
            is_evidence=True,
        )
        if w.kg_node_id and w.kg_node_id in cg.nodes:
            cg.add_edge(node_id, w.kg_node_id, relation="establishes")

    fingerprint = ";".join(sorted(f"{w.entity_key}.{w.attribute}={w.value}" for w in winners))

    return ContextGraphResult(
        subgraph=cg,
        fell_back=False,
        fallback_reason=None,
        evidence_used=evidence_used,
        trace_fingerprint=fingerprint,
    )
