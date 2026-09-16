"""
Reads every variant folder under ../sweep_results/ (produced by run_sweep.ps1
at the repo root) and reports fallback rate + average token counts per
variant. Mechanical stats only, computed from index.md -- correctness
(Direct/Reasoning/Mixed, correct/partial/incorrect) still needs a manual read
of each variant's raw_log.md against its expected_answer, same discipline as
every other run in this project. No keyword-heuristic auto-grading.

One-off analysis tool, not part of the KG/CG pipeline -- safe to delete
alongside run_sweep.ps1 and sweep_results/ once you're done with it.

Run:  python -m kg_cg_experiment.tests.summarize_sweep
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "sweep_results"
ROW_RE = re.compile(r"^\|\s*(\S+)\s*\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\w)\s*\|")


def parse_index(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW_RE.match(line)
        if m:
            _id, category, _leak, tok_kg, tok_cg, fallback = m.groups()
            rows.append({
                "category": category,
                "tok_kg": int(tok_kg),
                "tok_cg": int(tok_cg),
                "fallback": fallback == "y",
            })
    return rows


def main():
    if not ROOT.exists():
        print(f"No {ROOT} -- run .\\run_sweep.ps1 first.")
        return

    print(f"{'variant':28} {'n':>4} {'fallback%':>10} {'avg_kg_tok':>11} {'avg_cg_tok':>11}")
    for variant_dir in sorted(ROOT.iterdir()):
        idx = variant_dir / "index.md"
        if not idx.exists():
            continue
        rows = parse_index(idx)
        if not rows:
            continue
        n = len(rows)
        fallback_pct = sum(r["fallback"] for r in rows) / n * 100
        avg_kg = sum(r["tok_kg"] for r in rows) / n
        avg_cg = sum(r["tok_cg"] for r in rows) / n
        print(f"{variant_dir.name:28} {n:4d} {fallback_pct:9.1f}% {avg_kg:11.1f} {avg_cg:11.1f}")

    print()
    print("Fallback% and token counts only. For correctness by Direct/Reasoning/"
          "Mixed, read each variant's raw_log.md against expected_answer manually.")


if __name__ == "__main__":
    main()
