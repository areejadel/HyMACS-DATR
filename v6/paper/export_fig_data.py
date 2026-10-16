"""Exports per-lecture panel scores and human-aligned rows for the figures. Run from v6/: python paper/export_fig_data.py"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
import analyze_v6 as A
import common
from common import DIMS, composite, median_scores
common.setup("backprop")
V = A.load_v5(); J = A.load_judgements()
J["trunc"] = J["trunc"].fillna(0).astype(int); J["rep"] = J["rep"].fillna(1).astype(int)
P = A.build_v6_panel(V, J)
g = A.jlookup(J, "gpt4o", prompt="panel")
P["gpt4o_panelprompt"] = [g[(r.topic, r.run)].composite if (r.topic, r.run) in g else np.nan for r in P.itertuples()]
for d in DIMS:
    P["v6dim_" + d] = [median_scores([{"scores": s} for s in (getattr(r, "v6s_claude"), getattr(r, "v6s_kimi"), getattr(r, "v6s_glm")) if s]).get(d, np.nan) for r in P.itertuples()]
out = common.OUT_DIR / "paper_v6_stats"
cols = ["topic", "run", "model", "cond", "seed", "chars", "inner_comp", "inner_reported", "v5_panel_comp", "v5_panel_reported", "v6_panel", "v6_claude", "v6_kimi", "v6_glm", "v6_n", "gpt4o_panelprompt"] + ["v6dim_" + d for d in DIMS]
P[cols].to_csv(out / "lectures_240.csv", index=False)
H = A.load_human()
L = H.groupby(["lec", "topic", "run"]).h.agg(["mean", "count"]).reset_index().merge(P[cols], on=["topic", "run"], how="left")
L.to_csv(out / "human_lectures.csv", index=False)
print(len(P), len(L), H.rater.nunique())
