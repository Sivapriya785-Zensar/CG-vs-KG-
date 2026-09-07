"""
CG's context-extraction layer for the unstructured-data-source track: live,
per-query retrieval directly from the raw prose document, real embeddings,
no keyword list.

This is the asymmetry the "unstructured data" comparison is actually
testing: KG only ever sees graph/extract_kg_from_text.py's one-time,
possibly-lossy extraction -- if that extraction missed or flattened a
nuance from the document, KG has no way to recover it, ever. CG additionally
gets this live retrieval layer straight from the original source text on
every query, so a nuance the one-time extraction dropped is still reachable
here if the chunk containing it scores relevant. Whether that actually
produces better answers is the empirical question the test run answers, not
something asserted here.

Chunking is paragraph-level (the document's own natural unit), each chunk
embedded once and cached for the process lifetime -- cheap, since the
document is short. Retrieval is real cosine similarity between the query
embedding and every chunk embedding, same mechanism (and same underlying
embedding model) as the decision-trace direct-recall path in
graph/context_graph.py, just applied to document chunks instead of stored
statements.
"""
import math

from kg_cg_experiment.agent.llm_client import embed
from kg_cg_experiment.data.unstructured_policy_document import POLICY_DOCUMENT_TEXT

_CHUNK_CACHE: list[tuple[str, list[float]]] | None = None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _chunks() -> list[str]:
    return [p.strip() for p in POLICY_DOCUMENT_TEXT.split("\n\n") if p.strip()]


def _embedded_chunks() -> list[tuple[str, list[float]]]:
    """Embeds every chunk once per process and caches the result -- the
    document doesn't change at runtime, so there's no reason to re-embed it
    on every query."""
    global _CHUNK_CACHE
    if _CHUNK_CACHE is None:
        _CHUNK_CACHE = [(chunk, embed(chunk)) for chunk in _chunks()]
    return _CHUNK_CACHE


def retrieve_relevant_chunks(query: str, top_k: int = 3, threshold: float = 0.45) -> list[tuple[str, float]]:
    """Real cosine similarity, computed fresh every call against a real
    query embedding. threshold is looser than the decision-trace path's
    0.65 -- these chunks are multi-sentence paragraphs covering several
    facts at once, so similarity to any one query is naturally diluted
    compared to a single declarative statement; a tighter threshold here
    would just starve CG of context it should have. top_k=3 (not 2): an
    empirical check (see README.md) found adjacent paragraphs sharing
    enough vocabulary -- both the tier and blackout paragraphs discuss tier
    exemptions -- that the single best-scoring chunk for a tier-fee
    question was sometimes a different, only-tangentially-related chunk;
    3 of this document's 8 chunks keeps real recall without returning
    everything. Returns [] (not a fallback trigger -- this layer is
    additive, not required) when nothing clears the bar."""
    query_embedding = embed(query)
    scored = [(chunk, _cosine(query_embedding, chunk_embedding)) for chunk, chunk_embedding in _embedded_chunks()]
    scored.sort(key=lambda x: -x[1])
    return [(chunk, score) for chunk, score in scored[:top_k] if score >= threshold]
