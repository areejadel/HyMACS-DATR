"""
common.py — أدوات مشتركة لتجارب التقوية v6
============================================
- لا يعدّل أي ملف في v5: يستورد كود v5 كما هو ويقرأ نتائجه فقط.
- كل مخرجات v6 تُكتب في:  v6_تقوية/results_v6/
- كل تجربة تُستأنف تلقائياً (resume): أي سجلّ محفوظ لا يُعاد طلبه.

المسارات (افتراضياً):
    .../01_الكود/محاولات/v5          ← الكود والنتائج الأصلية
    .../01_الكود/محاولات/v6_تقوية    ← هذا المجلد
"""
from __future__ import annotations

import json
import os
import random
import sys
import threading
import time
from pathlib import Path
from statistics import median

V6_DIR = Path(__file__).resolve().parent
_V5_SIBLING = V6_DIR.parent / "v5"           # local layout: محاولات/v5 + محاولات/v6_تقوية
V5_DIR = Path(os.getenv("V5_DIR", str(_V5_SIBLING if _V5_SIBLING.exists() else V6_DIR.parent))).resolve()  # GitHub layout: repo root
OUT_DIR = Path(os.getenv("V6_OUT", str(V6_DIR / "results_v6"))).resolve()
# v5 → محاولات → 01_الكود → 11_خطة_v5_النشر
PLAN_DIR = V5_DIR.parents[2]
HUMAN_DIR = Path(os.getenv("HUMAN_DIR", str(PLAN_DIR / "05_التقييم_البشري" / "04_ردود_المحكمين")))

TOPICS = ("backprop", "normalization")
MODELS = ["allam_7b", "llama_3_8b", "llama_3_3_70b", "gemma_4_31b", "deepseek_v3_1", "qwen3_235b"]
STRONG = {"gemma_4_31b", "deepseek_v3_1", "qwen3_235b"}
MODEL_LABEL = {
    "allam_7b": "ALLaM-7B", "llama_3_8b": "Llama-3-8B", "llama_3_3_70b": "Llama-3.3-70B",
    "gemma_4_31b": "Gemma-4-31B", "deepseek_v3_1": "DeepSeek-V4-Pro", "qwen3_235b": "Qwen3-235B",
}
V5_CONDITIONS = ["no_refine", "self_refine", "datr_no_guard", "datr_full"]
DIMS = [
    "academic_accuracy", "pedagogical_effectiveness", "clarity_organization",
    "practical_relevance", "completeness", "engagement_potential",
    "technical_quality", "innovation",
]
JUDGE_TEMPERATURE = 0.2          # درجة حرارة موحّدة لكل الحكّام (تصحيح خلل v5)

MOCK = os.getenv("V6_MOCK", "0") == "1"


# ─────────────────────────────────────────────────────────────
#  تهيئة بيئة v5 (يجب أن تُستدعى قبل أي import من كود v5)
# ─────────────────────────────────────────────────────────────
_SETUP_TOPIC: str | None = None


def setup(topic: str = "backprop", mock: bool | None = None):
    """يضبط TOPIC ويضيف v5 إلى sys.path وينتقل إلى مجلده (مسارات الكتب نسبية).

    ملاحظة: config في v5 يقرأ TOPIC مرّة واحدة عند الاستيراد، لذلك تجارب
    التوليد (exp1/exp6) تعمل على موضوع واحد لكل عملية.
    """
    global _SETUP_TOPIC, MOCK
    if mock is not None:
        MOCK = mock
        os.environ["V6_MOCK"] = "1" if mock else "0"
    if _SETUP_TOPIC is not None and _SETUP_TOPIC != topic:
        raise RuntimeError(f"setup() استُدعي مسبقاً بموضوع {_SETUP_TOPIC}؛ شغّلي كل موضوع في عملية مستقلة.")
    _SETUP_TOPIC = topic
    os.environ["TOPIC"] = topic
    if not V5_DIR.exists():
        raise FileNotFoundError(f"مجلد v5 غير موجود: {V5_DIR}  (أو اضبطي V5_DIR)")
    os.chdir(V5_DIR)
    if str(V5_DIR) not in sys.path:
        sys.path.insert(0, str(V5_DIR))
    if str(V6_DIR) not in sys.path:
        sys.path.insert(1, str(V6_DIR))
    if MOCK:
        import mock_clients
        mock_clients.install()
    import config  # noqa: E402
    assert list(config.RUBRIC_DIMENSIONS) == DIMS, "أبعاد الـ rubric في v5 تغيّرت!"
    if not MOCK:
        import routes  # noqa: E402  — Together/OpenRouter/محلي حسب التوفّر الحالي
        routes.install()
    import guard  # noqa: E402  — حارس الرصيد يلفّ كل العملاء
    guard.install(OUT_DIR)
    # استيراد مسبق في الخيط الرئيسي (يمنع سباق الاستيراد بين الخيوط المتوازية)
    import pipeline  # noqa: F401,E402
    import pipeline.judge_panel  # noqa: F401,E402
    import pipeline.inner_judge  # noqa: F401,E402
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return config


# ─────────────────────────────────────────────────────────────
#  قراءة نتائج v5
# ─────────────────────────────────────────────────────────────
def v5_runs_dir(topic: str) -> Path:
    return V5_DIR / "results" / topic / "runs"


def load_v5_runs(topic: str, condition: str | None = None, with_text: bool = True) -> list[dict]:
    """يقرأ ملفات runs/*.json لموضوع (يتجاهل ملفات macOS ._*)."""
    out = []
    for f in sorted(v5_runs_dir(topic).glob("*.json")):
        if f.name.startswith("._"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if condition and d.get("condition") != condition:
            continue
        d["_run"] = f.stem            # مثل: qwen3_235b__no_refine__seed1
        d["_topic"] = topic
        if not with_text:
            for it in d.get("iterations", []):
                it.pop("lecture", None)
        out.append(d)
    return out


def human_lecture_runs() -> dict[str, tuple[str, str]]:
    """L01.. → (topic, run_name) من ملف الربط السرّي (إن وُجد)."""
    import csv
    p = HUMAN_DIR / "_secret_mapping_للباحثة_فقط.csv"
    if not p.exists():
        return {}
    res = {}
    with open(p, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            res[r["lecture_id"]] = (r["topic"], f'{r["model"]}__{r["condition"]}__seed{int(float(r["seed"]))}')
    return res


# ─────────────────────────────────────────────────────────────
#  درجات مركّبة وتجميع
# ─────────────────────────────────────────────────────────────
def composite(scores: dict | None) -> float:
    """المتوسط المنتظم للأبعاد الثمانية (كما تصفه الورقة). NaN إن نقص بُعد."""
    if not scores:
        return float("nan")
    vals = [float(scores.get(d, 0) or 0) for d in DIMS]
    if any(v <= 0 for v in vals):
        return float("nan")
    return sum(vals) / len(vals)


def median_scores(per_judge: list[dict]) -> dict:
    """وسيط كل بُعد عبر الحكّام الناجحين."""
    out = {}
    for d in DIMS:
        vals = [float(j["scores"][d]) for j in per_judge
                if j and not j.get("error") and float(j["scores"].get(d, 0) or 0) > 0]
        out[d] = float(median(vals)) if vals else 0.0
    return out


def truncate_at_paragraph(text: str, max_chars: int | None) -> str:
    """يقصّ النص عند حدّ فقرة قبل max_chars (إن أمكن)."""
    if not max_chars or len(text) <= max_chars:
        return text
    cut = text.rfind("\n\n", 0, max_chars)
    if cut < int(max_chars * 0.7):
        cut = text.rfind("\n", 0, max_chars)
    if cut < int(max_chars * 0.7):
        cut = max_chars
    return text[:cut].rstrip()


# ─────────────────────────────────────────────────────────────
#  مخزن JSONL قابل للاستئناف وآمن مع الخيوط
# ─────────────────────────────────────────────────────────────
class JsonlStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.records: dict[str, dict] = {}
        if self.path.exists():
            with open(self.path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue          # سطر مقطوع بسبب انقطاع — يُتجاهل ويُعاد
                    self.records[r["key"]] = r   # الأحدث يغلب

    def has(self, key: str, ok_only: bool = True) -> bool:
        r = self.records.get(key)
        if r is None:
            return False
        return (not r.get("error")) if ok_only else True

    def get(self, key: str):
        return self.records.get(key)

    def add(self, rec: dict):
        assert "key" in rec
        rec.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
        line = json.dumps(rec, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            self.records[rec["key"]] = rec

    def values(self):
        return list(self.records.values())


def run_parallel(jobs, fn, workers: int = 4, label: str = ""):
    """ينفّذ fn(job) بخيوط متوازية مع عدّاد تقدّم. يتوقف كلياً إن فعّل حارسُ الرصيد الإيقاف."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from guard import GUARD, Stopped
    jobs = list(jobs)
    n = len(jobs)
    if n == 0:
        print(f"  [{label}] لا مهام متبقّية ✓")
        return
    if GUARD.stopped:
        print(f"  [{label}] ⛔ لم يبدأ — الحارس متوقّف: {GUARD.stop_reason}")
        sys.exit(2)
    print(f"  [{label}] {n} مهمة — workers={workers}")

    def _safe(j):
        if GUARD.stopped:
            return "skipped"
        return fn(j)

    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_safe, j): j for j in jobs}
        for fu in as_completed(futs):
            done += 1
            try:
                fu.result()
            except Stopped:
                pass
            except Exception as e:  # لا نوقف الدفعة كلها بسبب مهمة واحدة (الحارس يتولّى التكرار)
                j = futs[fu]
                tag = j[0] if isinstance(j, tuple) else j
                print(f"    ✗ خطأ في {str(tag)[:120]}: {type(e).__name__}: {str(e)[:300]}")
            if done % max(1, n // 20) == 0 or done == n:
                el = time.time() - t0
                eta = el / done * (n - done)
                print(f"    {done}/{n}  ({el/60:.1f} د، المتبقّي ≈ {eta/60:.1f} د)  الصرف: {GUARD.summary()}",
                      flush=True)
            if GUARD.stopped:
                for f in futs:
                    f.cancel()
    if GUARD.stopped:
        print(f"\n⛔ [{label}] توقّف التشغيل: {GUARD.stop_reason}\n"
              f"   النتائج المكتملة محفوظة. أصلحي السبب ثم أعيدي نفس الأمر ليكمل من حيث توقّف.")
        sys.exit(2)


def rng(seed: int = 2026) -> random.Random:
    return random.Random(seed)
