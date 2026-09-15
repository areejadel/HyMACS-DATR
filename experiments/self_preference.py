"""
self_preference.py — self-preference matrix
========================================================
Measures self-preference bias rigorously (Panickssery et al. 2024):
does a model give a higher score to its own lecture than a cross-family panel does?

Design:
  - For each final lecture produced by generator g (from the saved run files):
      self_overall  = g's evaluation of itself (same model as judge — same-family/self)
      panel_overall = the cross-family panel median (already saved in external_overall)
      self_preference = self_overall - panel_overall
  - Aggregate per generator: mean self-preference gap +/- SE.

Cheap: reuses the saved lectures; the only new calls are
"the model judging itself" on the calibration set.

Run:
    TOPIC=backprop python experiments/self_preference.py --per-model 3
"""
from __future__ import annotations
import sys, json, argparse, random
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
import numpy as np

from config import RESULTS_DIR, RUBRIC_DIMENSIONS, GENERATORS, ACTIVE_TOPIC
from clients import get_client
from pipeline.judge_panel import _build_user_prompt, _parse_json, _JUDGE_SYSTEM_PROMPT


def _self_judge(model_key: str, lecture: str) -> dict:
    """Has the model judge a lecture itself (same-family judge)."""
    client = get_client(model_key)
    messages = [
        {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
        {"role": "user",   "content": _build_user_prompt(lecture)},
    ]
    res = client.generate(messages=messages, max_tokens=2500, temperature=0.2)
    if not getattr(res, "ok", False):
        return {"overall": 0.0, "scores": {}, "error": getattr(res, "error", "fail")}
    return _parse_json(res.text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-model", type=int, default=3,
                    help="number of lectures per generator in the calibration set")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    random.seed(args.seed)

    runs_dir = RESULTS_DIR / "runs"
    files = sorted(runs_dir.glob("*.json"))
    # collect the final lectures per generator (with the saved panel overall)
    by_model: dict[str, list[dict]] = defaultdict(list)
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("error") or not d.get("final_lecture"):
            continue
        if d.get("external_overall", 0) <= 0:        # we need the saved panel score
            continue
        by_model[d["model_key"]].append(d)

    if not by_model:
        print("No lectures with saved panel results. Run the experiment with USE_PANEL=1 first.")
        return

    rows = []
    print("=" * 64)
    print(f"  Self-preference matrix — subject: {ACTIVE_TOPIC}")
    print(f"  (self = model judges itself, panel = cross-family panel median)")
    print("=" * 64)

    per_model_gap: dict[str, list[float]] = {}
    for model_key in GENERATORS:
        runs = by_model.get(model_key, [])
        if not runs:
            continue
        sample = random.sample(runs, min(args.per_model, len(runs)))
        gaps = []
        for d in sample:
            self_eval = _self_judge(model_key, d["final_lecture"])
            if self_eval.get("error"):
                continue
            self_overall = self_eval["overall"]
            panel_overall = float(d["external_overall"])
            gap = self_overall - panel_overall
            gaps.append(gap)
            rows.append({
                "model_key": model_key,
                "family": GENERATORS[model_key].family,
                "run_id": d["run_id"],
                "self_overall": round(self_overall, 3),
                "panel_overall": round(panel_overall, 3),
                "self_preference": round(gap, 3),
            })
        if gaps:
            per_model_gap[model_key] = gaps
            mean = float(np.mean(gaps)); se = float(np.std(gaps, ddof=1) / np.sqrt(len(gaps))) if len(gaps) > 1 else 0.0
            fam = GENERATORS[model_key].family
            flag = "  [!] positive self-preference" if mean > 0.3 else ""
            print(f"  {model_key:<16}({fam:<9}) self-panel = {mean:+.2f} ± {se:.2f}  (n={len(gaps)}){flag}")

    # save
    import pandas as pd
    out = RESULTS_DIR / "self_preference_matrix.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8")
    print(f"\n[ok] saved: {out}")

    # overall summary
    all_gaps = [g for gs in per_model_gap.values() for g in gs]
    if all_gaps:
        print(f"\n  mean self-preference across all generators: {np.mean(all_gaps):+.3f}")
        print("  Interpretation: a systematic positive value => models over-rate themselves => a cross-family panel is justified.")


if __name__ == "__main__":
    main()
