"""baselines_stats.py — Study B with the two cost/guard-matched baselines.
Usage: python baselines_stats.py <results_v6 dir> <out dir>
Conditions: no_refine (draft), self_refine, self_refine_guard, datr_no_guard, datr_full (per-dim guard),
datr_composite_guard, datr_random_composite (2 random dims + composite guard), self_refine_composite."""
import glob, json, sys, itertools
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
DIMS = ["academic_accuracy", "pedagogical_effectiveness", "clarity_organization", "practical_relevance",
        "completeness", "engagement_potential", "technical_quality", "innovation"]
WEAK = {"allam_7b", "llama_3_8b", "llama_3_3_70b"}
NEW = ("datr_random_composite", "self_refine_composite")
rng = np.random.default_rng(7)

def boot(d, n=4000):
    d = np.asarray(d, float); b = [rng.choice(d, len(d)).mean() for _ in range(n)]
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))

def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for k, i in enumerate(o):
        run = max(run, (m - k) * p[i]); adj[i] = min(1, run)
    return adj

D, R = {}, {}
for t in ["backprop", "normalization"]:
    for f in glob.glob(str(RES / f"exp1/{t}/drafts*.jsonl")):
        for l in open(f): r = json.loads(l); D[r["key"]] = r
    for f in glob.glob(str(RES / f"exp1/{t}/runs*.jsonl")):
        for l in open(f): r = json.loads(l); R[r["key"]] = r
runs = []
for r in R.values():
    if r["panel"]["n_ok"] < 3: continue
    # same rule as paper_stats for the original five; new baselines: a run whose single revision call failed
    # after retries kept the previous text for that round and is complete -> included (sensitivity below)
    if r.get("error") and r["condition"] not in NEW: continue
    if r["model_key"] not in ("allam_7b", "llama_3_8b") and not r["settings"].get("guard_v2"): continue
    runs.append(r)
dk = {(d["topic"], d["model_key"], d["seed"]): d for d in D.values() if not d.get("error")}
rows = []
for r in runs:
    d = dk[(r["topic"], r["model_key"], r["seed"])]
    acc_t = set()
    for it in r["iterations"][1:]:
        if not it.get("rolled_back"): acc_t |= set(it.get("targets", []))
    tg1 = r["iterations"][1].get("targets", []) if len(r["iterations"]) > 1 else []
    rows.append(dict(topic=r["topic"], model=r["model_key"], seed=r["seed"], cond=r["condition"],
                     panel=r["panel_composite"], draft=r["draft_panel_composite"],
                     calls=sum(len(it.get("agents", [])) for it in r["iterations"][1:]),
                     props=sum(1 for it in r["iterations"][1:] if "proposed_composite" in it),
                     rb=r["n_rollbacks"], keep=r["final_is_draft"], elapsed=r["elapsed_sec"],
                     flag=bool(r.get("error")), deg=r.get("n_degenerate_retries", 0),
                     dims={k: r["panel"]["median_scores"][k] - d["panel"]["median_scores"][k] for k in DIMS},
                     acc_t=acc_t, tg1=tg1, draft_dims=d["panel"]["median_scores"],
                     inner_draft=d["inner"]["scores"]))
X = pd.DataFrame(rows); X["delta"] = X.panel - X.draft
X["tier"] = np.where(X.model.isin(WEAK), "weak", "strong"); X["cell"] = X.topic + "|" + X.model
C = ["self_refine", "self_refine_guard", "datr_no_guard", "datr_full", "datr_composite_guard",
     "datr_random_composite", "self_refine_composite"]
W = X.pivot_table(index=["topic", "model", "seed"], columns="cond", values="delta")
W["no_refine"] = 0.0
out = {"n_runs": {c: int((X.cond == c).sum()) for c in C}, "n_flagged_new": int(X[X.cond.isin(NEW)].flag.sum()),
       "deg_retries_qwen": int(X[(X.model == "qwen3_235b") & X.cond.isin(NEW)].deg.sum())}

# efficiency
eff = X.groupby("cond").agg(gain=("delta", "mean"), calls=("calls", "mean"), props=("props", "sum"),
                            rb=("rb", "sum"), keep=("keep", "mean"), elapsed=("elapsed", "mean")).reindex(C)
eff["reject_rate"] = eff.rb / eff.props
for c in C:
    lo, hi = boot(X[X.cond == c].delta); eff.loc[c, "lo"], eff.loc[c, "hi"] = lo, hi
eff.to_csv(OUT / "b_efficiency.csv")

# pairs: original 10 + new 5 = family of 15
P = [("self_refine", "no_refine"), ("self_refine_guard", "no_refine"), ("datr_no_guard", "no_refine"),
     ("datr_full", "no_refine"), ("datr_composite_guard", "no_refine"),
     ("datr_full", "self_refine_guard"), ("datr_composite_guard", "self_refine"),
     ("datr_full", "self_refine"), ("datr_full", "datr_no_guard"), ("datr_composite_guard", "datr_full"),
     ("datr_random_composite", "no_refine"), ("self_refine_composite", "no_refine"),
     ("datr_composite_guard", "datr_random_composite"), ("datr_composite_guard", "self_refine_composite"),
     ("self_refine_composite", "self_refine")]
pr = []
for a, b in P:
    d = (W[a] - W[b]).dropna(); lo, hi = boot(d)
    p = stats.wilcoxon(d).pvalue if (d != 0).any() else 1.0
    pr.append(dict(a=a, b=b, n=len(d), delta=d.mean(), lo=lo, hi=hi, p=p))
PP = pd.DataFrame(pr); PP["p_holm15"] = holm(PP.p); PP["p_holm10_orig"] = np.nan
PP.loc[:9, "p_holm10_orig"] = holm(PP.p[:10])
PP.to_csv(OUT / "b_pairs.csv", index=False)

# cluster bootstrap (12 cells) for key contrasts
def cboot(a, b, n=4000):
    d = (W[a] - W[b]).dropna().reset_index(); d["cell"] = d.topic + "|" + d.model; d["v"] = d[0] if 0 in d else d.iloc[:, -2]
    g = {k: v.v.values for k, v in d.groupby("cell")}; ks = list(g)
    bs = [np.concatenate([g[k] for k in rng.choice(ks, len(ks))]).mean() for _ in range(n)]
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
key = [("datr_composite_guard", "datr_random_composite"), ("datr_composite_guard", "self_refine_composite"),
       ("datr_random_composite", "no_refine")]
out["cluster"] = {f"{a}-{b}": cboot(a, b) for a, b in key}

# TOST DATR comp vs SR comp (paired t, +-0.15 and +-0.10)
d = (W.datr_composite_guard - W.self_refine_composite).dropna()
for eps in (0.15, 0.10):
    p1 = stats.ttest_1samp(d, -eps, alternative="greater").pvalue; p2 = stats.ttest_1samp(d, eps, alternative="less").pvalue
    out[f"tost_vs_srcomp_{eps}"] = float(max(p1, p2))
# rank-biserial
def rbc(x):
    x = np.asarray(x); x = x[x != 0]; r = stats.rankdata(np.abs(x)); return float((r[x > 0].sum() - r[x < 0].sum()) / r.sum())
out["rbc"] = {c: rbc(W[c].dropna()) for c in C}
out["rbc_datr_vs_random"] = rbc((W.datr_composite_guard - W.datr_random_composite).dropna())

# tiers
tier = []
for (tr, c), g in X.groupby(["tier", "cond"]):
    lo, hi = boot(g.delta); tier.append(dict(tier=tr, cond=c, n=len(g), delta=g.delta.mean(), lo=lo, hi=hi))
pd.DataFrame(tier).to_csv(OUT / "b_tier.csv", index=False)
for tr in ("weak", "strong"):
    Wt = W[W.index.get_level_values("model").isin(WEAK) == (tr == "weak")]
    dd = (Wt.datr_composite_guard - Wt.datr_random_composite).dropna(); lo, hi = boot(dd)
    out[f"tier_{tr}_datr_minus_random"] = (float(dd.mean()), lo, hi, float(stats.wilcoxon(dd).pvalue))
    dd = (Wt.datr_composite_guard - Wt.self_refine_composite).dropna(); lo, hi = boot(dd)
    out[f"tier_{tr}_datr_minus_srcomp"] = (float(dd.mean()), lo, hi, float(stats.wilcoxon(dd).pvalue))

# robustness of DATR - random
rob = {}
def contrast(mask_fn, a="datr_composite_guard", b="datr_random_composite"):
    Wm = W[[mask_fn(i) for i in W.index]]; dd = (Wm[a] - Wm[b]).dropna(); lo, hi = boot(dd)
    return dict(n=len(dd), delta=float(dd.mean()), lo=lo, hi=hi, p=float(stats.wilcoxon(dd).pvalue))
for m in sorted(X.model.unique()):
    rob[f"without_{m}"] = contrast(lambda i, m=m: i[1] != m)
flagged = set(map(tuple, X[X.flag][["topic", "model", "seed"]].values))
rob["without_flagged_qwen"] = contrast(lambda i: i not in flagged)
rob["srcomp_without_flagged"] = contrast(lambda i: i not in flagged, b="self_refine_composite")
for t in ("backprop", "normalization"):
    rob[f"only_{t}"] = contrast(lambda i, t=t: i[0] == t)
out["robust_datr_minus_random"] = rob

# targeting: gain on accepted-targeted dims vs others, DATR comp vs random comp
tg = []
for c in ("datr_composite_guard", "datr_random_composite", "datr_full"):
    for _, r in X[X.cond == c].iterrows():
        if not r.acc_t: continue
        on = np.mean([r.dims[k] for k in r.acc_t]); off = [r.dims[k] for k in DIMS if k not in r.acc_t]
        tg.append(dict(cond=c, key=(r.topic, r.model, r.seed), on=on, off=np.mean(off) if off else np.nan))
TG = pd.DataFrame(tg); out["targeting"] = TG.groupby("cond")[["on", "off"]].mean().to_dict()
out["targeting_n"] = TG.groupby("cond").size().to_dict()

# how weak were the dims each method chose? panel draft-score rank of round-1 targets (0 = weakest)
def ranks(r):
    s = r.draft_dims; order = sorted(DIMS, key=lambda k: s[k]); return [order.index(k) for k in r.tg1]
for c in ("datr_composite_guard", "datr_random_composite"):
    rr = [ranks(r) for _, r in X[X.cond == c].iterrows() if r.tg1]
    out[f"r1_target_panel_rank_{c}"] = float(np.mean([np.mean(x) for x in rr]))
    out[f"r1_target_draft_score_gap_{c}"] = float(np.mean([np.mean([r.draft_dims[k] for k in r.tg1]) - np.mean(list(r.draft_dims.values()))
                                                            for _, r in X[X.cond == c].iterrows() if r.tg1]))
# natural experiment in the random arm: overlap of random round-1 targets with the panel's two weakest dims vs gain
ov = []
for _, r in X[X.cond == "datr_random_composite"].iterrows():
    s = r.draft_dims; w2 = set(sorted(DIMS, key=lambda k: s[k])[:2]); ov.append((len(w2 & set(r.tg1)), r.delta))
OV = pd.DataFrame(ov, columns=["overlap", "delta"])
out["random_overlap"] = OV.groupby("overlap").delta.agg(["mean", "count"]).to_dict()
out["random_overlap_spearman"] = list(map(float, stats.spearmanr(OV.overlap, OV.delta)))
# same for DATR (inner-judge steering accuracy) vs gain
ov = []
for _, r in X[X.cond == "datr_composite_guard"].iterrows():
    s = r.draft_dims; w2 = set(sorted(DIMS, key=lambda k: s[k])[:2]); ov.append((len(w2 & set(r.tg1)), r.delta))
OV = pd.DataFrame(ov, columns=["overlap", "delta"])
out["datr_overlap"] = OV.groupby("overlap").delta.agg(["mean", "count"]).to_dict()
out["datr_overlap_spearman"] = list(map(float, stats.spearmanr(OV.overlap, OV.delta)))
# per-dimension mean change per condition
out["per_dim"] = {c: {k: float(np.mean([r.dims[k] for _, r in X[X.cond == c].iterrows()])) for k in DIMS} for c in C}
json.dump(out, open(OUT / "b_summary.json", "w"), indent=1, default=str)
pd.set_option("display.width", 200)
print(eff.round(3)); print(PP.round(4)); print(json.dumps(out, indent=1, default=str)[:6000])

# E3-style pooled targeting (same definition as analyze_v6 E3: pool all dimension deltas over runs)
e3 = {}
for c in ("datr_no_guard", "datr_full", "datr_composite_guard", "datr_random_composite"):
    tg, nt = [], []
    for _, r in X[X.cond == c].iterrows():
        for k in DIMS: (tg if k in r.acc_t else nt).append(r.dims[k])
    e3[c] = (float(np.mean(tg)) if tg else float("nan"), float(np.mean(nt)))
json.dump(e3, open(OUT / "b_e3.json", "w"), indent=1); print("E3", e3)

# per-cell table (mean +- SE over five drafts) for all methods incl. drafts
cells = []
for (t, m), g in X.groupby(["topic", "model"]):
    row = {"topic": t, "model": m}
    dr = g.drop_duplicates(["seed"])[["seed", "draft"]]
    row["no_refine"] = (dr.draft.mean(), dr.draft.std(ddof=1) / np.sqrt(len(dr)))
    for c in C:
        v = g[g.cond == c].panel; row[c] = (v.mean(), v.std(ddof=1) / np.sqrt(len(v)))
    cells.append(row)
json.dump(cells, open(OUT / "b_cells.json", "w"), indent=1)
