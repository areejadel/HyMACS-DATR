"""
panel_agreement.py — judge-panel agreement
=====================================================
Computes the reliability of the three external panel judges from
results/<topic>/runs/*.json.

Output:
  - Krippendorff's alpha (interval) per dimension + pooled  -> inter-judge agreement
  - Pairwise Spearman rho between judges on the overall score
  - Saves panel_agreement.csv

Run:
    TOPIC=backprop python experiments/panel_agreement.py
"""
from __future__ import annotations
import sys, json
from pathlib import Path
from itertools import combinations

sys.path.insert(0, str(Path(__file__).parent.parent))
import numpy as np

from config import RESULTS_DIR, RUBRIC_DIMENSIONS, ACTIVE_TOPIC


def krippendorff_alpha_interval(units: list[list[float]]) -> float:
    """
    Alpha (interval) with missing values. Each unit = list of judge ratings for one lecture.
    Canonical formula: alpha = 1 - Do/De  (distance = squared difference).
    """
    vals_per_unit = [[float(x) for x in u if x is not None] for u in units]
    vals_per_unit = [v for v in vals_per_unit if len(v) >= 2]   # only pairable units
    n = sum(len(v) for v in vals_per_unit)
    if n < 2:
        return float("nan")

    # observed disagreement (Do)
    do_num = 0.0
    for v in vals_per_unit:
        m = len(v)
        a = np.array(v)
        # sum_{i!=j} (a_i - a_j)^2 = 2*m*var* ... computed directly
        diff_sq = np.subtract.outer(a, a) ** 2
        do_num += diff_sq.sum() / (m - 1)
    do = do_num / n

    # expected disagreement (De) — over all pooled values
    pooled = np.array([x for v in vals_per_unit for x in v])
    diff_sq_all = np.subtract.outer(pooled, pooled) ** 2
    de = diff_sq_all.sum() / (n * (n - 1))
    if de == 0:
        return 1.0
    return 1.0 - do / de


def _spearman(x, y) -> float:
    try:
        from scipy.stats import spearmanr
        r, _ = spearmanr(x, y)
        return float(r)
    except Exception:
        # fallback: rank correlation by hand
        xr = np.argsort(np.argsort(x)); yr = np.argsort(np.argsort(y))
        return float(np.corrcoef(xr, yr)[0, 1])


def main():
    runs_dir = RESULTS_DIR / "runs"
    files = sorted(runs_dir.glob("*.json"))
    if not files:
        print(f"No results in {runs_dir}. Run the experiment first.")
        return

    # collect each judge's scores per run
    judge_roles: list[str] = []
    per_dim_units: dict[str, list[list[float]]] = {d: [] for d in RUBRIC_DIMENSIONS}
    overall_by_judge: dict[str, list[float]] = {}

    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("error"):
            continue
        panel = d.get("panel_per_judge") or {}
        if not panel:
            continue
        roles = [r for r, v in panel.items() if not v.get("error")]
        for r in roles:
            if r not in judge_roles:
                judge_roles.append(r)
                overall_by_judge[r] = []

        # per-dimension units
        for dim in RUBRIC_DIMENSIONS:
            row = []
            for r in judge_roles:
                v = panel.get(r, {})
                s = v.get("scores", {}).get(dim) if not v.get("error") else None
                row.append(float(s) if s else None)
            per_dim_units[dim].append(row)

        # per-judge overall (for Spearman) — filled in parallel only when all are available
        for r in judge_roles:
            v = panel.get(r, {})
            overall_by_judge[r].append(float(v.get("overall", 0.0)) if not v.get("error") else np.nan)

    if not judge_roles:
        print("No panel data (panel_per_judge) — did you run with USE_PANEL=1?")
        return

    # ── Krippendorff alpha per dimension + pooled ──
    print("=" * 60)
    print(f"  Judge-panel agreement — subject: {ACTIVE_TOPIC}")
    print(f"  Judges: {judge_roles}")
    print("=" * 60)
    rows = []
    pooled_units = []
    for dim in RUBRIC_DIMENSIONS:
        a = krippendorff_alpha_interval(per_dim_units[dim])
        rows.append({"dimension": dim, "krippendorff_alpha": round(a, 4)})
        pooled_units.extend(per_dim_units[dim])
        print(f"  {dim:<28} alpha = {a:+.3f}")
    a_pooled = krippendorff_alpha_interval(pooled_units)
    rows.append({"dimension": "POOLED_ALL_DIMS", "krippendorff_alpha": round(a_pooled, 4)})
    print(f"  {'POOLED (all dims)':<28} alpha = {a_pooled:+.3f}")

    # ── Pairwise Spearman on overall ──
    print("\n  Pairwise Spearman rho (on overall):")
    for r1, r2 in combinations(judge_roles, 2):
        x = np.array(overall_by_judge[r1]); y = np.array(overall_by_judge[r2])
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() >= 3:
            rho = _spearman(x[mask], y[mask])
            print(f"    {r1} <-> {r2}: rho = {rho:+.3f}  (n={int(mask.sum())})")

    import pandas as pd
    out = RESULTS_DIR / "panel_agreement.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8")
    print(f"\n[ok] saved: {out}")
    print("\nInterpretation: alpha >= 0.80 excellent, 0.67-0.80 acceptable for tentative conclusions, < 0.67 weak.")


if __name__ == "__main__":
    main()
