"""
exp6_allam_precision.py — (البند ٦، اختياري) هل ترتيب ALLaM الأخير سببه الضغط 4-bit؟
=====================================================================================
يولّد مسودات No-Refine لـ ALLaM بدقّة كاملة (bf16/fp16) بنفس خطّ v5 (RAG + 4 وكلاء)،
ثم يقيّمها باللوحة (0.2). نقارنها لاحقاً بمسودات v5 (GGUF Q4_K_M).

يتطلّب أحد الخيارين:
  --backend cuda : جهاز NVIDIA (≥16GB VRAM)، مثلاً سيرفر Vast.ai/RunPod
  --backend mlx  : Mac بذاكرة ≥ 32GB، مع ALLAM_MLX_REPO=humain-ai/ALLaM-7B-Instruct-preview
                   (المستودع الافتراضي في .env هو نسخة 4bit — يجب تغييره هنا)

تشغيل:
    python exp6_allam_precision.py --topic backprop --backend cuda
    python exp6_allam_precision.py --topic normalization --backend cuda
"""
from __future__ import annotations

import argparse
import os

import common


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, choices=common.TOPICS)
    ap.add_argument("--backend", required=True, choices=["cuda", "mlx"])
    ap.add_argument("--mlx-repo", default="humain-ai/ALLaM-7B-Instruct-preview")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    os.environ["ALLAM_BACKEND"] = a.backend
    if a.backend == "mlx":
        os.environ["ALLAM_MLX_REPO"] = a.mlx_repo
    common.setup(a.topic, mock=a.mock or None)
    from judges import panel_eval
    from pipeline.generator import LectureGenerator
    from pipeline.rag import get_retriever

    store = common.JsonlStore(common.OUT_DIR / "exp6_allam_precision.jsonl")
    out = common.OUT_DIR / "exp6" / a.topic
    out.mkdir(parents=True, exist_ok=True)
    retr = get_retriever()
    for s in a.seeds:
        k = f"{a.topic}|allam_7b|{a.backend}|seed{s}"
        if store.has(k):
            continue
        gen = LectureGenerator("allam_7b", retriever=retr)
        lec = gen.initial_draft()
        pe = panel_eval(lec)
        (out / f"allam_{a.backend}__seed{s}.md").write_text(lec, encoding="utf-8")
        store.add({"key": k, "topic": a.topic, "backend": a.backend, "seed": s,
                   "lecture_chars": len(lec), "panel": pe, "panel_composite": pe["composite"],
                   "error": pe.get("error")})
        print(f"  seed{s}: panel={pe['composite']:.2f}  chars={len(lec)}")


if __name__ == "__main__":
    main()
