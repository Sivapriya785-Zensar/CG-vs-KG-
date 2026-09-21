"""
Automated correctness grading for the large-scale CG-only run's raw log,
against test_queries_large.ALL_LARGE_QUERIES's programmatically-computed
expected_answer values. Full manual reading of 500 answers isn't feasible
in the available time, so this does fact-level matching instead: for each
question, checks whether the specific facts the expected_answer asserts
(dollar amounts, yes/no, day windows, category names) are actually present
and correctly stated in the CG answer text. This is a mechanical proxy for
correctness, not a substitute for human judgment on nuance/phrasing -- it
flags "PASS" only when the concrete facts match, "FAIL" when they're
missing/wrong/contradicted, and "UNCLEAR" when it can't tell either way.

Run:  python -m kg_cg_experiment.tests.grade_large_run
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kg_cg_experiment.tests.test_queries_large import ALL_LARGE_QUERIES

RAW_LOG = Path(__file__).resolve().parents[1] / "results_large" / "raw_log_chunk0.45_temp0.4.md"

ITEM_BY_ID = {item["id"]: item for item in ALL_LARGE_QUERIES}


def _extract_answer_block(raw_text: str, qid: str) -> str:
    pattern = rf"## {re.escape(qid)} \(.*?\n(.*?)(?=\n## |\Z)"
    m = re.search(pattern, raw_text, re.DOTALL)
    return m.group(1) if m else ""


def _cg_text(block: str) -> str:
    m = re.search(r"\*\*CG \(.*?\):\*\*\n> (.*?)(?=\nCatalog chunks retrieved|\Z)", block, re.DOTALL)
    return m.group(1).strip().lower() if m else ""


def _dollar_amounts(text: str) -> set[str]:
    return set(re.findall(r"\$(\d+(?:\.\d+)?)", text))


def grade_one(qid: str, expected: str, cg_answer: str) -> str:
    if not cg_answer:
        return "UNCLEAR"

    exp_lower = expected.lower()
    exp_dollars = _dollar_amounts(expected)
    cg_dollars = _dollar_amounts(cg_answer)

    says_no_info = any(p in cg_answer for p in [
        "not available in the current context", "don't have information",
        "does not provide", "no information", "cannot determine",
        "not mention", "doesn't mention",
    ])

    exp_is_yes = exp_lower.startswith("yes")
    exp_is_no = exp_lower.startswith("no")

    if exp_dollars:
        if exp_dollars.issubset(cg_dollars):
            if exp_is_no and "yes" in cg_answer[:60]:
                return "FAIL"
            return "PASS"
        if says_no_info or not cg_dollars:
            return "FAIL"
        return "FAIL"

    if exp_is_yes or exp_is_no:
        starts_yes = cg_answer.strip().startswith(("yes", "i'm happy to help! yes")) or " yes " in cg_answer[:80]
        starts_no = cg_answer.strip().startswith("no") or " no " in cg_answer[:40]
        if says_no_info:
            return "FAIL"
        if exp_is_yes and starts_yes and not starts_no:
            return "PASS"
        if exp_is_no and starts_no and not starts_yes:
            return "PASS"
        return "UNCLEAR"

    return "UNCLEAR"


def main():
    if not RAW_LOG.exists():
        print(f"ERROR: {RAW_LOG} not found.")
        sys.exit(1)

    raw_text = RAW_LOG.read_text(encoding="utf-8")
    results = []
    for item in ALL_LARGE_QUERIES:
        block = _extract_answer_block(raw_text, item["id"])
        cg_answer = _cg_text(block)
        verdict = grade_one(item["id"], item["expected_answer"], cg_answer)
        results.append((item["id"], item["category"], verdict))

    by_cat: dict[str, dict[str, int]] = {}
    for _qid, cat, verdict in results:
        by_cat.setdefault(cat, {"PASS": 0, "FAIL": 0, "UNCLEAR": 0})
        by_cat[cat][verdict] += 1

    total_pass = sum(1 for *_r, v in results if v == "PASS")
    total_fail = sum(1 for *_r, v in results if v == "FAIL")
    total_unclear = sum(1 for *_r, v in results if v == "UNCLEAR")
    n = len(results)

    print(f"Automated fact-level grading of {n} answers "
          f"(chunk=0.45, temp=0.4, CG-only, large-scale run)\n")
    print(f"{'Category':<12}{'PASS':>6}{'FAIL':>6}{'UNCLEAR':>9}{'n':>6}")
    for cat, counts in by_cat.items():
        cn = sum(counts.values())
        print(f"{cat:<12}{counts['PASS']:>6}{counts['FAIL']:>6}{counts['UNCLEAR']:>9}{cn:>6}")
    print(f"{'TOTAL':<12}{total_pass:>6}{total_fail:>6}{total_unclear:>9}{n:>6}")
    print(f"\nPASS rate (of all 500): {total_pass/n*100:.1f}%")
    print(f"PASS rate (excluding UNCLEAR): "
          f"{total_pass/(total_pass+total_fail)*100:.1f}%" if (total_pass + total_fail) else "n/a")

    out_path = RAW_LOG.parent / "grading_chunk0.45_temp0.4.md"
    lines = [f"# Automated fact-level grading -- chunk0.45_temp0.4\n\n",
             f"{n} questions graded mechanically against computed expected_answer facts "
             f"(dollar amounts / yes-no). PASS = concrete facts matched; FAIL = missing, wrong, "
             f"or contradicted; UNCLEAR = expected_answer had no checkable fact or CG answer "
             f"couldn't be parsed.\n\n",
             f"| Category | PASS | FAIL | UNCLEAR | n |\n|---|---|---|---|---|\n"]
    for cat, counts in by_cat.items():
        cn = sum(counts.values())
        lines.append(f"| {cat} | {counts['PASS']} | {counts['FAIL']} | {counts['UNCLEAR']} | {cn} |\n")
    lines.append(f"| **TOTAL** | {total_pass} | {total_fail} | {total_unclear} | {n} |\n\n")
    lines.append(f"PASS rate (of all 500): {total_pass/n*100:.1f}%\n\n")
    lines.append("## Per-question verdicts\n\n| id | category | verdict |\n|---|---|---|\n")
    for qid, cat, verdict in results:
        lines.append(f"| {qid} | {cat} | {verdict} |\n")
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
