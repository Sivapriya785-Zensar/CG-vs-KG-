"""
Runs the predefined 50 test queries against BOTH conditions, live, via the
real runner (real local chat model + real local embedding model). Nothing
here is precomputed. If Ollama isn't reachable this script fails loudly
instead of writing fake output.

The trace store is cleared once at the start of the run for reproducibility
of this specific graded run (so "prior session" cases are only seeded by
this script, not polluted by earlier interactive UI use) -- then
seed_statements are planted through the real Statement-mode pipeline
(agent.runner.run_statement), same code path the UI uses, before each
question runs. The answer cache is never used for this measurement run
(config default use_cache=False everywhere here) -- per the task's
"no token-usage optimization" rule, this run measures real per-query cost.

Writes, under kg_cg_experiment/results/:
  - raw_log.md       every statement-extraction event, every query/response
                      pair, real token counts, and the CG constructed
                      subgraph / fallback event for every query
  - results_table.md query, group, subtype, tokens A, tokens B, correct A/B,
                      cg_fallback y/n
  - summary.md        slide-ready summary
"""
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kg_cg_experiment.agent.llm_client import OllamaUnavailableError, is_available
from kg_cg_experiment.agent.runner import run_cg, run_kg, run_statement
from kg_cg_experiment.data import trace_store
from kg_cg_experiment.session import store
from kg_cg_experiment.tests.test_queries import ALL_QUERIES

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def keyword_hit(answer: str, keywords: list[str]) -> bool | None:
    """Leading-word-boundary match, not raw substring containment or a full
    \\bword\\b match. Plain substring matching let a short keyword like "no"
    false-positive inside "eco-NO-my" or "can-NO-t" (caught by manually
    reading raw_log.md, not by the heuristic itself). A strict \\bword\\b
    match overcorrected the other way and broke intentional prefix matches
    like "dec" against "December". A leading boundary only satisfies both:
    "no" cannot start mid-word (no match inside "economy"/"cannot"), while
    "dec" still matches at the start of "December"."""
    if not keywords:
        return None  # not auto-gradable from keywords alone -- see raw log / manual review
    a = answer.lower()
    return any(re.search(rf"\b{re.escape(kw.lower())}", a) for kw in keywords)


def run_all():
    if not is_available():
        print("ERROR: Ollama is not reachable. No results were produced -- nothing simulated.")
        sys.exit(1)

    RESULTS_DIR.mkdir(exist_ok=True)
    trace_store.clear_all()
    print(f"Cleared trace store for a reproducible run of {len(ALL_QUERIES)} queries.\n")

    raw_lines = [f"# Raw query/response log (50-question set)\n\nGenerated: {datetime.datetime.now().isoformat()}\n"]
    table_rows = []
    isolation_broken = False

    for item in ALL_QUERIES:
        query_session = f"test-{item['id']}-query"
        store.reset(query_session)
        # Each test item is its OWN hypothetical customer -- a fresh, unique
        # user_id per item, so unrelated test cases (e.g. one asserting
        # Gold, another Platinum) never share a trace-store slot and produce
        # a spurious cross-test conflict. See data/trace_store.py docstring.
        user_id = f"test-user-{item['id']}"

        raw_lines.append(f"\n## {item['id']} (Group {item['group']}"
                          + (f", {item['subtype']}" if item.get("subtype") else "") + ")\n")
        raw_lines.append(f"**Query:** {item['query']}\n")

        seed_statements = item.get("seed_statements", [])
        if seed_statements:
            seed_session = query_session if item.get("seed_session", "same") == "same" else f"test-{item['id']}-prior"
            raw_lines.append(f"**Seed statements (user: {user_id}, session: {seed_session}):**\n")
            for stmt in seed_statements:
                try:
                    result = run_statement(stmt, user_id, seed_session)
                except OllamaUnavailableError as e:
                    print(f"ERROR extracting statement for {item['id']}: {e}")
                    sys.exit(1)
                raw_lines.append(f"- \"{stmt}\" -> {result['message']}\n")

        turns = store.get_turns(query_session)

        try:
            kg_res = run_kg(item["query"])
            cg_res = run_cg(item["query"], user_id, query_session, turns, use_cache=False)
        except OllamaUnavailableError as e:
            raw_lines.append(f"\n**ERROR calling Ollama: {e}**\n")
            print(f"ERROR on {item['id']}: {e}")
            sys.exit(1)

        raw_lines.append("\n**Condition A (KG) response:**\n")
        raw_lines.append(f"> {kg_res.answer}\n")
        raw_lines.append(
            f"tokens: prompt={kg_res.prompt_tokens}, completion={kg_res.completion_tokens}, total={kg_res.total_tokens}\n"
        )
        raw_lines.append(f"KG subgraph: {json.dumps(kg_res.graph_json)}\n")

        raw_lines.append("\n**Condition B (CG) response:**\n")
        raw_lines.append(f"> {cg_res.answer}\n")
        raw_lines.append(
            f"tokens: prompt={cg_res.prompt_tokens}, completion={cg_res.completion_tokens}, total={cg_res.total_tokens}\n"
        )
        raw_lines.append(
            f"CG fell back: {cg_res.fell_back}"
            + (f" (reason: {cg_res.fallback_reason})" if cg_res.fell_back else "") + "\n"
        )
        raw_lines.append(f"CG constructed subgraph: {json.dumps(cg_res.graph_json)}\n")

        subtype = item.get("subtype")
        kg_empty = len(kg_res.graph_json["nodes"]) == 0
        cg_empty = len(cg_res.graph_json["nodes"]) == 0

        if item["group"] == 1:
            kw = item["expected_keywords"]
            correct_a = keyword_hit(kg_res.answer, kw)
            correct_b = keyword_hit(cg_res.answer, kw)
            if kg_res.graph_json != cg_res.graph_json and not cg_res.fell_back:
                isolation_broken = True
                raw_lines.append(
                    "**ISOLATION WARNING: Group 1 query produced different KG/CG subgraphs "
                    "without a logged fallback.**\n"
                )
        elif subtype == "unanswerable":
            # Graded structurally, not by keyword guesswork: an honest
            # non-answer means the graph handed to the LLM was empty. The
            # model's own wording is reviewed manually in raw_log.md, not
            # auto-graded, since a heuristic can't reliably catch a
            # hallucinated-but-plausible-sounding fabrication.
            correct_a = kg_empty
            correct_b = cg_empty
        else:
            kw_a = item.get("expected_keywords_kg", [])
            kw_b = item.get("expected_keywords_cg", [])
            correct_a = keyword_hit(kg_res.answer, kw_a)
            correct_b = keyword_hit(cg_res.answer, kw_b)

        expect_fallback = item.get("expect_fallback")
        fallback_matches_expectation = (
            None if expect_fallback is None else (cg_res.fell_back == expect_fallback)
        )
        if fallback_matches_expectation is False:
            raw_lines.append(
                f"**FALLBACK EXPECTATION MISMATCH: expected fell_back={expect_fallback}, "
                f"got {cg_res.fell_back}.**\n"
            )

        table_rows.append({
            "id": item["id"], "group": item["group"], "subtype": subtype or "-",
            "tokens_a": kg_res.total_tokens, "tokens_b": cg_res.total_tokens,
            "correct_a": correct_a, "correct_b": correct_b,
            "cg_fallback": cg_res.fell_back,
        })

    raw_path = RESULTS_DIR / "raw_log.md"
    raw_path.write_text("".join(raw_lines), encoding="utf-8")

    def fmt(v):
        return "-" if v is None else ("y" if v else "n")

    table_lines = [
        "# Results table (50 questions)\n",
        "\n_correct_a / correct_b: 'y'/'n' where a keyword-containment heuristic (Group 1, "
        "same/prior-session) or graph-emptiness check (unanswerable) applies; '-' where neither "
        "does and the raw log must be read directly -- see raw_log.md._\n\n",
        "| id | group | subtype | tokens_A | tokens_B | correct_A | correct_B | cg_fallback |\n",
        "|---|---|---|---|---|---|---|---|\n",
    ]
    for row in table_rows:
        table_lines.append(
            f"| {row['id']} | {row['group']} | {row['subtype']} | {row['tokens_a']} | {row['tokens_b']} | "
            f"{fmt(row['correct_a'])} | {fmt(row['correct_b'])} | {'y' if row['cg_fallback'] else 'n'} |\n"
        )
    if isolation_broken:
        table_lines.append(
            "\n**ISOLATION BROKEN: at least one Group 1 (static-fact) query produced "
            "different KG/CG subgraphs. See raw_log.md warnings.**\n"
        )
    (RESULTS_DIR / "results_table.md").write_text("".join(table_lines), encoding="utf-8")

    group2_rows = [r for r in table_rows if r["group"] == 2]
    fallback_count = sum(1 for r in table_rows if r["cg_fallback"])
    group2_fallback_count = sum(1 for r in group2_rows if r["cg_fallback"])
    avg_tokens_a = sum(r["tokens_a"] for r in table_rows) / len(table_rows)
    avg_tokens_b = sum(r["tokens_b"] for r in table_rows) / len(table_rows)

    def count_graded(rows, key):
        graded = [r for r in rows if r[key] is not None]
        return sum(1 for r in graded if r[key]), len(graded)

    correct_a_n, correct_a_d = count_graded(table_rows, "correct_a")
    correct_b_n, correct_b_d = count_graded(table_rows, "correct_b")

    summary = f"""# KG vs CG -- 50-question experiment summary

Run: {datetime.datetime.now().isoformat()} | Model: local Ollama (see kg_cg_experiment/config.py)

- Queries run: {len(table_rows)} ({len([r for r in table_rows if r['group']==1])} Group 1 / {len(group2_rows)} Group 2)
- Isolation check (Group 1): {"BROKEN -- see results_table.md" if isolation_broken else "OK, no gap detected"}
- Avg tokens/query -- KG: {avg_tokens_a:.0f}, CG: {avg_tokens_b:.0f}
- CG fallback rate (all queries): {fallback_count}/{len(table_rows)}
- CG fallback rate (Group 2 only): {group2_fallback_count}/{len(group2_rows)}
- Auto-graded correct -- KG: {correct_a_n}/{correct_a_d}, CG: {correct_b_n}/{correct_b_d} (heuristic/structural, first pass only)

Full raw output: kg_cg_experiment/results/raw_log.md
Full table: kg_cg_experiment/results/results_table.md
"""
    (RESULTS_DIR / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"Wrote {raw_path}, results_table.md, summary.md under {RESULTS_DIR}")


if __name__ == "__main__":
    run_all()
