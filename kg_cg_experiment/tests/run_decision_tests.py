"""
Runs the 24 decision scenarios live: 15 single-fact + 5 cross-session
chaining + 4 memory-interference stress tests. Real Ollama chat + real
embeddings throughout, unique user_id per scenario (except within a
chaining/interference scenario, which is deliberately one user_id across
multiple session_ids -- that's the point being tested).

This script is NOT run automatically as part of building this feature --
see the command at the bottom of README.md's Decision testing section.
Every LLM call costs real tokens on your local Ollama instance; nothing here
is precomputed or simulated, so results only exist once you actually run it.

Writes, under kg_cg_experiment/results_decisions/:
  - raw_log.md      every statement, every KG/CG decision (action +
                     reasoning + full raw response), real token counts
  - decision_table.md   id, expected, KG action, CG action, correct A/B,
                         fallback, tokens
  - fabrication_analysis.md   the centerpiece analysis: for every KG
                         response that asserts a specific tier/category with
                         no evidence to base it on, whether that assertion
                         was a lucky match or a real mismatch, and whether it
                         changed the ACTION taken (not just the wording) --
                         see run_decision_tests.py's `_classify_kg_assertion`
"""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kg_cg_experiment.agent.decision import run_cg_decision, run_kg_decision
from kg_cg_experiment.agent.llm_client import OllamaUnavailableError, is_available
from kg_cg_experiment.agent.runner import run_statement
from kg_cg_experiment.data import trace_store
from kg_cg_experiment.data.policy_dataset import NODES
from kg_cg_experiment.session import store
from kg_cg_experiment.tests.test_decisions import ALL_DECISION_SCENARIOS

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results_decisions"

_TIER_ALIASES = {a: n["label"] for n in NODES if n["type"] == "LoyaltyTier" for a in n["aliases"]}
_CATEGORY_ALIASES = {a: n["label"] for n in NODES if n["type"] == "ProductCategory" for a in n["aliases"]}


def _mentioned_labels(text: str, alias_map: dict) -> set:
    t = text.lower()
    return {label for alias, label in alias_map.items() if alias in t}


def _classify_kg_assertion(kg_response: str, real_tier: str | None, real_category: str | None) -> str | None:
    """KG never has evidence access -- any personalized tier/category name in
    its response is either a lucky coincidence or a genuine fabrication.
    Returns None if KG stayed appropriately generic (no personal assertion)."""
    tier_mentions = _mentioned_labels(kg_response, _TIER_ALIASES)
    category_mentions = _mentioned_labels(kg_response, _CATEGORY_ALIASES)

    notes = []
    for mention in tier_mentions:
        notes.append(f"tier={mention}" + (" (matches real)" if mention == real_tier else " (MISMATCH, real=" + str(real_tier) + ")"))
    for mention in category_mentions:
        notes.append(f"category={mention}" + (" (matches real)" if mention == real_category else " (MISMATCH, real=" + str(real_category) + ")"))
    return "; ".join(notes) if notes else None


def _run_single(item: dict, user_id: str, session_id: str, raw_lines: list, table_rows: list, fab_rows: list):
    real_tier = None
    real_category = None

    raw_lines.append(f"\n## {item['id']}\n")
    raw_lines.append(f"**Query:** {item['query']}\n")
    raw_lines.append(f"**Expected action:** {item['expected_action']}"
                      + (" (judgment call, see test_decisions.py)" if item.get("judgment_call") else "") + "\n")
    raw_lines.append(f"**Why:** {item['why']}\n")

    for stmt in item.get("seed_statements", []):
        result = run_statement(stmt, user_id, session_id)
        raw_lines.append(f"- Seed: \"{stmt}\" -> {result['message']}\n")
        for s in result["stored"]:
            if s["entity_key"] == "loyalty_tier":
                real_tier = s["value"]
            if s["entity_key"] == "product":
                real_category = s["value"]

    turns = store.get_turns(session_id)
    kg_res = run_kg_decision(item["query"])
    cg_res = run_cg_decision(item["query"], user_id, session_id, turns)

    _write_result(item, kg_res, cg_res, real_tier, real_category, raw_lines, table_rows, fab_rows)


def _write_result(item, kg_res, cg_res, real_tier, real_category, raw_lines, table_rows, fab_rows):
    raw_lines.append(f"\n**KG action: {kg_res.action}** ({kg_res.total_tokens} tokens, "
                      f"{kg_res.prompt_tokens}+{kg_res.completion_tokens})\n")
    raw_lines.append(f"> {kg_res.raw_response}\n")
    raw_lines.append(f"\n**CG action: {cg_res.action}** ({cg_res.total_tokens} tokens, "
                      f"{cg_res.prompt_tokens}+{cg_res.completion_tokens}"
                      + (f", FELL BACK: {cg_res.fallback_reason}" if cg_res.fell_back else "") + ")\n")
    raw_lines.append(f"> {cg_res.raw_response}\n")

    expected = item["expected_action"]
    correct_a = None if expected is None else (kg_res.action == expected)
    correct_b = None if expected is None else (cg_res.action == expected)

    table_rows.append({
        "id": item["id"], "expected": expected, "kg_action": kg_res.action, "cg_action": cg_res.action,
        "correct_a": correct_a, "correct_b": correct_b, "cg_fallback": cg_res.fell_back,
        "tokens_a": kg_res.total_tokens, "tokens_b": cg_res.total_tokens,
    })

    assertion = _classify_kg_assertion(kg_res.raw_response, real_tier, real_category)
    if assertion:
        fab_rows.append({
            "id": item["id"], "assertion": assertion, "kg_action": kg_res.action,
            "kg_correct": correct_a, "expected": expected,
        })


def run_all():
    if not is_available():
        print("ERROR: Ollama is not reachable. No results were produced -- nothing simulated.")
        sys.exit(1)

    RESULTS_DIR.mkdir(exist_ok=True)
    trace_store.clear_all()

    raw_lines = [f"# Decision scenarios -- raw log\n\nGenerated: {datetime.datetime.now().isoformat()}\n"]
    table_rows = []
    fab_rows = []

    raw_lines.append("\n# Single-fact scenarios\n")
    for item in ALL_DECISION_SCENARIOS["single_fact"]:
        session_id = f"dec-{item['id']}"
        store.reset(session_id)
        user_id = f"dec-user-{item['id']}"
        try:
            _run_single(item, user_id, session_id, raw_lines, table_rows, fab_rows)
        except OllamaUnavailableError as e:
            print(f"ERROR on {item['id']}: {e}")
            sys.exit(1)

    raw_lines.append("\n# Cross-session chaining scenarios\n")
    for item in ALL_DECISION_SCENARIOS["chaining"]:
        user_id = f"chain-user-{item['id']}"
        s1, s2, s3 = f"{item['id']}-s1", f"{item['id']}-s2", f"{item['id']}-s3"
        store.reset(s1); store.reset(s2); store.reset(s3)

        raw_lines.append(f"\n## {item['id']}\n")
        raw_lines.append(f"**Query:** {item['query']}\n**Expected action:** {item['expected_action']}\n**Why:** {item['why']}\n")

        real_tier = real_category = None
        r1 = run_statement(item["session1_statement"], user_id, s1)
        raw_lines.append(f"- Session 1 seed: \"{item['session1_statement']}\" -> {r1['message']}\n")
        for s in r1["stored"]:
            if s["entity_key"] == "loyalty_tier": real_tier = s["value"]
            if s["entity_key"] == "product": real_category = s["value"]

        r2 = run_statement(item["session2_statement"], user_id, s2)
        raw_lines.append(f"- Session 2 seed: \"{item['session2_statement']}\" -> {r2['message']}\n")
        for s in r2["stored"]:
            if s["entity_key"] == "loyalty_tier": real_tier = s["value"]
            if s["entity_key"] == "product": real_category = s["value"]

        try:
            kg_res = run_kg_decision(item["query"])
            cg_res = run_cg_decision(item["query"], user_id, s3, store.get_turns(s3))
        except OllamaUnavailableError as e:
            print(f"ERROR on {item['id']}: {e}")
            sys.exit(1)
        _write_result(item, kg_res, cg_res, real_tier, real_category, raw_lines, table_rows, fab_rows)

    raw_lines.append("\n# Memory-interference stress scenarios\n")
    for item in ALL_DECISION_SCENARIOS["interference"]:
        user_id = f"stress-user-{item['id']}"
        session_id = f"{item['id']}-store"
        store.reset(session_id)

        raw_lines.append(f"\n## {item['id']}\n")
        raw_lines.append(f"**Query:** {item['query']}\n**Expected action:** {item['expected_action']}\n**Why:** {item['why']}\n")
        raw_lines.append(f"**{len(item['statements'])} statements stored for this customer:**\n")

        real_tier = real_category = None
        for stmt in item["statements"]:
            r = run_statement(stmt, user_id, session_id)
            raw_lines.append(f"- \"{stmt}\" -> {r['message']}\n")
            for s in r["stored"]:
                if s["entity_key"] == "loyalty_tier": real_tier = s["value"]
                if s["entity_key"] == "product": real_category = s["value"]

        query_session = f"{item['id']}-query"
        store.reset(query_session)
        try:
            kg_res = run_kg_decision(item["query"])
            cg_res = run_cg_decision(item["query"], user_id, query_session, store.get_turns(query_session))
        except OllamaUnavailableError as e:
            print(f"ERROR on {item['id']}: {e}")
            sys.exit(1)
        _write_result(item, kg_res, cg_res, real_tier, real_category, raw_lines, table_rows, fab_rows)

    (RESULTS_DIR / "raw_log.md").write_text("".join(raw_lines), encoding="utf-8")

    def fmt(v):
        return "-" if v is None else ("y" if v else "n")

    table_lines = [
        "# Decision correctness table\n\n",
        "| id | expected | KG action | CG action | KG correct | CG correct | CG fallback | tokens A | tokens B |\n",
        "|---|---|---|---|---|---|---|---|---|\n",
    ]
    for r in table_rows:
        table_lines.append(
            f"| {r['id']} | {r['expected']} | {r['kg_action']} | {r['cg_action']} | {fmt(r['correct_a'])} | "
            f"{fmt(r['correct_b'])} | {'y' if r['cg_fallback'] else 'n'} | {r['tokens_a']} | {r['tokens_b']} |\n"
        )
    graded_a = [r for r in table_rows if r["correct_a"] is not None]
    graded_b = [r for r in table_rows if r["correct_b"] is not None]
    table_lines.append(
        f"\n**KG correct: {sum(1 for r in graded_a if r['correct_a'])}/{len(graded_a)}** "
        f"(of {len(graded_a)} scenarios with a defined expected action)\n"
        f"**CG correct: {sum(1 for r in graded_b if r['correct_b'])}/{len(graded_b)}**\n"
    )
    (RESULTS_DIR / "decision_table.md").write_text("".join(table_lines), encoding="utf-8")

    fab_lines = [
        "# Fabrication -> action analysis\n\n",
        "KG never has access to any customer-specific fact -- it only ever sees the "
        "static policy graph. Every row below is a case where KG's response nonetheless "
        "named a specific tier or product category. That's not evidence-based reasoning; "
        "it's the model filling a personalization gap on its own. This table shows whether "
        "doing so happened to be harmless (right action anyway) or actually changed the "
        "action taken -- which is the real-world risk this represents: a fabricated "
        "intermediate claim silently becoming a wrong downstream decision.\n\n",
        "| id | KG's fabricated assertion | KG action | matched expected? |\n",
        "|---|---|---|---|\n",
    ]
    if fab_rows:
        for r in fab_rows:
            fab_lines.append(f"| {r['id']} | {r['assertion']} | {r['kg_action']} | {fmt(r['kg_correct'])} |\n")
        mismatches_wrong_action = [r for r in fab_rows if r["kg_correct"] is False]
        fab_lines.append(
            f"\n**{len(fab_rows)}/{len(table_rows)} scenarios show KG asserting an ungrounded personal fact. "
            f"{len(mismatches_wrong_action)} of those led to a WRONG action, not just wrong wording.**\n"
        )
    else:
        fab_lines.append("\n(No fabricated assertions detected in this run -- KG stayed generic throughout.)\n")
    (RESULTS_DIR / "fabrication_analysis.md").write_text("".join(fab_lines), encoding="utf-8")

    print(f"Wrote raw_log.md, decision_table.md, fabrication_analysis.md under {RESULTS_DIR}")


if __name__ == "__main__":
    run_all()
