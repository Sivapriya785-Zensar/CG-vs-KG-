"""Generates tests/demo_test_cases.md from test_queries.py -- the UI has no
built-in test picker, so this is what a presenter follows manually."""
from pathlib import Path

from kg_cg_experiment.tests.test_queries import GROUP1, PRIOR_SESSION, SAME_SESSION, UNANSWERABLE

OUT = Path(__file__).resolve().parent / "demo_test_cases.md"


def render_group1():
    lines = ["## Group 1 -- static facts (Question mode only, any session)\n"]
    for q in GROUP1:
        lines.append(f"- `{q['id']}` {q['query']}")
    return lines


def render_group2(items, label, note):
    lines = [f"\n## {label}\n", f"{note}\n"]
    for q in items:
        lines.append(f"### `{q['id']}`")
        if q["seed_statements"]:
            where = "a NEW session (click New session first), same customer" if q["seed_session"] == "prior" else "this session"
            lines.append(f"1. **Statement mode**, in {where}:")
            for s in q["seed_statements"]:
                lines.append(f"   - `{s}`")
            step = "2."
        else:
            step = "1."
        if q["seed_session"] == "prior" and q["seed_statements"]:
            lines.append(f"{step} Click **New session** (same customer), switch to **Question mode**, ask:")
        else:
            lines.append(f"{step} **Question mode**, ask:")
        lines.append(f"   - `{q['query']}`")
        lines.append("")
    return lines


def main():
    lines = [
        "# 50 test cases -- manual demo reference\n",
        "No UI picker on purpose -- type these in by hand to keep the demo honest and live.\n",
        "`New customer` before each Group 1 or `unanswerable` item if you want a clean slate; "
        "not required otherwise.\n",
    ]
    lines += render_group1()
    lines += render_group2(SAME_SESSION, "Group 2 -- same-session evidence", "Statement and question in the same session.")
    lines += render_group2(PRIOR_SESSION, "Group 2 -- prior-session evidence", "Statement in an earlier session, question in a new one -- same customer.")
    lines += render_group2(UNANSWERABLE, "Group 2 -- unanswerable", "Nothing on record and nothing in the policy schema; both sides should say so.")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
