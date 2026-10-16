"""
exp1_shared_draft.py — (البند ١) التحسين من نفس المسودة  ← أهمّ تجربة
=======================================================================
المشكلة في v5: كل شرط ولّد مسودته الأولى بنفسه، والبذرة لا تُمرَّر للـ API،
فالفرق بين الشروط يضيع في تباين المسودات و«الإقران حسب البذرة» اعتباطي.

التصميم هنا (مقترن فعلاً):
  - المسودة = محاضرة No-Refine المحفوظة في v5 لكل (نموذج × بذرة)  ← 30 مسودة لكل موضوع.
  - كل الشروط تبدأ من نفس المسودة بالضبط:
        self_refine            كل الوكلاء الأربعة، بلا حارس           (كما في v5)
        self_refine_guard      كل الوكلاء + نفس الحارس                (جديد: المقارنة العادلة الناقصة)
        datr_no_guard          توجيه لأضعف بُعدين، بلا حارس           (كما في v5)
        datr_full              توجيه + حارس لكل بُعد (الكود الفعلي في v5)
        datr_composite_guard   توجيه + حارس على الدرجة المركّبة (ما تصفه الورقة حالياً)
  - No-Refine = المسودة نفسها (تُقيَّم مرّة واحدة باللوحة).
  - الحَكَم الداخلي (GPT-4o) ببرومبت محايد للموضوع (v5 كان يقول ML حتى في قواعد البيانات).
  - اللوحة بدرجة حرارة 0.2 لكل الحكّام، والمركّبة = متوسط الأبعاد الثمانية.
  - إصلاح قصّ المدخلات: في v5 كان الوكيل يرى أول 8000 حرف فقط من المسودة عند المراجعة
    (فتُفقد بقية محاضرات DeepSeek/Qwen الطويلة). هنا 30000 للنماذج كبيرة السياق
    (--prior-chars 8000 لإعادة سلوك v5). ALLaM وLlama-8B يبقيان على ميزانيتهما الأصلية.

تشغيل (موضوع واحد لكل عملية):
    python exp1_shared_draft.py --topic backprop --limit-jobs 2            # تجربة صغيرة
    python exp1_shared_draft.py --topic backprop
    python exp1_shared_draft.py --topic normalization
    python exp1_shared_draft.py --topic backprop --skip-local                    # النماذج السحابية
    python exp1_shared_draft.py --topic backprop --models allam_7b --workers 1   # ALLaM محلياً
    python exp1_shared_draft.py --topic backprop --models llama_3_8b --workers 1 # Llama-3-8B محلياً
    python exp1_shared_draft.py --topic backprop --skip-local --include-substitutes   # + DeepSeek-0813
النماذج المتاحة (أكتوبر 2026): ALLaM وLlama-3-8B محلياً، Llama-3.3-70B على Together.
Gemma-4-31B وQwen3-235B لم يعودا متاحين ⇒ يُتخطّيان تلقائياً.
الحجم: 30 مسودة × 5 شروط = 150 تشغيلة لكل موضوع (300 للموضوعين).
"""
from __future__ import annotations

import argparse
import copy
import time
from pathlib import Path

import common

CONDITIONS = ["self_refine", "self_refine_guard", "datr_no_guard", "datr_full", "datr_composite_guard"]
PANEL_PROMPT = "panel"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, choices=common.TOPICS)
    ap.add_argument("--models", nargs="+", default=common.MODELS)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    ap.add_argument("--conditions", nargs="+", default=CONDITIONS)
    ap.add_argument("--iters", type=int, default=3, help="K (كما في v5)")
    ap.add_argument("--composite-tol", type=float, default=0.0,
                    help="τ لحارس الدرجة المركّبة: يُقبل التعديل إن لم تنخفض المركّبة بأكثر من τ")
    ap.add_argument("--prior-chars", type=int, default=30000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit-jobs", type=int, default=None)
    ap.add_argument("--skip-allam", action="store_true")
    ap.add_argument("--skip-local", action="store_true", help="تخطّي النموذجين المحليين (ALLaM وLlama-3-8B)")
    ap.add_argument("--include-substitutes", action="store_true",
                    help="تضمين DeepSeek عبر الإصدار المؤرّخ V4-Pro-0813 (يختلف عن إصدار مسودات v5؛ يكلّف ~$12)")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()

    config = common.setup(a.topic, mock=a.mock or None)
    from judges import neutralize_inner_judge, panel_eval
    ij = neutralize_inner_judge()
    from pipeline.generator import LectureGenerator
    from pipeline.datr_router import DATRRouter
    import agents.base as ab

    # ── إصلاح قصّ المسودة للنماذج كبيرة السياق ──
    _orig_budget = ab.Agent._budget

    def _budget(self):
        b = dict(_orig_budget(self))
        if not b["small"]:
            b["prior_chars"] = a.prior_chars
        return b
    ab.Agent._budget = _budget

    from routes import LOCAL_MODELS, available, is_substitute
    models = [m for m in a.models if not (a.skip_allam and m == "allam_7b")
              and not (a.skip_local and m in LOCAL_MODELS)]
    skipped = [m for m in models if not available(m, a.include_substitutes)]
    if skipped:
        print(f"تخطّي (غير متاح أو بديل بإصدار مختلف؛ انظري routes.py): {skipped}")
    models = [m for m in models if m not in skipped]
    if not models:
        print("لا نماذج متاحة لهذا التشغيل.")
        return
    out = common.OUT_DIR / "exp1" / a.topic
    lec_dir = out / "lectures"
    lec_dir.mkdir(parents=True, exist_ok=True)
    # عملية ALLaM المحلية تكتب في ملفات منفصلة حتى يمكن تشغيلها بالتوازي مع السحابة
    suffix = {"allam_7b": "_allam", "llama_3_8b": "_llama8"}.get(models[0], "") if len(models) == 1 else ""
    if suffix == "" and set(models) & LOCAL_MODELS and len(models) > 1:
        print("ملاحظة: الأسرع تشغيل النموذجين المحليين في نافذة مستقلة (--models allam_7b --workers 1 ثم llama_3_8b)،"
              " وهنا أضيفي --skip-local")
    drafts = common.JsonlStore(out / f"drafts{suffix}.jsonl")
    runs = common.JsonlStore(out / f"runs{suffix}.jsonl")
    # تشغيلات سحابية سُجّلت قبل أن يراقب الحارس عميل Together (لا ضمان أن كل استدعاءاتها نجحت) ⇒ تُعاد
    stale = [k for k, r in runs.records.items()
             if r.get("model_key") not in LOCAL_MODELS and not (r.get("settings") or {}).get("guard_v2")]
    for k in stale:
        del runs.records[k]
    if stale:
        print(f"إعادة {len(stale)} تشغيلة سحابية سُجّلت قبل إصلاح الحارس")
    for store, name in ((drafts, "مسودة"), (runs, "تشغيلة")):
        partial = [k for k, r in store.records.items() if (r.get("panel") or {}).get("n_ok", 3) < 3]
        for k in partial:
            del store.records[k]
        if partial:
            print(f"إعادة {len(partial)} {name} بلوحة ناقصة (حَكَم فشل بسبب الازدحام)")
    settings = {"iters": a.iters, "composite_tol": a.composite_tol, "prior_chars": a.prior_chars,
                "quality_threshold": config.QUALITY_THRESHOLD,
                "regression_tolerance": config.REGRESSION_TOLERANCE, "top_k": 2,
                "temperature_gen": config.TEMPERATURE_GEN, "judge_temperature": common.JUDGE_TEMPERATURE,
                "inner_prompt": "inner_neutral",
                "substitutes": [m for m in models if is_substitute(m)], "guard_v2": True}
    if not common.MOCK:
        import routes
        settings["routes"] = routes.describe()
    print(f"الإعدادات: {settings}")

    inner = ij.InnerJudge()

    def inner_eval(lecture: str) -> dict:
        for attempt in range(3):
            e = inner.evaluate(lecture)
            c = common.composite(e.get("scores"))
            if not e.get("error") and c == c:
                e["overall_reported"] = e.get("overall")
                e["overall"] = c                # القرارات على المركّبة المنتظمة
                e["composite"] = c
                e.pop("raw", None)
                return e
            time.sleep(3 * (attempt + 1))
        e["composite"] = float("nan")
        e.setdefault("error", "inner judge failed")
        return e

    # ── 1) المسودات: تقييم داخلي محايد + لوحة (مرّة واحدة لكل مسودة) ──
    v5 = {(d["model_key"], d["seed"]): d for d in common.load_v5_runs(a.topic, condition="no_refine")}
    draft_jobs = []
    for m in models:
        for s in a.seeds:
            if (m, s) not in v5:
                print(f"  ⚠️  لا توجد مسودة v5 لـ {m} seed{s}")
                continue
            k = f"{a.topic}|{m}|seed{s}"
            if not drafts.has(k):
                draft_jobs.append((k, m, s))

    def _do_draft(job):
        k, m, s = job
        d = v5[(m, s)]
        lecture = d["iterations"][0]["lecture"]
        ev = inner_eval(lecture)
        pe = panel_eval(lecture, prompt=PANEL_PROMPT)
        from guard import GUARD
        GUARD.check()
        (lec_dir / f"{m}__draft__seed{s}.md").write_text(lecture, encoding="utf-8")
        drafts.add({"key": k, "topic": a.topic, "model_key": m, "seed": s, "v5_run": d["_run"],
                    "lecture_chars": len(lecture), "inner": ev, "panel": pe,
                    "error": ev.get("error") or pe.get("error")})

    common.run_parallel(draft_jobs, _do_draft, workers=a.workers, label="drafts")

    # ── 2) الشروط من نفس المسودة ──
    jobs = []
    for m in models:
        for s in a.seeds:
            dk = f"{a.topic}|{m}|seed{s}"
            if not drafts.has(dk):
                continue
            for c in a.conditions:
                k = f"{a.topic}|{m}|seed{s}|{c}"
                if not runs.has(k):
                    jobs.append((k, m, s, c))
    if a.limit_jobs:
        jobs = jobs[: a.limit_jobs]

    def _do_run(job):
        k, m, s, cond = job
        dr = drafts.get(f"{a.topic}|{m}|seed{s}")
        draft = v5[(m, s)]["iterations"][0]["lecture"]
        from guard import GUARD
        GUARD.reset_task()
        gen = LectureGenerator(m, retriever=None)       # المراجعة لا تستخدم RAG في v5
        router = DATRRouter()
        lecture, ev = draft, copy.deepcopy(dr["inner"])
        iters = [{"iteration": 0, "scores": ev["scores"], "composite": ev["composite"],
                  "chars": len(lecture)}]
        t0 = time.time()
        err = None
        for it in range(1, a.iters + 1):
            dec = router.decide(ev)
            if not dec.should_continue:
                break
            fb = inner.feedback_for_agents(ev)
            if cond.startswith("self_refine"):
                new = gen.refine_self(lecture, fb)
                agents_called, targets = ["sme", "pedagogy", "clarity", "engagement"], []
            else:
                new, agents_called = gen.refine_datr(lecture, dec.target_dimensions, fb)
                targets = list(dec.target_dimensions)
            from guard import GUARD
            GUARD.quality(f"gen:{m}", len(new) >= 0.3 * len(lecture),
                          f"مراجعة قصيرة جداً ({len(new)} مقابل {len(lecture)} حرف)")
            nev = inner_eval(new)
            if nev.get("error"):
                err = f"inner judge failed at iter {it}"
                break
            rolled, regressed = False, []
            if cond in ("datr_full", "self_refine_guard"):
                rolled, regressed = router.check_regression(ev["scores"], nev["scores"], targets)
            elif cond == "datr_composite_guard":
                rolled = nev["composite"] < ev["composite"] - a.composite_tol
            iters.append({"iteration": it, "targets": targets, "agents": agents_called,
                          "proposed_scores": nev["scores"], "proposed_composite": nev["composite"],
                          "proposed_chars": len(new), "rolled_back": bool(rolled),
                          "regressed_dims": list(regressed) if regressed else []})
            if not rolled:
                lecture, ev = new, nev
        GUARD.check()                                   # لا نحفظ تشغيلة ناقصة بعد التوقّف
        if GUARD.task_fails() and not err:
            # استدعاء وكيل فشل داخل التشغيلة (v5 كان يتجاهله ويُبقي النص) — نعلّمها خطأً لتُعاد لاحقاً
            err = f"{GUARD.task_fails()} failed model call(s) inside run — will be retried on next launch"
        final_is_draft = lecture == draft
        pe = dr["panel"] if final_is_draft else panel_eval(lecture, prompt=PANEL_PROMPT)
        GUARD.check()
        (lec_dir / f"{m}__{cond}__seed{s}.md").write_text(lecture, encoding="utf-8")
        runs.add({"key": k, "topic": a.topic, "model_key": m, "seed": s, "condition": cond,
                  "settings": settings, "iterations": iters, "final_inner": ev,
                  "final_inner_composite": ev["composite"], "final_chars": len(lecture),
                  "final_is_draft": final_is_draft, "panel": pe, "panel_composite": pe["composite"],
                  "draft_panel_composite": dr["panel"]["composite"],
                  "n_rollbacks": sum(1 for x in iters[1:] if x.get("rolled_back")),
                  "n_rounds": len(iters) - 1, "elapsed_sec": round(time.time() - t0, 1),
                  "error": err or pe.get("error")})

    # ALLaM المحلي متسلسل؛ نعالجه بخيط واحد في النهاية
    cloud = [j for j in jobs if j[1] not in LOCAL_MODELS]
    local = [j for j in jobs if j[1] in LOCAL_MODELS]
    common.run_parallel(cloud, _do_run, workers=a.workers, label=f"{a.topic}: cloud runs")
    common.run_parallel(local, _do_run, workers=1, label=f"{a.topic}: local-model runs")
    print(f"✓ النتائج: {out}")


if __name__ == "__main__":
    main()
