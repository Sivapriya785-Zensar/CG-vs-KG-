"""
Opt-in answer-cache reuse for Condition B (the "store successful decision
traces which can be applied to similar questions, to reduce tokens" option).

OFF by default everywhere the core measurement runs -- the predefined test
suite never uses it, and the UI only uses it when the user explicitly checks
the "reuse cached answers" box. The task's "no token-usage optimization"
instruction governs the actual A/B measurement; this is a separate, clearly
labeled, opt-in feature layered on top, never silently applied.

A cache hit requires ALL of:
  - the new question is a close paraphrase of a previously answered one
    (real embedding similarity, config.CACHE_SIMILARITY_THRESHOLD -- higher
    than the trace-matching threshold, since reusing a whole answer is a
    stronger claim than "this fact is relevant")
  - the KG context subgraph is byte-identical (graph_content_hash)
  - the exact decision-trace values used are byte-identical (trace_fingerprint)

Any one of those failing means a fresh LLM call, never a stale reuse.
"""
from dataclasses import dataclass

from kg_cg_experiment.config import CACHE_SIMILARITY_THRESHOLD
from kg_cg_experiment.data import trace_store


@dataclass
class CacheHit:
    answer_text: str
    original_prompt_tokens: int
    original_completion_tokens: int
    matched_question: str


def lookup(user_id: str, query_embedding: list[float], kg_context_hash: str, trace_fingerprint: str) -> CacheHit | None:
    row = trace_store.cache_search(user_id, query_embedding, kg_context_hash, trace_fingerprint, CACHE_SIMILARITY_THRESHOLD)
    if row is None:
        return None
    return CacheHit(
        answer_text=row.answer_text,
        original_prompt_tokens=row.prompt_tokens,
        original_completion_tokens=row.completion_tokens,
        matched_question=row.question_text,
    )


def store(user_id: str, query: str, query_embedding: list[float], kg_context_hash: str, trace_fingerprint: str,
          answer_text: str, prompt_tokens: int, completion_tokens: int) -> None:
    trace_store.cache_add(
        user_id=user_id,
        question_text=query,
        kg_context_hash=kg_context_hash,
        trace_fingerprint=trace_fingerprint,
        answer_text=answer_text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        embedding=query_embedding,
    )
