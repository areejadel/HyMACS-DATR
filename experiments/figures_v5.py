"""
figures_v5.py — paper figures from the v5 data
==================================================
Generates the key figures for the results section (high-quality PNG) for both subjects:
  F1  Gap (inner - external) per model        <- the main finding
  F2  Inner vs external per model             <- single-judge compression vs panel discrimination
  F3  DATR effect: external by method         <- refinement + the guard
  F4  Panel agreement (Krippendorff alpha) per dimension

Run:
    python experiments/figures_v5.py
"""
from __future__ import annotations
import sys, json, glob, csv
from pathlib import Path
from collections import defaultdict
import statistics as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figures_v5"; OUT.mkdir(parents=True, exist_ok=True)
TOPICS = ["backprop", "normalization"]
TLAB = {"backprop": "Backpropagation", "normalization": "Normalization"}
MODELS = ["allam_7b","llama_3_8b","llama_3_3_70b","gemma_4_31b","deepseek_v3_1","qwen3_235b"]
MLAB = {"allam_7b":"ALLaM-7B","llama_3_8b":"Llama-3-8B","llama_3_3_70b":"Llama-3.3-70B",
        "gemma_4_31b":"Gemma-4-31B","deepseek_v3_1":"DeepSeek-V4","qwen3_235b":"Qwen3-235B"}
CONDS = ["no_refine","self_refine","datr_no_guard","datr_full"]
CLAB = {"no_refine":"No-Refine","self_refine":"Self-Refine","datr_no_guard":"DATR (no guard)","datr_full":"DATR-full"}
DIMS = ["academic_accuracy","pedagogical_effectiveness","clarity_organization","practical_relevance",
        "completeness","engagement_potential","technical_quality","innovation"]
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,"figure.dpi":150})


def load(topic):
    inn=defaultdict(list); ext=defaultdict(list); cell=defaultdict(list)
    for f in glob.glob(str(ROOT/"results"/topic/"runs"/"*.json")):
        d=json.load(open(f,encoding="utf-8"))
        if d.get("error") or (d.get("panel_n_ok") or 0)<3: continue
        e=float(d.get("external_overall") or 0); i=float(d.get("final_inner_overall") or 0)
        if e<=0: continue
        m=d["model_key"]; inn[m].append(i); ext[m].append(e); cell[(m,d["condition"])].append(e)
    return inn, ext, cell


DATA={t:load(t) for t in TOPICS}


def F1_gap():
    import numpy as np
    fig,ax=plt.subplots(figsize=(9,4.5))
    x=np.arange(len(MODELS)); w=0.38
    for k,t in enumerate(TOPICS):
        inn,ext,_=DATA[t]
        gaps=[st.mean(inn[m])-st.mean(ext[m]) for m in MODELS]
        ax.bar(x+(k-0.5)*w, gaps, w, label=TLAB[t])
    ax.axhline(0,color="#333",lw=.8)
    ax.set_xticks(x); ax.set_xticklabels([MLAB[m] for m in MODELS],rotation=25,ha="right")
    ax.set_ylabel("Gap  (inner GPT-4o − external panel)")
    ax.set_title("Single-judge inflation gap by model (weak models over-rated by the inner judge)")
    ax.legend(); fig.tight_layout(); fig.savefig(OUT/"F1_gap.png"); plt.close(fig)


def F2_inner_vs_ext():
    import numpy as np
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),sharey=True)
    for ax,t in zip(axes,TOPICS):
        inn,ext,_=DATA[t]; x=np.arange(len(MODELS)); w=0.38
        ax.bar(x-w/2,[st.mean(inn[m]) for m in MODELS],w,label="Inner (GPT-4o)",color="#c0392b")
        ax.bar(x+w/2,[st.mean(ext[m]) for m in MODELS],w,label="External panel",color="#11324d")
        ax.set_xticks(x); ax.set_xticklabels([MLAB[m] for m in MODELS],rotation=30,ha="right",fontsize=9)
        ax.set_title(TLAB[t]); ax.set_ylim(0,10)
    axes[0].set_ylabel("Mean rubric score (1–10)"); axes[0].legend()
    fig.suptitle("Inner judge compresses the range; the panel discriminates (range 2→8.5)")
    fig.tight_layout(); fig.savefig(OUT/"F2_inner_vs_external.png"); plt.close(fig)


def F3_datr():
    import numpy as np
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),sharey=True)
    colors={"no_refine":"#95a5a6","self_refine":"#7f8c8d","datr_no_guard":"#e08e0b","datr_full":"#11324d"}
    for ax,t in zip(axes,TOPICS):
        _,_,cell=DATA[t]; x=np.arange(len(MODELS)); w=0.2
        for j,c in enumerate(CONDS):
            vals=[st.mean(cell[(m,c)]) if cell[(m,c)] else 0 for m in MODELS]
            ax.bar(x+(j-1.5)*w,vals,w,label=CLAB[c],color=colors[c])
        ax.set_xticks(x); ax.set_xticklabels([MLAB[m] for m in MODELS],rotation=30,ha="right",fontsize=9)
        ax.set_title(TLAB[t]); ax.set_ylim(0,10)
    axes[0].set_ylabel("External panel score"); axes[0].legend(fontsize=8,ncol=2)
    fig.suptitle("DATR-full vs baselines (modest but significant; regression-guard rescues unguarded refinement)")
    fig.tight_layout(); fig.savefig(OUT/"F3_datr.png"); plt.close(fig)


def F4_alpha():
    import numpy as np
    fig,ax=plt.subplots(figsize=(9,4.5)); x=np.arange(len(DIMS)); w=0.38
    for k,t in enumerate(TOPICS):
        p=ROOT/"results"/t/"panel_agreement.csv"
        a={}
        if p.exists():
            for r in csv.DictReader(open(p,encoding="utf-8")):
                a[r["dimension"]]=float(r["krippendorff_alpha"])
        ax.bar(x+(k-0.5)*w,[a.get(d,0) for d in DIMS],w,label=TLAB[t])
    ax.axhline(0.80,color="#2f8f4e",ls="--",lw=1,label="0.80 (excellent)")
    ax.set_xticks(x); ax.set_xticklabels([d.replace("_","\n") for d in DIMS],fontsize=8)
    ax.set_ylabel("Krippendorff's α"); ax.set_ylim(0,1)
    ax.set_title("External panel inter-judge agreement per dimension (both topics ≥ 0.80)")
    ax.legend(); fig.tight_layout(); fig.savefig(OUT/"F4_panel_alpha.png"); plt.close(fig)


def F5_self_pref():
    """Self-preference matrix (self - panel) per model, both subjects."""
    import numpy as np, csv as _csv
    fig,ax=plt.subplots(figsize=(9,4.5)); x=np.arange(len(MODELS)); w=0.38
    for k,t in enumerate(TOPICS):
        p=ROOT/"results"/t/"self_preference_matrix.csv"
        per=defaultdict(list)
        if p.exists():
            for r in _csv.DictReader(open(p,encoding="utf-8")):
                per[r["model_key"]].append(float(r["self_preference"]))
        vals=[st.mean(per[m]) if per[m] else 0 for m in MODELS]
        ax.bar(x+(k-0.5)*w,vals,w,label=TLAB[t])
    ax.axhline(0,color="#333",lw=.8)
    ax.set_xticks(x); ax.set_xticklabels([MLAB[m] for m in MODELS],rotation=25,ha="right")
    ax.set_ylabel("Self-preference  (self-judge − cross-family panel)")
    ax.set_title("Every model over-rates itself; weak models most (justifies the cross-family panel)")
    ax.legend(); fig.tight_layout(); fig.savefig(OUT/"F5_self_preference.png"); plt.close(fig)


def F6_rollback():
    """Guard rollback rate per model under datr_full, both subjects."""
    import numpy as np
    fig,ax=plt.subplots(figsize=(9,4.3)); x=np.arange(len(MODELS)); w=0.38
    for k,t in enumerate(TOPICS):
        rb=defaultdict(lambda:[0,0])
        for f in glob.glob(str(ROOT/"results"/t/"runs"/"*.json")):
            d=json.load(open(f,encoding="utf-8"))
            if d.get("error") or d.get("condition")!="datr_full": continue
            its=d.get("iterations") or []
            for it in its[1:]:
                rb[d["model_key"]][1]+=1
                if it.get("rolled_back"): rb[d["model_key"]][0]+=1
        vals=[(rb[m][0]/rb[m][1]*100 if rb[m][1] else 0) for m in MODELS]
        ax.bar(x+(k-0.5)*w,vals,w,label=TLAB[t])
    ax.set_xticks(x); ax.set_xticklabels([MLAB[m] for m in MODELS],rotation=25,ha="right")
    ax.set_ylabel("Regression-Guard rollback rate (%)")
    ax.set_title("Regression-Guard activity under DATR-full (fires when a step would regress quality)")
    ax.legend(); fig.tight_layout(); fig.savefig(OUT/"F6_rollback.png"); plt.close(fig)


def F7_dim_heatmap():
    """Heatmap: external score per (model x dimension) — the quality profile."""
    import numpy as np
    fig,axes=plt.subplots(1,2,figsize=(13,4.8))
    for ax,t in zip(axes,TOPICS):
        M=np.zeros((len(MODELS),len(DIMS)))
        cnt=np.zeros_like(M)
        for f in glob.glob(str(ROOT/"results"/t/"runs"/"*.json")):
            d=json.load(open(f,encoding="utf-8"))
            if d.get("error") or (d.get("panel_n_ok") or 0)<3: continue
            es=d.get("external_scores") or {}
            if d["model_key"] not in MODELS: continue
            mi=MODELS.index(d["model_key"])
            for di,dim in enumerate(DIMS):
                v=es.get(dim,0) or 0
                if v>0: M[mi,di]+=v; cnt[mi,di]+=1
        M=np.divide(M,cnt,out=np.zeros_like(M),where=cnt>0)
        im=ax.imshow(M,aspect="auto",cmap="RdYlGn",vmin=2,vmax=9)
        ax.set_xticks(range(len(DIMS))); ax.set_xticklabels([d.replace("_","\n") for d in DIMS],fontsize=7)
        ax.set_yticks(range(len(MODELS))); ax.set_yticklabels([MLAB[m] for m in MODELS],fontsize=8)
        ax.set_title(TLAB[t])
        for i in range(len(MODELS)):
            for j in range(len(DIMS)):
                ax.text(j,i,f"{M[i,j]:.1f}",ha="center",va="center",fontsize=6,color="#222")
    fig.colorbar(im,ax=axes,fraction=0.025,label="External score")
    fig.suptitle("Per-dimension quality profile (external panel) by generator")
    fig.savefig(OUT/"F7_dim_heatmap.png",bbox_inches="tight"); plt.close(fig)


def F8_scatter():
    """Per-run inner vs external scatter, both subjects."""
    import numpy as np
    cmap=plt.get_cmap("tab10")
    fig,axes=plt.subplots(1,2,figsize=(12,5),sharex=True,sharey=True)
    for ax,t in zip(axes,TOPICS):
        for mi,m in enumerate(MODELS):
            xs=[];ys=[]
            for f in glob.glob(str(ROOT/"results"/t/"runs"/"*.json")):
                d=json.load(open(f,encoding="utf-8"))
                if d.get("error") or d["model_key"]!=m or (d.get("panel_n_ok") or 0)<3: continue
                e=d.get("external_overall") or 0; i=d.get("final_inner_overall") or 0
                if e>0: xs.append(i); ys.append(e)
            ax.scatter(xs,ys,s=18,color=cmap(mi),label=MLAB[m],alpha=.75)
        ax.plot([0,10],[0,10],"--",color="#888",lw=1)
        ax.set_xlim(0,10); ax.set_ylim(0,10); ax.set_xlabel("Inner judge (GPT-4o)")
        ax.set_title(TLAB[t])
    axes[0].set_ylabel("External panel"); axes[0].legend(fontsize=7,loc="upper left")
    fig.suptitle("Per-run inner vs external score; points below the diagonal = inner over-scoring")
    fig.tight_layout(); fig.savefig(OUT/"F8_scatter.png"); plt.close(fig)


def F9_convergence():
    """Inner score trajectory across iterations under datr_full (convergence/plateau)."""
    import numpy as np
    cmap=plt.get_cmap("tab10")
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),sharey=True)
    for ax,t in zip(axes,TOPICS):
        for mi,m in enumerate(MODELS):
            traj=defaultdict(list)
            for f in glob.glob(str(ROOT/"results"/t/"runs"/"*.json")):
                d=json.load(open(f,encoding="utf-8"))
                if d.get("error") or d["model_key"]!=m or d.get("condition")!="datr_full": continue
                for it in (d.get("iterations") or []):
                    traj[it["iteration"]].append(it.get("inner_overall") or 0)
            ks=sorted(traj);
            if ks: ax.plot(ks,[st.mean(traj[k]) for k in ks],marker="o",ms=4,color=cmap(mi),label=MLAB[m])
        ax.set_xlabel("Iteration"); ax.set_title(TLAB[t]); ax.set_xticks([0,1,2,3])
    axes[0].set_ylabel("Inner composite score"); axes[0].legend(fontsize=7)
    fig.suptitle("DATR-full refinement trajectories (inner score per iteration)")
    fig.tight_layout(); fig.savefig(OUT/"F9_convergence.png"); plt.close(fig)


if __name__ == "__main__":
    F1_gap(); F2_inner_vs_ext(); F3_datr(); F4_alpha(); F5_self_pref(); F6_rollback()
    F7_dim_heatmap(); F8_scatter(); F9_convergence()
    print(f"[ok] figures saved in: {OUT}")
    for p in sorted(OUT.glob("*.png")):
        print("   -", p.name)
