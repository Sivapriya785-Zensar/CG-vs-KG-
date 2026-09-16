"""
Runs one query against Condition A (KG) or Condition B (CG) with the *same*
agent logic (same system prompt template, same LLM, same call shape) -- the
only thing that differs between conditions is what graph context (and,
for CG only when it has real evidence, recent conversation turns) gets
injected into the prompt. This is the isolation the experiment depends on.

Also hosts run_statement(), the Statement-mode path: turns a declared fact
into a persisted decision trace with no LLM call at all (zero tokens).
"""
from dataclasses import dataclass, field

from kg_cg_experiment.agent import cache
from kg_cg_experiment.agent.llm_client import chat, embed
from kg_cg_experiment.config import CG_RECENT_TURNS_WINDOW, GRAPH_TRAVERSAL_HOPS
from kg_cg_experiment.data import trace_store
from kg_cg_experiment.graph.context_graph import build_context_graph
from kg_cg_experiment.graph.knowledge_graph import build_static_kg
from kg_cg_experiment.graph.seed_matching import traverse
from kg_cg_experiment.graph.serialize import graph_content_hash, graph_to_context_text, graph_to_json
from kg_cg_experiment.graph.statement_extraction import extract_statements

SYSTEM_PROMPT = (
    "You are a customer support policy assistant for a retail store. "
    "Answer the user's question using ONLY the policy facts provided below. "
    "Follow these rules strictly:\n"
    "1. Use only facts literally stated below. Do not rely on general knowledge of "
    "how retail returns, warranties, or loyalty programs usually work.\n"
    "2. If a fact needed to answer is not stated below -- including the customer's own "
    "loyalty tier, product category, or purchase history -- say that information is not "
    "available in the current context. Do not guess it and do not assert a specific value "
    "(e.g. 'As a Platinum member...') that was not given to you. You may explain what the "
    "policy says for each relevant case and state that you don't know which applies here.\n"
    "3. Do not invent fees, dates, tiers, windows, rules, or eligibility criteria that are "
    "not written below.\n"
    "4. Do not add separate fees together into a combined total unless the question "
    "explicitly asks for a sum.\n"
    "Be concise and specific: state the exact fees, tiers, windows, and dates that ARE "
    "provided.\n\n{graph_context}"
)


@dataclass
class ConditionResult:
    condition: str
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    graph_json: dict
    fell_back: bool = False
    fallback_reason: str | None = None
    served_from_cache: bool = False
    cache_note: str | None = None
    messages_sent: list = field(default_factory=list)


def run_kg(query: str) -> ConditionResult:
    kg = build_static_kg()
    sub = traverse(query, kg, hops=GRAPH_TRAVERSAL_HOPS)
    context_text = graph_to_context_text(sub)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(graph_context=context_text)},
        {"role": "user", "content": query},
    ]
    result = chat(messages)
    return ConditionResult(
        condition="kg",
        answer=result["text"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
        total_tokens=result["total_tokens"],
        graph_json=graph_to_json(sub),
        messages_sent=messages,
    )


def run_cg(query: str, user_id: str, session_id: str, turns: list[dict], use_cache: bool = False) -> ConditionResult:
    kg = build_static_kg()
    query_embedding = embed(query)
    cg_result = build_context_graph(query, user_id, session_id, kg, query_embedding)

    if cg_result.fell_back:
        # Fail-safe: behave identically to Condition A -- same context,
        # no history injected, so CG can never do worse than KG-alone.
        context_text = graph_to_context_text(cg_result.subgraph)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(graph_context=context_text)},
            {"role": "user", "content": query},
        ]
    else:
        context_text = graph_to_context_text(cg_result.subgraph)
        recent = turns[-CG_RECENT_TURNS_WINDOW:]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(graph_context=context_text)},
            *recent,
            {"role": "user", "content": query},
        ]

    kg_context_hash = graph_content_hash(cg_result.subgraph) if not cg_result.fell_back else None

    if use_cache and not cg_result.fell_back:
        hit = cache.lookup(user_id, query_embedding, kg_context_hash, cg_result.trace_fingerprint)
        if hit is not None:
            return ConditionResult(
                condition="cg",
                answer=hit.answer_text,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                graph_json=graph_to_json(cg_result.subgraph, cg_result.rejected_candidates, kg),
                fell_back=False,
                served_from_cache=True,
                cache_note=(
                    f"served from cache -- 0 new tokens this call; originally cost "
                    f"{hit.original_prompt_tokens + hit.original_completion_tokens} tokens "
                    f"when first answered as: {hit.matched_question!r}"
                ),
                messages_sent=messages,
            )

    result = chat(messages)

    if use_cache and not cg_result.fell_back:
        cache.store(
            user_id, query, query_embedding, kg_context_hash, cg_result.trace_fingerprint,
            result["text"], result["prompt_tokens"], result["completion_tokens"],
        )

    return ConditionResult(
        condition="cg",
        answer=result["text"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
        total_tokens=result["total_tokens"],
        graph_json=graph_to_json(cg_result.subgraph, cg_result.rejected_candidates, kg),
        fell_back=cg_result.fell_back,
        fallback_reason=cg_result.fallback_reason,
        messages_sent=messages,
    )


def run_both(query: str, user_id: str, session_id: str, turns: list[dict], use_cache: bool = False) -> dict:
    return {
        "kg": run_kg(query),
        "cg": run_cg(query, user_id, session_id, turns, use_cache=use_cache),
    }


def run_statement(text: str, user_id: str, session_id: str) -> dict:
    """Statement mode: no LLM chat call at all -- deterministic extraction,
    one real embedding call per stored fact (needed later for retrieval),
    then a direct SQLite write. Returns what was actually stored, or an
    honest 'nothing extracted' if no rule matched."""
    extracted = extract_statements(text)
    if not extracted:
        return {"stored": [], "message": "No extraction rule matched this statement -- nothing stored."}

    stored = []
    text_embedding = embed(text)
    for item in extracted:
        trace_id = trace_store.add_trace(
            user_id=user_id,
            entity_key=item.entity_key,
            attribute=item.attribute,
            value=item.value,
            raw_statement=text,
            session_id=session_id,
            embedding=text_embedding,
            kg_node_id=item.kg_node_id,
        )
        stored.append({
            "trace_id": trace_id,
            "entity_key": item.entity_key,
            "attribute": item.attribute,
            "value": item.value,
            "kg_node_id": item.kg_node_id,
        })

    summary = "; ".join(f"{s['entity_key']}.{s['attribute']} = {s['value']}" for s in stored)
    return {"stored": stored, "message": f"Stored: {summary}"}
