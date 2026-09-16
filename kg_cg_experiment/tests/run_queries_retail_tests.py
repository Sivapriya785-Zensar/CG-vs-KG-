
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kg_cg_experiment.agent.llm_client import OllamaUnavailableError, is_available
from kg_cg_experiment.agent.runner import run_cg, run_kg, run_statement
from kg_cg_experiment.data import trace_store
from kg_cg_experiment.session import store
from kg_cg_experiment.tests.test_queries_retail import ALL_RETAIL_QUERIES, LEAK_FREE_COUNT

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results_retail"


def run_all():
    if not is_available():
        print("ERROR: Ollama is not reachable. No results were produced -- nothing simulated.")
        sys.exit(1)

    RESULTS_DIR.mkdir(exist_ok=True)
    trace_store.clear_all()
    print(f"Cleared trace store for a reproducible run of {len(ALL_RETAIL_QUERIES)} queries "
          f"({LEAK_FREE_COUNT}/{len(ALL_RETAIL_QUERIES)} are leak_free memory tests).\n")

    raw_lines = [f"# Raw log -- retail Direct / Reasoning / Mixed set\n\nGenerated: {datetime.datetime.now().isoformat()}\n"]
    index_lines = ["# Index\n", "| id | category | leak_free | tokens_A (KG) | tokens_B (CG) | cg_fallback |\n",
                   "|---|---|---|---|---|---|\n"]

    for item in ALL_RETAIL_QUERIES:
        query_session = f"rq-{item['id']}-query"
        store.reset(query_session)
        user_id = f"rq-user-{item['id']}"

        raw_lines.append(f"\n## {item['id']} ({item['category']}, leak_free={item['leak_free']})\n")
        raw_lines.append(f"**Query:** {item['query']}\n")
        raw_lines.append(f"**Expected:** {item['expected_answer']}\n")
        raw_lines.append(f"**Why (grounding):** {item['why']}\n")
        if item.get("note"):
            raw_lines.append(f"**Note:** {item['note']}\n")

        for stmt in item["seed_statements"]:
            try:
                result = run_statement(stmt, user_id, query_session)
            except OllamaUnavailableError as e:
                print(f"ERROR extracting statement for {item['id']}: {e}")
                sys.exit(1)
            raw_lines.append(f"- Seed: \"{stmt}\" -> {result['message']}\n")

        turns = store.get_turns(query_session)

        try:
            kg_res = run_kg(item["query"])
            cg_res = run_cg(item["query"], user_id, query_session, turns, use_cache=False)
        except OllamaUnavailableError as e:
            raw_lines.append(f"\n**ERROR calling Ollama: {e}**\n")
            print(f"ERROR on {item['id']}: {e}")
            sys.exit(1)

        raw_lines.append(f"\n**KG ({kg_res.total_tokens} tokens, {kg_res.prompt_tokens}+{kg_res.completion_tokens}):**\n")
        raw_lines.append(f"> {kg_res.answer}\n")
        raw_lines.append(f"\n**CG ({cg_res.total_tokens} tokens, {cg_res.prompt_tokens}+{cg_res.completion_tokens}"
                          f"{', FELL BACK: ' + cg_res.fallback_reason if cg_res.fell_back else ''}):**\n")
        raw_lines.append(f"> {cg_res.answer}\n")

        index_lines.append(f"| {item['id']} | {item['category']} | {item['leak_free']} | "
                            f"{kg_res.total_tokens} | {cg_res.total_tokens} | {'y' if cg_res.fell_back else 'n'} |\n")

    (RESULTS_DIR / "raw_log.md").write_text("".join(raw_lines), encoding="utf-8")
    (RESULTS_DIR / "index.md").write_text("".join(index_lines), encoding="utf-8")
    print(f"Wrote raw_log.md under {RESULTS_DIR}")


if __name__ == "__main__":
    run_all()
