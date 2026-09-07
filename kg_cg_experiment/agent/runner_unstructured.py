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
    "Be concise and specific (state fees, tiers, and dates when relevant). "
    "If the facts below don't cover something, say you don't have that information -- "
    "do not invent policy details.\n\n{graph_context}"
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
