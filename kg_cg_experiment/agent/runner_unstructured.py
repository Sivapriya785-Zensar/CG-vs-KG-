"""
Runs a query against the unstructured-data-source track: same isolation
discipline as agent/runner.py (same system prompt template, same LLM, same
call shape for both conditions), same trace-store evidence mechanism for
personalization -- the only thing that's actually different from the
structured track is where the base policy knowledge comes from.

  run_kg_unstructured: traverse the ONE-TIME-extracted graph
    (graph/knowledge_graph_unstructured.py). Exactly what run_kg() does,
    just pointed at a different graph object.
  run_cg_unstructured: everything run_cg() does (structural + direct-recall
    evidence over the extracted graph) PLUS graph/context_extraction.py's
    live retrieval straight from the original prose -- the asymmetry this
    whole comparison track is testing: KG is permanently limited to
    whatever the one-time extraction captured; CG gets another live shot at
    the original source on every query.

Deliberately its own file, not a branch inside runner.py -- the two tracks
should stay easy to diff against each other.
"""
from dataclasses import dataclass, field

from kg_cg_experiment.agent.llm_client import chat, embed
from kg_cg_experiment.config import CG_RECENT_TURNS_WINDOW, GRAPH_TRAVERSAL_HOPS
from kg_cg_experiment.graph.context_extraction import retrieve_relevant_chunks
from kg_cg_experiment.graph.context_graph import build_context_graph
from kg_cg_experiment.graph.knowledge_graph_unstructured import build_kg_from_unstructured
from kg_cg_experiment.graph.seed_matching import traverse
from kg_cg_experiment.graph.serialize import graph_to_context_text, graph_to_json

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
    retrieved_chunks: list = field(default_factory=list)  # [(chunk_text, similarity)], CG only
    messages_sent: list = field(default_factory=list)


def run_kg_unstructured(query: str) -> ConditionResult:
    kg = build_kg_from_unstructured()
    sub = traverse(query, kg, hops=GRAPH_TRAVERSAL_HOPS)
    context_text = graph_to_context_text(sub)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(graph_context=context_text)},
        {"role": "user", "content": query},
    ]
    result = chat(messages)
    return ConditionResult(
        condition="kg_unstructured",
        answer=result["text"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
        total_tokens=result["total_tokens"],
        graph_json=graph_to_json(sub),
        messages_sent=messages,
    )


def run_cg_unstructured(query: str, user_id: str, session_id: str, turns: list[dict]) -> ConditionResult:
    kg = build_kg_from_unstructured()
    query_embedding = embed(query)
    cg_result = build_context_graph(query, user_id, session_id, kg, query_embedding)

    graph_context_text = graph_to_context_text(cg_result.subgraph)
    retrieved = retrieve_relevant_chunks(query)

    context_text = graph_context_text
    if retrieved:
        excerpts = "\n\n".join(f"- {chunk}" for chunk, _score in retrieved)
        context_text += f"\n\nRelevant policy document excerpts:\n{excerpts}"

    if cg_result.fell_back:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(graph_context=context_text)},
            {"role": "user", "content": query},
        ]
    else:
        recent = turns[-CG_RECENT_TURNS_WINDOW:]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(graph_context=context_text)},
            *recent,
            {"role": "user", "content": query},
        ]

    result = chat(messages)
    return ConditionResult(
        condition="cg_unstructured",
        answer=result["text"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
        total_tokens=result["total_tokens"],
        graph_json=graph_to_json(cg_result.subgraph, cg_result.rejected_candidates, kg),
        fell_back=cg_result.fell_back,
        fallback_reason=cg_result.fallback_reason,
        retrieved_chunks=retrieved,
        messages_sent=messages,
    )
