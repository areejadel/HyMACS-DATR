"""
stats_v5.py — DATR statistical significance tests
==========================================================
Wilcoxon signed-rank (paired by model x seed) on the external score:
  - datr_full   vs no_refine     (does targeted refinement help?)
  - datr_full   vs self_refine    (targeted vs untargeted)
  - datr_full   vs datr_no_guard  (effect of the regression guard)
Per subject + pooled. Plus effect size (Cliff's delta).

Run:
    python experiments/stats_v5.py
"""
from __future__ import annotations
import sys, json, glob
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.stats import wilcoxon

MODELS = ["allam_7b","llama_3_8b","llama_3_3_70b","qwen3_235b","deepseek_v3_1","gemma_4_31b"]
SEEDS = [0,1,2,3,4]


def load_ext(topic):
    """(model,condition,seed) -> external_overall (for valid runs)."""
    d = {}
    for f in glob.glob(str(Path(__file__).resolve().parents[1] / "results" / topic / "runs" / "*.json")):
        r = json.load(open(f, encoding="utf-8"))
        if r.get("error") or not r.get("final_lecture"):
            continue
        e = float(r.get("external_overall") or 0)
        if e > 0:
            d[(r["model_key"], r["condition"], int(r["seed"]))] = e
    return d


def paired(data, cond_a, cond_b):
    """(model,seed) pairs shared between the two conditions."""
    a, b = [], []
    for m in MODELS:
        for s in SEEDS:
            ka, kb = (m, cond_a, s), (m, cond_b, s)
            if ka in data and kb in data:
                a.append(data[ka]); b.append(data[kb])
    return np.array(a), np.array(b)


def cliffs_delta(a, b):
    """Non-parametric effect size (-1..1)."""
    gt = sum(x > y for x in a for y in b); lt = sum(x < y for x in a for y in b)
    return (gt - lt) / (len(a) * len(b))


def test(data, a, b, label):
    xa, xb = paired(data, a, b)
    if len(xa) < 6:
        print(f"  {label:<28} n={len(xa)} (too few)"); return
    diff = xa - xb
    try:
        stat, p = wilcoxon(xa, xb)
    except ValueError:
        p = 1.0
    d = cliffs_delta(xa, xb)
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
    print(f"  {label:<28} n={len(xa):>2}  Δmean={diff.mean():+.3f}  p={p:.4f} {sig:<4} δ={d:+.2f}")


def main():
    print("Wilcoxon tests (external panel score) — paired by model x seed")
    print("(*** p<0.001 · ** p<0.01 · * p<0.05 · ns not significant · delta=Cliff's delta)")
    pooled = {}
    for topic in ["backprop", "normalization"]:
        data = load_ext(topic)
        for (k, v) in data.items():
            pooled[(topic,) + k] = v
        print(f"\n── {topic} ──")
        test(data, "datr_full", "no_refine",     "datr_full vs no_refine")
        test(data, "datr_full", "self_refine",    "datr_full vs self_refine")
        test(data, "datr_full", "datr_no_guard",  "datr_full vs datr_no_guard (guard)")

    # pooled across the two subjects
    print("\n── pooled (both subjects) ──")
    flat = defaultdict(dict)
    for (topic, m, c, s), v in pooled.items():
        flat[("pool",)][((topic, m), c, s)] = v
    pd = flat[("pool",)]
    def ppaired(ca, cb):
        a, b = [], []
        for key in pd:
            (tm, c, s) = key
            if c == ca:
                kb = (tm, cb, s)
                if kb in pd:
                    a.append(pd[key]); b.append(pd[kb])
        return np.array(a), np.array(b)
    for ca, cb, lab in [("datr_full","no_refine","datr_full vs no_refine"),
                        ("datr_full","self_refine","datr_full vs self_refine"),
                        ("datr_full","datr_no_guard","datr_full vs datr_no_guard (guard)")]:
        xa, xb = ppaired(ca, cb)
        if len(xa) >= 6:
            try: _, p = wilcoxon(xa, xb)
            except ValueError: p = 1.0
            sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else "ns"
            print(f"  {lab:<28} n={len(xa):>2}  Δmean={(xa-xb).mean():+.3f}  p={p:.4f} {sig:<4} δ={cliffs_delta(xa,xb):+.2f}")


if __name__ == "__main__":
    main()
