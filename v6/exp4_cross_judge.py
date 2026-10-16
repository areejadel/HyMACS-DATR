"""
exp4_cross_judge.py — (البند ٤) مصفوفة الحكم المتقاطع: تفضيل ذاتي حقيقي أم مجرّد تساهل؟
=========================================================================================
المشكلة في v5: كل مولّد قيّم محاضراته فقط (~8.5 للجميع)، فـ «الذات − اللوحة» ≈ 8.5 − اللوحة
وهذا تساهلُ حَكَم وليس انحيازاً للذات.

التصميم هنا:
  - 36 محاضرة No-Refine: 3 لكل مولّد في كل موضوع (البذور الثلاث الوسطى حسب درجة v5).
  - كل محاضرة يقيّمها: المولّدات الستّة كحكّام (gen:*) + اللوحة (claude, kimi, glm).
  - نفس البرومبت للجميع (panel_compact: درجات فقط) ونفس النص المقصوص لكل الحكّام
    (--trunc، افتراضياً 9000 حرف) لأن نافذة ALLaM (4096 رمز) لا تتّسع للمحاضرات الطويلة.
  - التحليل (analyze_v6.py): الدرجة = تساهل الحَكَم + جودة المحاضرة + انحياز الذات
    ⇒ «انحياز الذات» هو التفضيل الذاتي بعد إزالة التساهل.

تشغيل:
    python exp4_cross_judge.py                        # المتاح من المولّدات + اللوحة (× 36)
    # Gemma كحَكَم مجاناً (حساب OpenRouter مجاني بلا شحن، 36 طلباً ضمن حد ~50/يوم):
    V6_ROUTE_gemma_4_31b=openrouter:google/gemma-4-31b-it:free python exp4_cross_judge.py --only-judges gen:gemma_4_31b --workers 1
    python exp4_cross_judge.py --skip-local           # السحابة فقط (ALLaM وLlama-3-8B لاحقاً)
    python exp4_cross_judge.py --only-judges gen:allam_7b gen:llama_3_8b   # المحليان وحدهما
"""
from __future__ import annotations

import argparse

import common

GEN_JUDGES = [f"gen:{m}" for m in common.MODELS]


def select_lectures():
    items = []
    for t in common.TOPICS:
        runs = common.load_v5_runs(t, condition="no_refine")
        for m in common.MODELS:
            rs = sorted([d for d in runs if d["model_key"] == m], key=lambda d: d.get("external_overall", 0))
            if len(rs) >= 5:
                rs = rs[1:4]            # البذور الثلاث الوسطى (تجنّب الأطراف)
            for d in rs[:3]:
                items.append({"topic": t, "run": d["_run"], "lecture": d["final_lecture"],
                              "model_key": m, "condition": "no_refine", "seed": d["seed"]})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trunc", type=int, default=9000)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--skip-allam", action="store_true")
    ap.add_argument("--skip-local", action="store_true")
    ap.add_argument("--only-judges", nargs="+", default=None)
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    common.setup("backprop", mock=a.mock or None)
    from judge_jobs import run_judge_jobs

    items = select_lectures()
    from routes import available
    gen_ok = [j for j in GEN_JUDGES if available(j[4:])]       # المولّد نفسه فقط (لا بدائل بإصدار آخر)
    print(f"المولّدات كحكّام (نفس نموذج v5): {gen_ok}   |   غير متاح: {sorted(set(GEN_JUDGES) - set(gen_ok))}")
    judges = a.only_judges or (gen_ok + ["claude", "kimi", "glm"])
    local_j = ["gen:allam_7b", "gen:llama_3_8b"]
    if a.skip_allam:
        judges = [j for j in judges if j != "gen:allam_7b"]
    if a.skip_local:
        judges = [j for j in judges if j not in local_j]
    print(f"محاضرات: {len(items)}  ×  حكّام: {len(judges)}  ⇒ {len(items) * len(judges)} استدعاء")
    # ALLaM المحلي متسلسل أصلاً؛ نشغّله في دفعة منفصلة حتى لا يحجز الخيوط
    cloud = [j for j in judges if j not in local_j]
    if cloud:
        run_judge_jobs(items, cloud, prompt="panel_compact", rep=1, trunc=a.trunc, workers=a.workers,
                       label="cross-judge (cloud)", experiment="exp4", limit=a.limit)
    # النموذجان المحليان واحداً بعد الآخر (تحرير الذاكرة بينهما)
    for j in [j for j in local_j if j in judges]:
        run_judge_jobs(items, [j], prompt="panel_compact", rep=1, trunc=a.trunc, workers=1,
                       label=f"cross-judge ({j} local)", experiment="exp4", limit=a.limit)
        _release_local(j)


def _release_local(role):
    import gc
    try:
        if role == "gen:allam_7b":
            import clients.allam_local as al
            al._model = None
        else:
            import llama_local_client as ll
            ll.release()
        import judges
        judges._clients.pop(role, None)
    except Exception:
        pass
    gc.collect()


if __name__ == "__main__":
    main()
