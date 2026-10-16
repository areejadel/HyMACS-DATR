"""
exp5_length_control.py — (البند ٥) هل تكافئ اللوحة الطول؟
==========================================================
تُقصّ محاضرات النماذج القوية (No-Refine، 3 نماذج × 5 بذور × موضوعان = 30) عند حدّ
فقرة إلى طول قريب من محاضرات ALLaM/Llama-8B (افتراضياً 4000 حرف)، ثم تقيّمها اللوحة.
إن بقيت درجاتها أعلى بوضوح من ALLaM/Llama-8B ⇒ الترتيب ليس أثراً للطول.

تشغيل:
    python exp5_length_control.py                # 90 استدعاء
    python exp5_length_control.py --chars 5000
"""
from __future__ import annotations

import argparse

import common


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", type=int, default=4000)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    common.setup("backprop", mock=a.mock or None)
    from judge_jobs import items_from_v5, run_judge_jobs

    items = items_from_v5(common.TOPICS, conditions=["no_refine"], models=sorted(common.STRONG))
    print(f"محاضرات قوية: {len(items)} — القصّ إلى {a.chars} حرف")
    run_judge_jobs(items, ["claude", "kimi", "glm"], prompt="panel", rep=1, trunc=a.chars,
                   workers=a.workers, label=f"length@{a.chars}", experiment="exp5", limit=a.limit)


if __name__ == "__main__":
    main()
