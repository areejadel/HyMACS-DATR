"""
assign_raters.py — distribute lectures across raters (overlapping design)
=========================================================================
Instead of having every rater score all 24 lectures, distribute them with overlap:
  - Each rater scores only ~ (24 x coverage / n_raters) lectures.
  - Each lecture is scored by (coverage) raters.
  - Overlap between raters => inter-rater agreement (Krippendorff alpha) is computable.

Produces:
  - allocation.csv          (rater -> list of their lectures)
  - rater_01.xlsx ... rater_NN.xlsx  (a personal form per rater, their lectures only)

Run:
    python experiments/assign_raters.py --raters 10 --coverage 3
"""
from __future__ import annotations
import sys, argparse, csv
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.build_human_eval import build_rating_form


def cyclic_assignment(ids, n_raters, coverage):
    """Balanced distribution: each lecture goes to the least-loaded raters (coverage distinct raters).
    => loads as equal as possible (difference <= 1) + enough overlap to compute agreement (alpha)."""
    loads = [0] * n_raters
    assign = {r: [] for r in range(n_raters)}
    for lid in ids:
        chosen = []
        for r in sorted(range(n_raters), key=lambda x: (loads[x], x)):
            chosen.append(r); loads[r] += 1
            if len(chosen) == coverage:
                break
        for r in chosen:
            assign[r].append(lid)
    return assign


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raters", type=int, default=10)
    ap.add_argument("--coverage", type=int, default=3, help="how many raters per lecture")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "human_eval"))
    args = ap.parse_args()

    OUT = Path(args.out)
    lec_dir = OUT / "01_selected_lectures"
    ids = sorted([p.stem for p in lec_dir.glob("L*.pdf")] or [p.stem for p in lec_dir.glob("L*.md")])
    if not ids:
        print(f"[!] no lectures in {lec_dir}. Run build_human_eval.py first."); return
    if args.coverage > args.raters:
        print("[!] coverage cannot exceed the number of raters."); return

    assign = cyclic_assignment(ids, args.raters, args.coverage)
    forms_dir = OUT / "02_rater_forms"; forms_dir.mkdir(parents=True, exist_ok=True)

    # allocation table
    with open(forms_dir / "allocation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["rater", "n_lectures", "lectures"])
        for r in range(args.raters):
            w.writerow([f"rater_{r+1:02d}", len(assign[r]), " ".join(assign[r])])

    # personal form per rater
    for r in range(args.raters):
        build_rating_form(sorted(assign[r]), forms_dir / f"rater_{r+1:02d}.xlsx")

    # coverage check
    cov = Counter(l for ls in assign.values() for l in ls)
    loads = [len(v) for v in assign.values()]
    print(f"[ok] {len(ids)} lectures · {args.raters} raters · coverage {args.coverage}")
    print(f"  load per rater: {min(loads)}-{max(loads)} lectures")
    print(f"  coverage per lecture: {min(cov.values())}-{max(cov.values())} raters  "
          f"({'ok all >= '+str(args.coverage) if min(cov.values())>=args.coverage else '[!] shortfall'})")
    print(f"  outputs -> {forms_dir}/  (allocation.csv + rater_01..{args.raters:02d}.xlsx)")


if __name__ == "__main__":
    main()
