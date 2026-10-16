"""paper_stats.py — numbers for access_v6.tex that are not in report_v6.md.
Usage (from v6/): python paper/paper_stats.py results_v6 results_v6/paper_v6_stats ..   (last arg: v5 dir holding results/)"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RES = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
MODELS = ["allam_7b", "llama_3_8b", "llama_3_3_70b", "gemma_4_31b", "deepseek_v3_1", "qwen3_235b"]
WEAK = {"allam_7b", "llama_3_8b", "llama_3_3_70b"}
rng = np.random.default_rng(7)


def boot_mean(d, n=4000):
    d = np.asarray(d, float)
    bs = [rng.choice(d, len(d)).mean() for _ in range(n)]
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


# ---------- exp1 ----------
R, D = [], {}
for t in ["backprop", "normalization"]:
    for f in glob.glob(str(RES / f"exp1/{t}/drafts*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            D[r["key"]] = r
    seen = {}
    for f in glob.glob(str(RES / f"exp1/{t}/runs*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            seen[r["key"]] = r
    for r in seen.values():
        if r.get("error") or r["panel"]["n_ok"] < 3:
            continue
        if r["model_key"] not in ("allam_7b", "llama_3_8b") and not r["settings"].get("guard_v2"):
            continue
        R.append(r)
drafts = pd.DataFrame([dict(topic=d["topic"], model=d["model_key"], seed=d["seed"],
                            panel=d["panel"]["composite"], inner=d["inner"]["composite"],
                            chars=d["lecture_chars"]) for d in D.values() if not d.get("error")])
runs = pd.DataFrame([dict(topic=r["topic"], model=r["model_key"], seed=r["seed"], cond=r["condition"],
                          panel=r["panel_composite"], draft=r["draft_panel_composite"],
                          calls=sum(len(it.get("agents", [])) for it in r["iterations"][1:]),
                          rb=r["n_rollbacks"], rounds=r["n_rounds"], chars=r["final_chars"],
                          elapsed=r["elapsed_sec"], final_is_draft=r["final_is_draft"]) for r in R])
runs["delta"] = runs.panel - runs.draft
runs["tier"] = np.where(runs.model.isin(WEAK), "weak", "strong")
nr = drafts.assign(cond="no_refine", delta=0.0)
ALL = pd.concat([nr[["topic", "model", "seed", "cond", "panel"]], runs[["topic", "model", "seed", "cond", "panel"]]])
cell = ALL.groupby(["model", "topic", "cond"]).panel.agg(["mean", "sem"]).reset_index()
cell.to_csv(OUT / "exp1_cells.csv", index=False)
gap = drafts.groupby(["model", "topic"])[["inner", "panel"]].mean().reset_index()
gap["gap"] = gap.inner - gap.panel
gap.to_csv(OUT / "exp1_draft_gap.csv", index=False)

eff = runs.groupby("cond").agg(calls=("calls", "mean"), rollbacks=("rb", "mean"), elapsed=("elapsed", "mean"),
                               delta=("delta", "mean"), keep_draft=("final_is_draft", "mean")).reset_index()
eff.to_csv(OUT / "exp1_efficiency.csv", index=False)

tier = []
for (tr, c), g in runs.groupby(["tier", "cond"]):
    lo, hi = boot_mean(g.delta)
    tier.append(dict(tier=tr, cond=c, n=len(g), delta=g.delta.mean(), lo=lo, hi=hi,
                     p=stats.wilcoxon(g.delta).pvalue if (g.delta != 0).any() else 1.0))
pd.DataFrame(tier).to_csv(OUT / "exp1_tier.csv", index=False)

W = ALL.pivot_table(index=["topic", "model", "seed"], columns="cond", values="panel")
pairs = []
for a, b in [("self_refine", "no_refine"), ("self_refine_guard", "no_refine"), ("datr_no_guard", "no_refine"),
             ("datr_full", "no_refine"), ("datr_composite_guard", "no_refine"),
             ("datr_full", "self_refine_guard"), ("datr_composite_guard", "self_refine"),
             ("datr_full", "self_refine"), ("datr_full", "datr_no_guard"),
             ("datr_composite_guard", "datr_full")]:
    d = (W[a] - W[b]).dropna()
    lo, hi = boot_mean(d)
    pairs.append(dict(a=a, b=b, n=len(d), delta=d.mean(), lo=lo, hi=hi, p=stats.wilcoxon(d).pvalue))
P = pd.DataFrame(pairs)
# Holm over this family of 10
order = np.argsort(P.p.values)
m = len(P)
adj = np.empty(m)
run_max = 0
for k, i in enumerate(order):
    run_max = max(run_max, (m - k) * P.p.values[i])
    adj[i] = min(1.0, run_max)
P["p_holm"] = adj
P.to_csv(OUT / "exp1_pairs.csv", index=False)

# ---------- calibrated self-preference (exp4) ----------
J = pd.DataFrame([json.loads(l) for l in open(RES / "judgements.jsonl")])
X = J[(J.experiment == "exp4") & J.error.isna()].copy()
X["lec"] = X.topic + "|" + X.run
X["y"] = X.composite.astype(float)
pan = X[X.role.isin(["claude", "kimi", "glm"])].groupby("lec").y.median()
gen_of = X.groupby("lec").model_key.first()
sp = []
for mk in MODELS:
    Jm = X[X.role == f"gen:{mk}"].set_index("lec").y
    if Jm.empty:
        continue
    own = [l for l in Jm.index if gen_of[l] == mk]
    oth = [l for l in Jm.index if gen_of[l] != mk]

    def est(o, t):
        b, a = np.polyfit(pan[t].values, Jm[t].values, 1)
        return float(np.mean(Jm[o].values - (a + b * pan[o].values))), float(b)
    e, b = est(own, oth)
    bs = [est(list(rng.choice(own, len(own))), list(rng.choice(oth, len(oth))))[0] for _ in range(4000)]
    r_oth = stats.spearmanr(pan[oth].values, Jm[oth].values)[0]
    sp.append(dict(model=mk, naive=float(np.mean(Jm[own].values - pan[own].values)),
                   leniency=float(np.mean(Jm[oth].values - pan[oth].values)), slope=b, rho_others=r_oth,
                   self_cal=e, lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)),
                   judge_range=float(X[X.role == f"gen:{mk}"].groupby("model_key").y.mean().max()
                                     - X[X.role == f"gen:{mk}"].groupby("model_key").y.mean().min())))
pd.DataFrame(sp).to_csv(OUT / "selfpref_calibrated.csv", index=False)
cross = X.pivot_table(index="role", columns="model_key", values="y", aggfunc="mean")
cross.to_csv(OUT / "cross_matrix.csv")

# ---------- per-dimension alpha of the v6 panel (Claude from v5 runs + Kimi-K3 + GLM-5.2) ----------
def kalpha(matrix):
    units = [r[~np.isnan(r)] for r in np.asarray(matrix, float)]
    units = [u for u in units if len(u) >= 2]
    n = sum(len(u) for u in units)
    do = sum((np.subtract.outer(u, u) ** 2).sum() / (len(u) - 1) for u in units) / n
    pooled = np.concatenate(units)
    de = (np.subtract.outer(pooled, pooled) ** 2).sum() / (n * (n - 1))
    return 1 - do / de


DIMS = ["academic_accuracy", "pedagogical_effectiveness", "clarity_organization", "practical_relevance",
        "completeness", "engagement_potential", "technical_quality", "innovation"]
V5 = (Path(sys.argv[3]) / "results") if len(sys.argv) > 3 else None
A = J[(J.experiment == "exp2A") & J.error.isna() & (J.rep == 1)]
claude = {}
if V5:
    for t in ["backprop", "normalization"]:
        for f in glob.glob(str(V5 / t / "runs" / "*.json")):
            if Path(f).name.startswith("._"):
                continue
            d = json.load(open(f))
            v = (d.get("panel_per_judge") or {}).get("judge_claude") or {}
            if v and not v.get("error"):
                claude[(t, Path(f).stem)] = v["scores"]
for r in J[(J.experiment == "exp2A") & (J.role == "claude") & J.error.isna()].itertuples():
    claude[(r.topic, r.run)] = r.scores          # Claude re-judged where it failed in v5
rows = []
for t in ["backprop", "normalization", "pooled"]:
    s = A if t == "pooled" else A[A.topic == t]
    runs_ = sorted(set(zip(s.topic, s.run)))
    ki = {(r.topic, r.run): r.scores for r in s[s.role == "kimi"].itertuples()}
    gl = {(r.topic, r.run): r.scores for r in s[s.role == "glm"].itertuples()}
    for d in DIMS + ["composite"]:
        mat = []
        for k in runs_:
            row = []
            for src in (claude, ki, gl):
                sc = src.get(k)
                if d == "composite":
                    v = np.mean([float(sc[x]) for x in DIMS]) if sc and all(sc.get(x) for x in DIMS) else np.nan
                else:
                    v = float(sc[d]) if sc and sc.get(d) else np.nan
                row.append(v)
            mat.append(row)
        rows.append(dict(topic=t, dim=d, alpha=kalpha(np.array(mat)), n=len(runs_)))
pd.DataFrame(rows).to_csv(OUT / "alpha_dim_v6.csv", index=False)
print("ok", len(runs), len(drafts))
