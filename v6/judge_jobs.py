"""
judge_jobs.py — منفّذ مشترك لتجارب «إعادة التقييم» (exp2, exp3, exp5)
=====================================================================
كل التقييمات تُحفظ في ملف واحد:  results_v6/judgements.jsonl
مفتاح السجلّ:  topic|run|role|prompt|rep|trunc
"""
from __future__ import annotations

from common import OUT_DIR, JsonlStore, run_parallel

STORE_PATH = OUT_DIR / "judgements.jsonl"


def jkey(topic, run, role, prompt, rep, trunc) -> str:
    return f"{topic}|{run}|{role}|{prompt}|rep{rep}|trunc{trunc or 0}"


def run_judge_jobs(items, roles, prompt="panel", rep=1, trunc=None, workers=6,
                   label="judge", experiment="", limit=None):
    """items: قائمة dict فيها topic, run, lecture (+ أي حقول وصفية)."""
    from judges import judge
    store = JsonlStore(STORE_PATH)
    jobs = []
    for it in items:
        for role in roles:
            k = jkey(it["topic"], it["run"], role, prompt, rep, trunc)
            if not store.has(k):
                jobs.append((k, it, role))
    if limit:
        jobs = jobs[:limit]

    def _do(job):
        k, it, role = job
        res = judge(role, it["lecture"], prompt=prompt, max_chars=trunc)
        res.update({"key": k, "experiment": experiment, "topic": it["topic"], "run": it["run"],
                    "model_key": it.get("model_key"), "condition": it.get("condition"),
                    "seed": it.get("seed"), "rep": rep, "trunc": trunc or 0,
                    "lecture_chars": len(it["lecture"])})
        store.add(res)
        if res.get("error"):
            print(f"    ⚠️  {k}: {res['error'][:120]}")

    run_parallel(jobs, _do, workers=workers, label=label)
    n_err = sum(1 for r in store.values() if r.get("experiment") == experiment and r.get("error"))
    print(f"  ✓ {label}: محفوظ في {STORE_PATH.name}  (أخطاء متبقّية: {n_err} — أعيدي التشغيل لإعادة محاولتها)")
    return store


def items_from_v5(topics, conditions=None, models=None):
    from common import load_v5_runs
    items = []
    for t in topics:
        for d in load_v5_runs(t):
            if conditions and d["condition"] not in conditions:
                continue
            if models and d["model_key"] not in models:
                continue
            items.append({"topic": t, "run": d["_run"], "lecture": d["final_lecture"],
                          "model_key": d["model_key"], "condition": d["condition"], "seed": d["seed"],
                          "v5_external": d.get("external_overall")})
    return items
