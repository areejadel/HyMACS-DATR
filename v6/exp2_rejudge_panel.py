"""
exp2_rejudge_panel.py — (البند ٢) إعادة تقييم اللوحة بإعدادات موحّدة + ثبات إعادة القياس
==========================================================================================
الجزء A (إلزامي): Kimi وGLM يقيّمان المحاضرات النهائية الـ240 بدرجة حرارة 0.2
         (في v5 كانا بـ 0.7 بالخطأ). Claude كان أصلاً بـ 0.2 فنعيد استخدام درجته من v5،
         إلا في التشغيلات التي فشل فيها Claude في v5 فنقيّمها من جديد.
         ⇒ «لوحة v6» = Claude(v5) + Kimi(0.2) + GLM(0.2) لكل الـ240.
الجزء B (ثبات القياس): 48 محاضرة (الـ24 البشرية + 24 طبقية) تُقيَّم مرة ثانية
         بالحكّام الثلاثة (rep2) لحساب test–retest.

تشغيل:
    python exp2_rejudge_panel.py --part A
    python exp2_rejudge_panel.py --part B
    python exp2_rejudge_panel.py --part A --limit 5     # تجربة صغيرة أولاً
    python exp2_rejudge_panel.py --part A --mock        # بدون أي تكلفة (اختبار)
الاستدعاءات التقريبية: A ≈ 480 + ~12 ،  B = 144
"""
from __future__ import annotations

import argparse

import common


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["A", "B", "both"], default="both")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None, help="أقصى عدد استدعاءات (للتجربة)")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    common.setup("backprop", mock=a.mock or None)
    from judge_jobs import items_from_v5, run_judge_jobs

    items = items_from_v5(common.TOPICS)
    print(f"محاضرات v5: {len(items)}")

    if a.part in ("A", "both"):
        run_judge_jobs(items, ["kimi", "glm"], prompt="panel", rep=1, workers=a.workers,
                       label="A: Kimi+GLM @T0.2", experiment="exp2A", limit=a.limit)
        # Claude فقط حيث فشل في v5
        failed = []
        runs = {(d["_topic"], d["_run"]): d for t in common.TOPICS for d in common.load_v5_runs(t, with_text=False)}
        for it in items:
            pj = runs[(it["topic"], it["run"])].get("panel_per_judge", {}).get("judge_claude", {})
            if not pj or pj.get("error"):
                failed.append(it)
        print(f"تشغيلات فشل فيها Claude في v5: {len(failed)}")
        run_judge_jobs(failed, ["claude"], prompt="panel", rep=1, workers=a.workers,
                       label="A: Claude (المفقود فقط)", experiment="exp2A", limit=a.limit)

    if a.part in ("B", "both"):
        sample = retest_sample(items)
        print(f"عيّنة إعادة القياس: {len(sample)} محاضرة")
        run_judge_jobs(sample, ["claude", "kimi", "glm"], prompt="panel", rep=2, workers=a.workers,
                       label="B: retest (rep2)", experiment="exp2B", limit=a.limit)


def retest_sample(items, n_extra_per_cell: int = 2):
    """الـ24 محاضرة البشرية + محاضرتان لكل (نموذج×موضوع) من غير البشرية (بذرة ثابتة)."""
    hum = set(common.human_lecture_runs().values())
    chosen = [it for it in items if (it["topic"], it["run"]) in hum]
    r = common.rng(7)
    for t in common.TOPICS:
        for m in common.MODELS:
            pool = [it for it in items if it["topic"] == t and it["model_key"] == m
                    and (t, it["run"]) not in hum]
            pool.sort(key=lambda x: x["run"])
            chosen += r.sample(pool, min(n_extra_per_cell, len(pool)))
    return chosen


if __name__ == "__main__":
    main()
