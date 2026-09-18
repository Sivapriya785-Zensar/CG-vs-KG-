
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kg_cg_experiment.agent.llm_client import OllamaUnavailableError, is_available
from kg_cg_experiment.agent.runner import run_statement
from kg_cg_experiment.agent.runner_unstructured import run_cg_unstructured, run_kg_unstructured
from kg_cg_experiment.data import trace_store
from kg_cg_experiment.graph.knowledge_graph_unstructured import EXTRACTED_JSON_PATH, build_kg_from_unstructured
from kg_cg_experiment.session import store
from kg_cg_experiment.tests.test_queries_retail import ALL_RETAIL_QUERIES

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results_retail_unstructured"


def run_all():
    if not EXTRACTED_JSON_PATH.exists():
        print(f"ERROR: {EXTRACTED_JSON_PATH} doesn't exist. Run the one-time extraction first:\n"
              f"  python -m kg_cg_experiment.graph.extract_kg_from_text")
        sys.exit(1)

    if not is_available():
        print("ERROR: Ollama is not reachable. No results were produced -- nothing simulated.")
        sys.exit(1)

    RESULTS_DIR.mkdir(exist_ok=True)
    trace_store.clear_all()

    kg = build_kg_from_unstructured()
    print(f"Loaded extracted KG: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges.")
    print(f"Running {len(ALL_RETAIL_QUERIES)} questions against the unstructured-data-source pipeline.\n")

    raw_lines = [f"# Raw log -- unstructured-data-source track\n\nGenerated: {datetime.datetime.now().isoformat()}\n",
                 f"Extracted KG: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges "
                 f"(see data/extracted_kg.json, produced by graph/extract_kg_from_text.py).\n"]
    index_lines = ["# Index\n", "| id | category | leak_free | tokens_A (KG) | tokens_B (CG) | "
                   "cg_fallback | chunks_retrieved |\n", "|---|---|---|---|---|---|---|\n"]

    for item in ALL_RETAIL_QUERIES:
        query_session = f"ru-{item['id']}-query"
        store.reset(query_session)
        user_id = f"ru-user-{item['id']}"

        raw_lines.append(f"\n## {item['id']} ({item['category']}, leak_free={item['leak_free']})\n")
        raw_lines.append(f"**Query:** {item['query']}\n")
        raw_lines.append(f"**Expected:** {item['expected_answer']}\n")
        raw_lines.append(f"**Why (grounding):** {item['why']}\n")

        for stmt in item["seed_statements"]:
            try:
                result = run_statement(stmt, user_id, query_session)
            except OllamaUnavailableError as e:
                print(f"ERROR extracting statement for {item['id']}: {e}")
                sys.exit(1)
            raw_lines.append(f"- Seed: \"{stmt}\" -> {result['message']}\n")

        turns = store.get_turns(query_session)

        try:
            kg_res = run_kg_unstructured(item["query"])
            cg_res = run_cg_unstructured(item["query"], user_id, query_session, turns)
        except OllamaUnavailableError as e:
            raw_lines.append(f"\n**ERROR calling Ollama: {e}**\n")
            print(f"ERROR on {item['id']}: {e}")
            sys.exit(1)

        raw_lines.append(f"\n**KG-unstructured ({kg_res.total_tokens} tokens, "
                          f"{kg_res.prompt_tokens}+{kg_res.completion_tokens}):**\n")
        raw_lines.append(f"> {kg_res.answer}\n")

        raw_lines.append(f"\n**CG-unstructured ({cg_res.total_tokens} tokens, "
                          f"{cg_res.prompt_tokens}+{cg_res.completion_tokens}"
                          f"{', FELL BACK: ' + cg_res.fallback_reason if cg_res.fell_back else ''}):**\n")
        raw_lines.append(f"> {cg_res.answer}\n")
        if cg_res.retrieved_chunks:
            raw_lines.append("Context-extraction layer retrieved:\n")
            for chunk, score in cg_res.retrieved_chunks:
                raw_lines.append(f"  - (sim={score:.3f}) \"{chunk[:100]}...\"\n")
        else:
            raw_lines.append("Context-extraction layer retrieved: nothing above threshold.\n")

        index_lines.append(f"| {item['id']} | {item['category']} | {item['leak_free']} | "
                            f"{kg_res.total_tokens} | {cg_res.total_tokens} | "
                            f"{'y' if cg_res.fell_back else 'n'} | {len(cg_res.retrieved_chunks)} |\n")

    (RESULTS_DIR / "raw_log.md").write_text("".join(raw_lines), encoding="utf-8")
    (RESULTS_DIR / "index.md").write_text("".join(index_lines), encoding="utf-8")

    print(f"Wrote raw_log.md and index.md under {RESULTS_DIR}")


if __name__ == "__main__":
    run_all()
