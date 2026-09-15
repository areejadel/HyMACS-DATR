"""
aggregate_results.py
====================
Collects all JSON files from results/runs/ into a single DataFrame and saves a CSV.

Each row = one run, with:
  run_id, model_key, condition, seed, timestamp,
  inner_overall, ext_overall, gap,
  inner_<dim> x 8, ext_<dim> x 8, gap_<dim> x 8,
  initial_inner_overall, improvement,
  rounds_count, rollback_count,
  total_elapsed_sec, error

Run:
    python experiments/aggregate_results.py
    python experiments/aggregate_results.py --runs-dir custom/path --out custom.csv
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from config import RUBRIC_DIMENSIONS, RESULTS_DIR


def _safe(d: dict, *keys, default=None):
    """Safely walk nested keys."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is default:
            return default
    return cur


def parse_run(path: Path) -> Optional[dict]:
    """Flatten a single JSON file into a dict."""
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(f"  [!] skipping {path.name}: {e}")
        return None

    if d.get("error"):
        # keep the row but with the error recorded
        return {
            "run_id":       d.get("run_id", path.stem),
            "model_key":    d.get("model_key"),
            "condition":    d.get("condition"),
            "seed":         d.get("seed"),
            "timestamp":    d.get("timestamp"),
            "error":        d.get("error"),
            "inner_overall": None,
            "ext_overall":   None,
            "gap":           None,
        }

    # main fields
    inner_overall = float(d.get("final_inner_overall") or 0.0)
    ext_overall   = float(d.get("external_overall")   or 0.0)
    gap           = inner_overall - ext_overall

    inner_scores = d.get("final_inner_scores") or {}
    ext_scores   = d.get("external_scores")   or {}

    # iterations
    iters = d.get("iterations") or []
    initial = iters[0] if iters else {}
    initial_inner_overall = float(initial.get("inner_overall") or 0.0)
    rounds_count    = max(0, len(iters) - 1)              # iter[0] = initial draft
    rollback_count  = sum(1 for it in iters if it.get("rolled_back"))

    row = {
        "run_id":      d.get("run_id", path.stem),
        "model_key":   d.get("model_key"),
        "condition":   d.get("condition"),
        "seed":        d.get("seed"),
        "timestamp":   d.get("timestamp"),
        "error":       None,

        "inner_overall":           round(inner_overall, 3),
        "ext_overall":             round(ext_overall,   3),
        "gap":                     round(gap,           3),

        "initial_inner_overall":   round(initial_inner_overall, 3),
        "improvement":             round(inner_overall - initial_inner_overall, 3),

        "rounds_count":            rounds_count,
        "rollback_count":          rollback_count,
        "rollback_rate":           round(rollback_count / rounds_count, 3) if rounds_count > 0 else 0.0,

        "total_elapsed_sec":       round(float(d.get("total_elapsed_sec") or 0.0), 1),
        "lecture_chars":           len(d.get("final_lecture") or ""),
    }

    # 8 inner dims + 8 ext dims + 8 gap dims
    for dim in RUBRIC_DIMENSIONS:
        i_val = float(inner_scores.get(dim, 0.0) or 0.0)
        e_val = float(ext_scores.get(dim,   0.0) or 0.0)
        row[f"inner_{dim}"] = round(i_val, 2)
        row[f"ext_{dim}"]   = round(e_val, 2)
        row[f"gap_{dim}"]   = round(i_val - e_val, 2)

    return row


def aggregate(runs_dir: Path) -> pd.DataFrame:
    """Collect all JSON into a single DataFrame."""
    files = sorted(runs_dir.glob("*.json"))
    print(f"File count: {len(files)}")

    rows = []
    skipped = 0
    for f in files:
        row = parse_run(f)
        if row is None:
            skipped += 1
            continue
        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"[ok] {len(df)} rows / [!] {skipped} skipped\n")

    return df


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Summary table: mean +/- SE per (model, condition)."""
    valid = df[df["error"].isna()].copy()
    grp = valid.groupby(["model_key", "condition"])

    n_groups = grp.size()
    summary = grp.agg(
        n_runs        =("run_id",        "count"),
        inner_mean    =("inner_overall", "mean"),
        inner_std     =("inner_overall", "std"),
        ext_mean      =("ext_overall",   "mean"),
        ext_std       =("ext_overall",   "std"),
        gap_mean      =("gap",           "mean"),
        gap_std       =("gap",           "std"),
        improvement   =("improvement",   "mean"),
        rollback_rate =("rollback_rate", "mean"),
        elapsed_sec   =("total_elapsed_sec", "mean"),
    ).round(3)

    # SE = std / sqrt(n)
    summary["inner_se"] = (summary["inner_std"] / (summary["n_runs"] ** 0.5)).round(3)
    summary["ext_se"]   = (summary["ext_std"]   / (summary["n_runs"] ** 0.5)).round(3)
    summary["gap_se"]   = (summary["gap_std"]   / (summary["n_runs"] ** 0.5)).round(3)

    # column order
    cols = [
        "n_runs",
        "inner_mean", "inner_se",
        "ext_mean",   "ext_se",
        "gap_mean",   "gap_se",
        "improvement",
        "rollback_rate",
        "elapsed_sec",
    ]
    return summary[cols].reset_index()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", type=Path,
                        default=RESULTS_DIR / "runs",
                        help="folder of JSON files")
    parser.add_argument("--out", type=Path,
                        default=RESULTS_DIR / "master_results.csv",
                        help="output CSV file")
    parser.add_argument("--summary-out", type=Path,
                        default=RESULTS_DIR / "summary_by_condition.csv",
                        help="summary file per (model, condition)")
    args = parser.parse_args()

    if not args.runs_dir.exists():
        print(f"[x] folder not found: {args.runs_dir}")
        sys.exit(1)

    print(f"runs_dir: {args.runs_dir}")
    print(f"out:      {args.out}\n")

    df = aggregate(args.runs_dir)

    # save master CSV
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"[ok] master CSV: {args.out}  ({len(df)} runs)")

    # save summary CSV
    summary = summary_table(df)
    summary.to_csv(args.summary_out, index=False, encoding="utf-8")
    print(f"[ok] summary CSV: {args.summary_out}  ({len(summary)} rows)\n")

    # print the summary
    print("=" * 90)
    print("  SUMMARY — mean inner / external / gap per (model, condition)")
    print("=" * 90)
    print(f"  {'model':<18}{'cond':<16}{'n':>3}  {'inner±SE':<14}{'ext±SE':<14}{'gap±SE':<14}{'rb%':>6}")
    print("  " + "-" * 86)
    for _, r in summary.iterrows():
        m  = r["model_key"][:17]
        c  = r["condition"][:15]
        n  = int(r["n_runs"])
        innr = f"{r['inner_mean']:.2f}±{r['inner_se']:.2f}"
        extr = f"{r['ext_mean']:.2f}±{r['ext_se']:.2f}"
        gapr = f"{r['gap_mean']:+.2f}±{r['gap_se']:.2f}"
        rb   = f"{r['rollback_rate']*100:.0f}%"
        print(f"  {m:<18}{c:<16}{n:>3}  {innr:<14}{extr:<14}{gapr:<14}{rb:>6}")
    print()

    # per-model summary only
    print("=" * 60)
    print("  GAP per model (averaged over all conditions)")
    print("=" * 60)
    valid = df[df["error"].isna()]
    by_model = valid.groupby("model_key").agg(
        n=("run_id", "count"),
        inner=("inner_overall", "mean"),
        ext=("ext_overall", "mean"),
        gap=("gap", "mean"),
        gap_std=("gap", "std"),
    ).round(2).sort_values("gap", ascending=False)
    print(by_model.to_string())
    print()


if __name__ == "__main__":
    main()
