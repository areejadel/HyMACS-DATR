"""
smoke_v6.py — فحص سريع قبل أي صرف: هل كل نموذج وحَكَم يعمل؟
==============================================================
استدعاء صغير واحد لكل حَكَم (claude, kimi, glm, gpt4o) ولكل مولّد،
على محاضرة قصيرة حقيقية من نتائج v5. التكلفة: أقل من سنت تقريباً.

تشغيل:
    python smoke_v6.py               # السحابة فقط
    python smoke_v6.py --with-allam  # + ALLaM المحلي
"""
from __future__ import annotations

import argparse

import common


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-allam", action="store_true", help="(مرادف قديم لـ --with-local)")
    ap.add_argument("--with-local", action="store_true", help="اختبار ALLaM وLlama-3-8B المحليين أيضاً")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    common.setup("backprop", mock=a.mock or None)
    from judges import judge

    runs = common.load_v5_runs("backprop", condition="no_refine")
    lec = min(runs, key=lambda d: len(d["final_lecture"]))["final_lecture"][:3000]
    local = a.with_local or a.with_allam
    from routes import LOCAL_MODELS, available, describe
    from judges import JUDGE_SPECS
    print("الحكّام:", {r: f"{b}:{i}" for r, (b, i) in JUDGE_SPECS.items()})
    print("المولّدات:", describe())
    gens = [m for m in common.MODELS if available(m, include_substitutes=True) and (m not in LOCAL_MODELS or local)]
    print("غير متاح (يُتخطّى):", [m for m in common.MODELS if not available(m, True)])
    roles = ["claude", "kimi", "glm", "gpt4o"] + [f"gen:{m}" for m in gens]
    ok_all = True
    for r in roles:
        res = judge(r, lec, prompt="panel_compact", retries=1)
        ok = not res.get("error")
        ok_all &= ok
        info = (f"composite={res['composite']:.2f}  out_tokens={res['completion_tokens']}"
                + (f"  via={res.get('served_by')}" if res.get("served_by") else "")) if ok else res["error"][:150]
        print(f"  {'✓' if ok else '✗'} {r:<20} {res['model_id']:<48} {info}")
        if ok and res["completion_tokens"] > 600:
            print("      ⚠️  رموز إخراج كثيرة لرد قصير — قد يكون «التفكير» مفعّلاً (يكلّف أكثر). أرسلي هذا السطر.")
        if r == "gen:allam_7b":
            import clients.allam_local as al
            al._model = None
        if r == "gen:llama_3_8b":
            import llama_local_client as ll
            ll.release()
    print("\nكل شيء جاهز ✓" if ok_all else "\n⚠️  أصلحي ما فشل (المفتاح/الرصيد/معرّف النموذج) قبل التشغيل الكامل.")


if __name__ == "__main__":
    main()
