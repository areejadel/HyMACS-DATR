"""
estimate_cost.py — كم ستكلّف كل مرحلة على كل مزوّد؟ (بلا أي استدعاء API)
==========================================================================
يقرأ أطوال محاضرات v5 الفعلية + المسارات الحالية (routes.py / judges.py) + الأسعار (guard.py)
ويطبع تقديراً لكل تجربة. التقدير متحفّظ قليلاً (يفترض 3 جولات تحسين كاملة دائماً).

    python estimate_cost.py
    python estimate_cost.py --include-substitutes      # + DeepSeek-0813 في exp1
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import common

PANEL_IN, PANEL_OUT = 800, 700          # رموز البرومبت الإضافية / ردّ اللوحة (درجات + تبريرات)
COMPACT_OUT = 150                       # ردّ الدرجات فقط
INNER_IN, INNER_OUT = 1200, 1200        # الحَكَم الداخلي (درجات + تبريرات + اقتراحات)
REV_IN = 1500                           # برومبت الوكيل + الملاحظات
CH_PER_TOK = 3.8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-substitutes", action="store_true")
    ap.add_argument("--also-neutral", action="store_true", help="exp3 مع البرومبت المحايد أيضاً")
    a = ap.parse_args()
    common.setup("backprop", mock=True)          # لا استدعاءات؛ نحتاج config فقط
    import guard
    import routes
    from judges import JUDGE_SPECS

    def price(mid):
        return guard.PRICES.get(mid, guard.DEFAULT_PRICE)

    def judge_target(role):
        if role.startswith("gen:"):
            b, mid = routes.route_of(role[4:])
            if b in ("v5", "local_llama"):
                return "local", None
            return b, mid
        b, mid = JUDGE_SPECS[role]
        return b, mid

    cost = defaultdict(lambda: defaultdict(float))     # stage -> provider -> $

    def add(stage, role, n, tin, tout):
        prov, mid = judge_target(role)
        if prov == "local":
            return
        pin, pout = price(mid)
        cost[stage][prov] += n * (tin * pin + tout * pout) / 1e6

    runs = {t: common.load_v5_runs(t, with_text=True) for t in common.TOPICS}
    allruns = [d for t in common.TOPICS for d in runs[t]]
    L = lambda d: len(d.get("final_lecture", "")) / CH_PER_TOK

    # exp2 — Part A: Kimi وGLM على 240 (+ Claude حيث فشل في v5)؛ Part B: 48 × 3
    for d in allruns:
        for r in ("kimi", "glm"):
            add("exp2", r, 1, L(d) + PANEL_IN, PANEL_OUT)
        cl = (d.get("panel_per_judge") or {}).get("judge_claude") or {}
        if not cl or cl.get("error"):
            add("exp2", "claude", 1, L(d) + PANEL_IN, PANEL_OUT)
    avgL = sum(L(d) for d in allruns) / len(allruns)
    for r in ("claude", "kimi", "glm"):
        add("exp2", r, 48, avgL + PANEL_IN, PANEL_OUT)

    # exp3 — GPT-4o ببرومبت اللوحة على 240
    for d in allruns:
        add("exp3", "gpt4o", 2 if a.also_neutral else 1, L(d) + PANEL_IN, PANEL_OUT)

    # exp5 — محاضرات النماذج القوية No-Refine مقصوصة إلى 4000 حرف × اللوحة
    n5 = sum(1 for d in allruns if d["condition"] == "no_refine" and d["model_key"] in common.STRONG)
    for r in ("claude", "kimi", "glm"):
        add("exp5", r, n5, 4000 / CH_PER_TOK + PANEL_IN, PANEL_OUT)

    # exp4 — 36 محاضرة × (المولّدات المتاحة كحكّام + اللوحة)، برومبت مختصر، قصّ 9000 حرف
    gen_j = [f"gen:{m}" for m in common.MODELS if routes.available(m)]
    for r in gen_j + ["claude", "kimi", "glm"]:
        add("exp4", r, 36, min(avgL, 9000 / CH_PER_TOK) + PANEL_IN, COMPACT_OUT)

    # exp1 — لكل مسودة: 2 شرط SR × 3 جولات × 4 وكلاء + 3 شروط DATR × 3 × 2  = 42 مراجعة
    #         + 16 تقييماً داخلياً (GPT-4o) + 6 تقييمات لوحة
    ex1_models = [m for m in common.MODELS if routes.available(m, a.include_substitutes)]
    for t in common.TOPICS:
        for d in runs[t]:
            if d["condition"] != "no_refine" or d["model_key"] not in ex1_models:
                continue
            l = len(d["iterations"][0]["lecture"]) / CH_PER_TOK
            add("exp1", f"gen:{d['model_key']}", 42, l + REV_IN, l)
            add("exp1", "gpt4o", 16, l + INNER_IN, INNER_OUT)
            for r in ("claude", "kimi", "glm"):
                add("exp1", r, 6, l + PANEL_IN, PANEL_OUT)

    provs = ["together", "openai", "anthropic", "openrouter"]
    print("\nالمسارات:", routes.describe())
    print("الحكّام:", {r: f"{b}:{i}" for r, (b, i) in JUDGE_SPECS.items()})
    print(f"exp1 يشمل: {ex1_models}\n")
    print(f"{'stage':<8}" + "".join(f"{p:>12}" for p in provs) + f"{'total':>10}")
    tot = defaultdict(float)
    for st in ("exp2", "exp3", "exp5", "exp4", "exp1"):
        row = cost[st]
        for p in provs:
            tot[p] += row.get(p, 0)
        print(f"{st:<8}" + "".join(f"{row.get(p, 0):>12.2f}" for p in provs) + f"{sum(row.values()):>10.2f}")
    print("-" * 66)
    print(f"{'TOTAL':<8}" + "".join(f"{tot[p]:>12.2f}" for p in provs) + f"{sum(tot.values()):>10.2f}")
    print(f"\nمع هامش أمان 25%:  " + ", ".join(f"{p} ${tot[p] * 1.25:.0f}" for p in provs if tot[p]))
    print("السقوف الحالية في guard.py:", {p: guard.CAPS[p] for p in provs})


if __name__ == "__main__":
    main()
