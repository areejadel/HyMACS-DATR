"""
exp3_gpt4o_panel_prompt.py — (البند ٣) GPT-4o ببرومبت اللوحة نفسه
==================================================================
يفصل أثر «النموذج» عن أثر «البرومبت» في ادعاء أن الحَكَم الداخلي يضخّم ويضغط المقياس:
  - gpt4o + prompt=panel          ← جديد (هذا السكربت)
  - gpt4o + prompt=inner          ← موجود في v5 (final_inner_scores)
  - [اختياري] gpt4o + prompt=inner_neutral  (--also-neutral)
ويتيح لاحقاً لوحة من 4 حكّام وتحليل leave-one-out لحجم اللوحة (بدون تكلفة إضافية).

تشغيل:
    python exp3_gpt4o_panel_prompt.py
    python exp3_gpt4o_panel_prompt.py --limit 5
الاستدعاءات: 240 (+240 مع --also-neutral)
"""
from __future__ import annotations

import argparse

import common


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--also-neutral", action="store_true",
                    help="أيضاً GPT-4o ببرومبت الحَكَم الداخلي المحايد")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    common.setup("backprop", mock=a.mock or None)
    from judge_jobs import items_from_v5, run_judge_jobs

    items = items_from_v5(common.TOPICS)
    run_judge_jobs(items, ["gpt4o"], prompt="panel", rep=1, workers=a.workers,
                   label="GPT-4o @panel-prompt", experiment="exp3", limit=a.limit)
    if a.also_neutral:
        run_judge_jobs(items, ["gpt4o"], prompt="inner_neutral", rep=1, workers=a.workers,
                       label="GPT-4o @inner-neutral", experiment="exp3", limit=a.limit)


if __name__ == "__main__":
    main()
