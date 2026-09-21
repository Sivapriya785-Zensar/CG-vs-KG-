"""
Runs the 500-question large-scale unstructured track through CG ONLY (no
KG calls -- half the live model calls of a full KG+CG run, per explicit
scope request). Uses the same context_graph.build_context_graph() mechanism
as every other CG run in this project (structural + direct-embedding
personalization recall against the trace store), plus live chunk retrieval
over the full ~2000-product document -- self-contained here rather than
reusing graph/context_extraction.py, so this large corpus's chunk cache
never touches (or is touched by) the default 8-paragraph document's cache.

Configurable via env vars (same pattern as the rest of the sweep):
  LARGE_CHUNK_THRESHOLD   (default 0.45)
  LARGE_CHUNK_TOP_K       (default 3)
  OLLAMA_TEMPERATURE      (read by config.py already)

Run:  python -m kg_cg_experiment.tests.run_large_cg_only_test
"""
import datetime
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import networkx as nx

from kg_cg_experiment.agent.llm_client import OllamaUnavailableError, chat, embed, is_available
from kg_cg_experiment.agent.runner import run_statement
from kg_cg_experiment.config import CG_RECENT_TURNS_WINDOW
from kg_cg_experiment.data import trace_store
from kg_cg_experiment.data.large_unstructured_policy_document import CATALOG_SECTION_TEXT
from kg_cg_experiment.graph.context_graph import build_context_graph
from kg_cg_experiment.graph.serialize import graph_to_context_text
from kg_cg_experiment.session import store
from kg_cg_experiment.tests.test_queries_large import ALL_LARGE_QUERIES

LARGE_EXTRACTED_JSON = Path(__file__).resolve().parents[1] / "data" / "large_extracted_kg.json"
CHUNK_THRESHOLD = float(os.environ.get("LARGE_CHUNK_THRESHOLD", "0.45"))
TOP_K = int(os.environ.get("LARGE_CHUNK_TOP_K", "3"))

SYSTEM_PROMPT = (
    "You are a customer support policy assistant for a large retail store with "
    "a catalog of thousands of products across five departments. "
    "Answer the user's question using ONLY the facts provided below. "
    "Follow these rules strictly:\n"
    "1. Use only facts literally stated below. Do not rely on general knowledge of "
    "how retail returns, warranties, or loyalty programs usually work.\n"
    "2. If a fact needed to answer is not stated below -- including the customer's own "
    "loyalty tier or purchase history -- say that information is not available in the "
    "current context. Do not guess it.\n"
    "3. Do not invent fees, dates, tiers, windows, rules, or departments that are not "
    "written below.\n\n{graph_context}"
)


def build_large_kg() -> nx.DiGraph:
    import json
    data = json.loads(LARGE_EXTRACTED_JSON.read_text(encoding="utf-8"))
    g = nx.DiGraph()
    for node in data["nodes"]:
        g.add_node(node["id"], type=node["type"], label=node.get("label", node["id"]),
                   aliases=node.get("aliases", []), attrs=node.get("attrs", {}))
    for edge in data["edges"]:
        if edge["source"] in g.nodes and edge["target"] in g.nodes:
            g.add_edge(edge["source"], edge["target"], relation=edge.get("relation", ""))
    return g


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


_CATALOG_CHUNKS = [p.strip() for p in CATALOG_SECTION_TEXT.split("\n\n") if p.strip()]
_CATALOG_CHUNK_CACHE: list[tuple[str, list[float]]] | None = None


def _embedded_catalog_chunks() -> list[tuple[str, list[float]]]:
    global _CATALOG_CHUNK_CACHE
    if _CATALOG_CHUNK_CACHE is None:
        print(f"Embedding {len(_CATALOG_CHUNKS)} catalog chunks once (cached for this run)...")
        _CATALOG_CHUNK_CACHE = [(c, embed(c)) for c in _CATALOG_CHUNKS]
    return _CATALOG_CHUNK_CACHE


def retrieve_catalog_chunks(query_embedding: list[float]) -> list[tuple[str, float]]:
    scored = [(c, _cosine(query_embedding, e)) for c, e in _embedded_catalog_chunks()]
    scored.sort(key=lambda x: -x[1])
    return [(c, s) for c, s in scored[:TOP_K] if s >= CHUNK_THRESHOLD]


def run_all():
    label = f"chunk{CHUNK_THRESHOLD}_temp{os.environ.get('OLLAMA_TEMPERATURE', '0')}"
    out_dir = Path(__file__).resolve().parents[1] / "results_large"
    out_dir.mkdir(exist_ok=True)

    if not LARGE_EXTRACTED_JSON.exists():
        print(f"ERROR: {LARGE_EXTRACTED_JSON} missing. Run graph/extract_large_kg_from_text.py first.")
        sys.exit(1)
    if not is_available():
        print("ERROR: Ollama is not reachable.")
        sys.exit(1)

    trace_store.clear_all()
    kg = build_large_kg()
    print(f"Large extracted KG: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges.")
    print(f"Running {len(ALL_LARGE_QUERIES)} questions, CG-only, "
          f"chunk_threshold={CHUNK_THRESHOLD}, temperature={os.environ.get('OLLAMA_TEMPERATURE', '0')}")

    raw_lines = [f"# CG-only large-scale run -- {label}\n\nGenerated: {datetime.datetime.now().isoformat()}\n",
                 f"Chunk threshold: {CHUNK_THRESHOLD}, top_k: {TOP_K}, "
                 f"catalog chunks: {len(_CATALOG_CHUNKS)}, extracted KG: "
                 f"{kg.number_of_nodes()}n/{kg.number_of_edges()}e\n"]
    index_lines = ["# Index\n", "| id | category | tokens_cg | cg_fallback | chunks_retrieved |\n",
                   "|---|---|---|---|---|\n"]

    for n, item in enumerate(ALL_LARGE_QUERIES, 1):
        session_id = f"lg-{item['id']}-query"
        store.reset(session_id)
        user_id = f"lg-user-{item['id']}"

        raw_lines.append(f"\n## {item['id']} ({item['category']})\n")
        raw_lines.append(f"**Query:** {item['query']}\n")
        raw_lines.append(f"**Expected:** {item['expected_answer']}\n")

        for stmt in item["seed_statements"]:
            try:
                result = run_statement(stmt, user_id, session_id)
            except OllamaUnavailableError as e:
                print(f"ERROR seeding {item['id']}: {e}")
                sys.exit(1)
            raw_lines.append(f"- Seed: \"{stmt}\" -> {result['message']}\n")

        turns = store.get_turns(session_id)

        try:
            query_embedding = embed(item["query"])
            cg_result = build_context_graph(item["query"], user_id, session_id, kg, query_embedding)
            retrieved = retrieve_catalog_chunks(query_embedding)

            context_text = graph_to_context_text(cg_result.subgraph)
            if retrieved:
                excerpts = "\n\n".join(f"- {c}" for c, _s in retrieved)
                context_text += f"\n\nRelevant catalog excerpts:\n{excerpts}"

            if cg_result.fell_back:
                messages = [{"role": "system", "content": SYSTEM_PROMPT.format(graph_context=context_text)},
                            {"role": "user", "content": item["query"]}]
            else:
                recent = turns[-CG_RECENT_TURNS_WINDOW:]
                messages = [{"role": "system", "content": SYSTEM_PROMPT.format(graph_context=context_text)},
                            *recent, {"role": "user", "content": item["query"]}]

            result = chat(messages)
        except OllamaUnavailableError as e:
            raw_lines.append(f"\n**ERROR calling Ollama: {e}**\n")
            print(f"ERROR on {item['id']}: {e}")
            sys.exit(1)

        raw_lines.append(f"\n**CG ({result['total_tokens']} tokens, "
                          f"{result['prompt_tokens']}+{result['completion_tokens']}"
                          f"{', FELL BACK: ' + cg_result.fallback_reason if cg_result.fell_back else ''}):**\n")
        raw_lines.append(f"> {result['text']}\n")
        if retrieved:
            raw_lines.append("Catalog chunks retrieved:\n")
            for chunk, score in retrieved:
                raw_lines.append(f"  - (sim={score:.3f}) \"{chunk[:100]}...\"\n")
        else:
            raw_lines.append("Catalog chunks retrieved: none above threshold.\n")

        index_lines.append(f"| {item['id']} | {item['category']} | {result['total_tokens']} | "
                            f"{'y' if cg_result.fell_back else 'n'} | {len(retrieved)} |\n")

        if n % 50 == 0:
            print(f"  ...{n}/{len(ALL_LARGE_QUERIES)} done")

    (out_dir / f"raw_log_{label}.md").write_text("".join(raw_lines), encoding="utf-8")
    (out_dir / f"index_{label}.md").write_text("".join(index_lines), encoding="utf-8")
    print(f"\nWrote raw_log_{label}.md and index_{label}.md under {out_dir}")


if __name__ == "__main__":
    run_all()
