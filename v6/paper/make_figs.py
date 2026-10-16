"""Figures for the paper (all from v6 results). Usage (from v6/): python paper/make_figs.py [out_dir]"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
S = HERE.parent / "results_v6" / "paper_v6_stats"   # written by paper_stats.py + export_fig_data.py
T = HERE.parent / "results_v6" / "tables"           # written by analyze_v6.py
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "figures")
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b",
    "xtick.color": "#52514e", "ytick.color": "#52514e", "grid.color": "#e4e3df", "grid.linewidth": 0.5,
    "pdf.fonttype": 42, "savefig.dpi": 300,
})
BLUE, ORANGE, AQUA, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#e4e3df"
GRAY = "#9a9994"
MODELS = ["allam_7b", "llama_3_8b", "llama_3_3_70b", "gemma_4_31b", "deepseek_v3_1", "qwen3_235b"]
LBL = {"allam_7b": "ALLaM-7B", "llama_3_8b": "Llama-3-8B", "llama_3_3_70b": "Llama-3.3-70B",
       "gemma_4_31b": "Gemma-4-31B", "deepseek_v3_1": "DeepSeek-V4-Pro", "qwen3_235b": "Qwen3-235B"}
CND = {"self_refine": "Self-Refine", "self_refine_guard": "Self-Refine + guard", "datr_no_guard": "DATR (no guard)",
       "datr_full": "DATR + per-dim. guard", "datr_composite_guard": "DATR + composite guard"}
COL_W, TXT_W = 3.45, 7.16


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)


def panel_label(ax, s):
    ax.text(-0.02, 1.04, s, transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom", ha="right")


L = pd.read_csv(S / "lectures_240.csv")
pairs = pd.read_csv(S / "exp1_pairs.csv")
eff = pd.read_csv(S / "exp1_efficiency.csv").set_index("cond")
sp = pd.read_csv(S / "selfpref_calibrated.csv").set_index("model")
order_gen = L.groupby("model").v6_panel.mean().sort_values().index.tolist()


def forest(ax, show_calls=True):
    conds = ["self_refine", "self_refine_guard", "datr_no_guard", "datr_full", "datr_composite_guard"]
    sub = pairs[pairs.b == "no_refine"].set_index("a").loc[conds]
    y = np.arange(len(conds))[::-1]
    ax.axvline(0, color=MUTED, lw=0.6, zorder=1)
    for yi, c in zip(y, conds):
        r = sub.loc[c]
        col = BLUE if c.startswith("datr") else GRAY
        ax.plot([r.lo, r.hi], [yi, yi], color=col, lw=1.6, solid_capstyle="round", zorder=2)
        ax.plot(r.delta, yi, "o", ms=5, color=col, mec="white", mew=0.8, zorder=3)
        lab = f"{r.delta:+.2f}"
        if show_calls:
            lab += f"   ({eff.loc[c, 'calls']:.1f} calls)"
        ax.text(r.hi + 0.015, yi, lab, va="center", fontsize=6.8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([CND[c] for c in conds])
    ax.set_xlabel("Panel gain over the same draft (95% CI)")
    ax.set_xlim(-0.05, 0.62)
    ax.grid(axis="x")
    ax.set_axisbelow(True)


# ------------------------------------------------------------------ Fig 1 teaser
def fig_teaser():
    fig, axs = plt.subplots(1, 3, figsize=(TXT_W, 2.35), gridspec_kw=dict(width_ratios=[1.15, 1.0, 1.25], wspace=0.55))
    ax = axs[0]
    g = L.groupby("model")[["v6_panel", "inner_reported", "gpt4o_panelprompt"]].mean().loc[order_gen]
    x = np.arange(len(g))
    for col, c, lab, mk in [("v6_panel", BLUE, "Cross-family panel", "o"),
                            ("inner_reported", ORANGE, "GPT-4o, inner prompt", "s"),
                            ("gpt4o_panelprompt", AQUA, "GPT-4o, panel prompt", "^")]:
        ax.plot(x, g[col], marker=mk, color=c, lw=1.2, ms=4.5, mec="white", mew=0.6, label=lab)
    ax.set_xticks(x)
    ax.set_xticklabels([LBL[m].replace("-Pro", "") for m in g.index], rotation=40, ha="right")
    ax.set_ylabel("Mean rubric score (1–10)")
    ax.set_ylim(1.5, 9)
    ax.grid(axis="y")
    ax.legend(frameon=False, loc="lower right", handlelength=1.6)
    ax.set_title("A single judge compresses", loc="left")
    panel_label(ax, "(a)")

    ax = axs[1]
    m = [k for k in MODELS]
    y = np.arange(len(m))[::-1]
    ax.barh(y + 0.19, [sp.loc[k, "naive"] for k in m], height=0.34, color=GRAY, label="Naive (self − panel)")
    ax.barh(y - 0.19, [sp.loc[k, "self_cal"] for k in m], height=0.34, color=BLUE, label="Calibrated")
    ax.errorbar([sp.loc[k, "self_cal"] for k in m], y - 0.19,
                xerr=[[sp.loc[k, "self_cal"] - sp.loc[k, "lo"] for k in m], [sp.loc[k, "hi"] - sp.loc[k, "self_cal"] for k in m]],
                fmt="none", ecolor=INK, elinewidth=0.7, capsize=1.5)
    ax.axvline(0, color=MUTED, lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([LBL[k] for k in m])
    ax.set_xlabel("Self-preference (rubric points)")
    ax.set_xlim(-0.6, 7.2)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=2, fontsize=6.6, handlelength=1.0, borderaxespad=0.2, columnspacing=0.8)
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    panel_label(ax, "(b)")

    ax = axs[2]
    forest(ax)
    ax.set_title("Refinement from a shared draft", loc="left")
    panel_label(ax, "(c)")
    save(fig, "vfig01_teaser")


# ------------------------------------------------------------------ Fig 2 architecture
def fig_arch():
    fig, ax = plt.subplots(figsize=(TXT_W, 2.25))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 32)
    ax.axis("off")

    def box(x, y, w, h, text, fc, tc="white", fs=7.2, bold=True):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=fc, ec="none"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs,
                fontweight="bold" if bold else "normal", linespacing=1.15)

    def arrow(x0, y0, x1, y1, style="-|>", ls="-"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle=style, color="#33322f", lw=0.9, ls=ls, shrinkA=0, shrinkB=0))

    box(0.5, 13, 9.5, 6, "Reference\ntextbook", "#7f7e79")
    box(12, 13, 9.5, 6, "RAG\n(top-6)", "#168a5f")
    arrow(10.2, 16, 11.8, 16)
    agents = ["SME", "Pedagogy", "Clarity", "Engagement"]
    ax.text(30, 30.6, "Specialist agents", ha="center", fontsize=6.6, color=MUTED, style="italic")
    for i, a in enumerate(agents):
        box(24, 24.5 - i * 6.6, 12, 5, a, BLUE, fs=6.8)
        arrow(21.7, 16, 23.8, 27 - i * 6.6)
        arrow(36.2, 27 - i * 6.6, 39.8, 16)
    box(40, 13, 9.5, 6, "Draft\nlecture", "#33322f")
    arrow(49.7, 16, 52.3, 16)
    box(52.5, 13, 11, 6, "Inner judge\nGPT-4o", ORANGE)
    box(67, 21, 13, 6, "DATR router\n2 weakest dims", "#c98500", tc=INK)
    box(67, 5, 13, 6, "Regression-\nGuard", "#c23b3a")
    arrow(63.7, 17.5, 66.8, 23.5)
    arrow(73.5, 20.8, 73.5, 11.2)
    ax.text(74.4, 16, "owning agents\nrevise", fontsize=6.3, color=MUTED, va="center", style="italic")
    ax.plot([66.8, 58, 58], [8, 8, 12.4], color="#33322f", lw=0.9, ls=(0, (3, 2)))
    arrow(58, 12.2, 58, 12.9)
    ax.text(57.2, 6.6, "accept or roll back;\nrepeat up to K rounds", fontsize=6.3, color=MUTED, style="italic",
            va="center", ha="right")
    arrow(80.2, 8, 84.3, 13)
    box(84.5, 11, 15, 10, "Cross-family panel\n(median)\nClaude-Sonnet-4.6\nKimi-K3 · GLM-5.2", "#6250d6", fs=6.4)
    save(fig, "vfig02_architecture")


# ------------------------------------------------------------------ Fig 3 alpha per dimension
def fig_alpha():
    A = pd.read_csv(S / "alpha_dim_v6.csv")
    dims = ["academic_accuracy", "pedagogical_effectiveness", "clarity_organization", "practical_relevance",
            "completeness", "engagement_potential", "technical_quality", "innovation", "composite"]
    nm = ["Academic acc.", "Pedagogical eff.", "Clarity & org.", "Practical rel.", "Completeness",
          "Engagement", "Technical qual.", "Innovation", "Composite"]
    fig, ax = plt.subplots(figsize=(COL_W, 2.6))
    y = np.arange(len(dims))[::-1]
    for off, t, c, lab in [(0.19, "backprop", BLUE, "Backpropagation"), (-0.19, "normalization", ORANGE, "Normalization")]:
        v = A[A.topic == t].set_index("dim").loc[dims, "alpha"].values
        ax.barh(y + off, v, height=0.34, color=c, label=lab)
    ax.axvline(0.8, color=MUTED, lw=0.7, ls=(0, (3, 2)))
    ax.text(0.802, y[0] + 0.75, "0.80", fontsize=6.5, color=MUTED)
    ax.set_yticks(y)
    ax.set_yticklabels(nm)
    ax.set_xlim(0.6, 1.0)
    ax.set_xlabel("Krippendorff's α (interval), 120 lectures per subject")
    ax.legend(frameon=False, loc="lower left", ncol=2, bbox_to_anchor=(0, -0.3))
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    save(fig, "vfig03_panel_alpha")


# ------------------------------------------------------------------ Fig 4 inner vs panel (both subjects)
def fig_inner():
    B = pd.read_csv(T / "B1_inner_vs_panel_by_model.csv")
    fig, axs = plt.subplots(1, 2, figsize=(TXT_W, 2.2), sharey=True, gridspec_kw=dict(wspace=0.12))
    inv = {v: k for k, v in LBL.items()}
    for ax, t, ttl in [(axs[0], "backprop", "Backpropagation"), (axs[1], "normalization", "Normalization")]:
        s = B[B.topic == t].copy()
        s["k"] = s.model.map(inv)
        s = s.set_index("k").loc[order_gen]
        x = np.arange(len(s))
        w = 0.26
        for off, col, c, lab in [(-w, "panel v6", BLUE, "Cross-family panel"),
                                 (0, "GPT-4o inner-prompt (v5)", ORANGE, "GPT-4o, inner prompt"),
                                 (w, "GPT-4o panel-prompt", AQUA, "GPT-4o, panel prompt")]:
            ax.bar(x + off, s[col].astype(float), width=w - 0.03, color=c, label=lab)
        ax.set_xticks(x)
        ax.set_xticklabels([LBL[m] for m in s.index], rotation=25, ha="right")
        ax.set_title(ttl, loc="left")
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.set_ylim(0, 9)
    axs[0].set_ylabel("Mean rubric score (1–10)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.98))
    save(fig, "vfig04_inner_vs_panel")


# ------------------------------------------------------------------ Fig 5 cross-judge matrix + calibration
def fig_cross():
    C = pd.read_csv(S / "cross_matrix.csv").set_index("role")
    rows = ["claude", "kimi", "glm"] + [f"gen:{m}" for m in order_gen]
    rl = ["Claude-Sonnet-4.6", "Kimi-K3", "GLM-5.2"] + [LBL[m] + " (gen.)" for m in order_gen]
    M = C.loc[rows, order_gen].values
    fig, axs = plt.subplots(1, 2, figsize=(TXT_W, 2.75), gridspec_kw=dict(width_ratios=[1.25, 1], wspace=0.55))
    ax = axs[0]
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#f2f7fd", "#9cc3ef", "#2a78d6", "#0f3f7a"])
    im = ax.imshow(M, cmap=cmap, vmin=1.5, vmax=9.5, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            self_ = rows[i] == f"gen:{order_gen[j]}"
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=6.6,
                    color="white" if v > 6.3 else INK, fontweight="bold" if self_ else "normal")
            if self_:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, ec=ORANGE, lw=1.4))
    ax.axhline(2.5, color="white", lw=2)
    ax.set_xticks(range(len(order_gen)))
    ax.set_xticklabels([LBL[m] for m in order_gen], rotation=35, ha="right")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rl)
    ax.set_xlabel("Lecture generator")
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.ax.tick_params(labelsize=6.5, length=0)
    cb.outline.set_visible(False)
    ax.set_title("Mean score given by each judge (row) — self in box", loc="left")
    panel_label(ax, "(a)")

    ax = axs[1]
    X = pd.read_csv(S / "lectures_240.csv")  # not used for scatter; use cross matrix rows for calibration lines
    pan = C.loc[["claude", "kimi", "glm"]].median()
    xs = np.linspace(1.5, 9, 50)
    for m, c in [("allam_7b", ORANGE), ("llama_3_3_70b", AQUA), ("deepseek_v3_1", BLUE)]:
        jy = C.loc[f"gen:{m}"]
        ax.plot(pan[order_gen].values, jy[order_gen].values, "o", color=c, ms=4.5, mec="white", mew=0.6,
                label=f"{LBL[m]} as judge (slope {sp.loc[m, 'slope']:.2f})")
        own = pan[m], jy[m]
        ax.plot(*own, "o", ms=8, mfc="none", mec=c, mew=1.2)
    ax.plot(xs, xs, color=MUTED, lw=0.7, ls=(0, (3, 2)))
    ax.text(7.05, 6.55, "y = x", fontsize=6.5, color=MUTED, ha="left")
    ax.set_xlabel("Panel median (per generator)")
    ax.set_ylabel("Score given by generator-judge")
    ax.set_xlim(1.5, 9)
    ax.set_ylim(1.5, 9.6)
    ax.legend(frameon=False, loc="lower right", fontsize=6.3)
    ax.grid()
    ax.set_axisbelow(True)
    ax.set_title("Weaker judges are flat, not self-favouring", loc="left")
    panel_label(ax, "(b)")
    save(fig, "vfig05_crossjudge")


# ------------------------------------------------------------------ Fig 6 per-dimension heatmap (v6 panel)
def fig_heat():
    dims = ["academic_accuracy", "pedagogical_effectiveness", "clarity_organization", "practical_relevance",
            "completeness", "engagement_potential", "technical_quality", "innovation"]
    nm = ["Acad. acc.", "Pedag. eff.", "Clarity", "Practical", "Complete.", "Engage.", "Technical", "Innov."]
    M = L.groupby("model")[[f"v6dim_{d}" for d in dims]].mean().loc[order_gen[::-1]].values
    fig, ax = plt.subplots(figsize=(COL_W, 2.1))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#f2f7fd", "#9cc3ef", "#2a78d6", "#0f3f7a"])
    im = ax.imshow(M, cmap=cmap, vmin=1.5, vmax=9.5, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.1f}", ha="center", va="center", fontsize=6.4, color="white" if M[i, j] > 6.3 else INK)
    ax.set_xticks(range(len(dims)))
    ax.set_xticklabels(nm, rotation=35, ha="right")
    ax.set_yticks(range(M.shape[0]))
    ax.set_yticklabels([LBL[m] for m in order_gen[::-1]])
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    save(fig, "vfig06_dim_heatmap")


# ------------------------------------------------------------------ Fig 7 refinement detail
def fig_refine():
    tier = pd.read_csv(S / "exp1_tier.csv")
    E3 = pd.read_csv(T / "E3_targeting_mechanism.csv")
    conds = ["self_refine", "self_refine_guard", "datr_no_guard", "datr_full", "datr_composite_guard"]
    fig, axs = plt.subplots(1, 2, figsize=(TXT_W, 2.3), gridspec_kw=dict(width_ratios=[1.3, 1], wspace=0.75))
    ax = axs[0]
    y = np.arange(len(conds))[::-1]
    for off, tr, c, lab in [(0.17, "weak", ORANGE, "Weaker generators (ALLaM, Llama)"), (-0.17, "strong", BLUE, "Stronger generators (Gemma, DeepSeek, Qwen)")]:
        s = tier[tier.tier == tr].set_index("cond").loc[conds]
        ax.plot([s.lo, s.hi], [y + off, y + off], color=c, lw=1.5, solid_capstyle="round")
        ax.plot(s.delta, y + off, "o", color=c, ms=4.5, mec="white", mew=0.6, label=lab)
    ax.axvline(0, color=MUTED, lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([CND[c] for c in conds])
    ax.set_xlabel("Panel gain over the same draft (95% CI)")
    ax.set_xlim(-0.12, 0.62)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.04, 1.0), fontsize=6.6, ncol=1, borderaxespad=0.2)
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    panel_label(ax, "(a)")

    ax = axs[1]
    e = E3.set_index("condition")
    dc = ["datr_no_guard", "datr_full", "datr_composite_guard"]
    x = np.arange(len(dc))
    tv = [float(e.loc[c, "Δ targeted dims (panel)"]) for c in dc]
    nv = [float(e.loc[c, "Δ non-targeted dims (panel)"]) for c in dc]
    ax.bar(x - 0.18, tv, width=0.34, color=BLUE, label="Targeted dimensions")
    ax.bar(x + 0.18, nv, width=0.34, color=GRAY, label="Other dimensions")
    for xi, v in zip(x - 0.18, tv):
        ax.text(xi, v + 0.015, f"{v:+.2f}", ha="center", fontsize=6.5)
    for xi, v in zip(x + 0.18, nv):
        ax.text(xi, max(v, 0) + 0.015, f"{v:+.2f}", ha="center", fontsize=6.5)
    ax.axhline(0, color=MUTED, lw=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(["No guard", "Per-dim.\nguard", "Composite\nguard"])
    ax.set_ylabel("Δ panel score per dimension")
    ax.set_ylim(-0.1, 0.78)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_title("DATR moves the dimensions it targets", loc="left")
    panel_label(ax, "(b)")
    save(fig, "vfig07_refinement")


# ------------------------------------------------------------------ Fig 8 human validation
def fig_human():
    H = pd.read_csv(S / "human_lectures.csv")
    fig, axs = plt.subplots(1, 2, figsize=(TXT_W, 2.3), gridspec_kw=dict(width_ratios=[1.1, 1], wspace=0.35))
    ax = axs[0]
    ax.plot([1, 9.3], [1, 9.3], color=MUTED, lw=0.7, ls=(0, (3, 2)))
    ax.plot(H["mean"], H.v6_panel, "o", color=BLUE, ms=4.5, mec="white", mew=0.6,
            label=f"Panel (ρ = {stats.spearmanr(H['mean'], H.v6_panel)[0]:.2f}, MAE {np.mean(np.abs(H['mean'] - H.v6_panel)):.2f})")
    ax.plot(H["mean"], H.inner_reported, "s", color=ORANGE, ms=4, mec="white", mew=0.6,
            label=f"Inner judge (ρ = {stats.spearmanr(H['mean'], H.inner_reported)[0]:.2f}, MAE {np.mean(np.abs(H['mean'] - H.inner_reported)):.2f})")
    ax.set_xlabel("Mean human score")
    ax.set_ylabel("Automated score")
    ax.set_xlim(1, 9.3)
    ax.set_ylim(1, 9.3)
    ax.legend(frameon=False, loc="lower right")
    ax.grid()
    ax.set_axisbelow(True)
    panel_label(ax, "(a)")
    ax = axs[1]
    C1 = pd.read_csv(T / "C1_human_alignment.csv")
    names = [("panel v6 (median-composite)", "Panel", BLUE), ("GPT-4o inner-prompt (paper's inner)", "Inner judge", ORANGE)]
    topics = ["backprop", "normalization", "pooled"]
    x = np.arange(3)
    for k, (n, lab, c) in enumerate(names):
        v = [float(C1[(C1.evaluator == n) & (C1.topic == t)].MAE.iloc[0]) for t in topics]
        ax.bar(x + (k - 0.5) * 0.36, v, width=0.33, color=c, label=lab)
        for xi, vi in zip(x + (k - 0.5) * 0.36, v):
            ax.text(xi, vi + 0.03, f"{vi:.2f}", ha="center", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels(["Backprop.", "Normaliz.", "Pooled"])
    ax.set_ylabel("MAE to human mean")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    panel_label(ax, "(b)")
    save(fig, "vfig08_human")


for f in [fig_teaser, fig_arch, fig_alpha, fig_inner, fig_cross, fig_heat, fig_refine, fig_human]:
    f()
print("done", sorted(p.name for p in OUT.glob("vfig*.pdf")))
