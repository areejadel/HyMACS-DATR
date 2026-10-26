"""
guard.py — حارس الرصيد: يوقف التشغيل فوراً عند أي خلل حتى لا يُهدَر الرصيد
=============================================================================
يلفّ دالة generate في كل عملاء v5 (Together / OpenAI / Anthropic / ALLaM)، ويقيس
كل استدعاء ويوقف التشغيل كله في الحالات التالية:

  1) فشل متتالٍ: إذا فشلت 8 استدعاءات متتالية لنفس المزوّد (مفتاح خاطئ، رصيد منتهٍ،
     نموذج محذوف، ردود فارغة...) ⇒ توقّف.
  2) نسبة فشل عالية: إذا فشل ≥ 30% من آخر 40 استدعاء لمزوّد ⇒ توقّف.
  3) سقف الصرف: إذا تجاوز الصرف التقديري لمزوّد السقف المحدّد ⇒ توقّف.
       V6_CAP_TOGETHER   (افتراضي 20 دولاراً — مجموع ما شُحن)
       V6_CAP_OPENROUTER (افتراضي 9 — شحن 10)
       V6_CAP_OPENAI     (افتراضي 30)
       V6_CAP_ANTHROPIC  (افتراضي 15)
     الصرف يُحفظ تراكمياً في results_v6/spend_ledger.jsonl، فيُحتسب عبر كل التشغيلات.
  4) إيقاف يدوي: أنشئي ملفاً اسمه STOP داخل results_v6/ ⇒ يتوقف خلال ثوانٍ
     (touch results_v6/STOP)  — احذفيه قبل التشغيل التالي.

بعد التوقّف لا يُرسَل أي استدعاء جديد، ولا يُحفظ أي سجلّ ناقص؛ ويُكتب السبب في
results_v6/STOPPED_REASON.txt. أصلحي السبب ثم أعيدي نفس الأمر فيكمل من حيث توقّف.
"""
from __future__ import annotations

import json
import os
import threading
import time
from collections import deque

# أسعار تقديرية لكل مليون رمز (إدخال، إخراج) بالدولار — للحماية فقط، وليست فاتورة.
# مصدرها جداول أسعار Together/OpenAI/Anthropic المنشورة (أكتوبر 2026)؛ اختير الأعلى عند التضارب.
# يمكن تعديلها بملف results_v6/prices_v6.json بنفس الشكل.
PRICES = {
    # OpenRouter (أكتوبر 2026)
    "moonshotai/kimi-k2.6": (0.46, 2.45),
    "z-ai/glm-5.1": (0.97, 3.04),
    "deepseek/deepseek-v4-pro": (0.96, 1.91),
    "qwen/qwen3-235b-a22b-2507": (0.09, 0.55),
    "google/gemma-4-31b-it": (0.09, 0.34),
    "moonshotai/kimi-k3": (3.00, 15.00),      # عبر OpenRouter → Together
    "z-ai/glm-5.2": (1.40, 4.40),
    # Together (أكتوبر 2026، من /v1/models على حسابك)
    "moonshotai/Kimi-K3": (2.70, 13.50),
    "zai-org/GLM-5.2": (1.40, 4.40),
    "zai-org/GLM-5.3": (1.40, 4.40),
    "deepseek-ai/DeepSeek-V4-Pro-0813": (1.32, 3.96),
    "google/gemma-4-31b-it:free": (0.0, 0.0),
    "moonshotai/Kimi-K2.6": (1.20, 4.50),
    "zai-org/GLM-5.1": (1.40, 4.40),
    "deepseek-ai/DeepSeek-V4-Pro": (2.10, 4.40),
    "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8": (0.20, 0.60),
    "google/gemma-4-31B-it": (0.39, 0.97),
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": (1.04, 1.04),
    "meta-llama/Meta-Llama-3-8B-Instruct-Lite": (0.14, 0.14),
    "gpt-4o": (2.50, 10.00),
    "claude-sonnet-4-6": (3.00, 15.00),
}
DEFAULT_PRICE = (2.50, 10.00)
JUDGE_MODELS = {"moonshotai/Kimi-K2.6", "zai-org/GLM-5.1", "gpt-4o", "claude-sonnet-4-6",
                "moonshotai/kimi-k2.6", "z-ai/glm-5.1", "moonshotai/Kimi-K3", "zai-org/GLM-5.2",
                "zai-org/GLM-5.3"}          # لأي نموذج غير معروف: افتراض متحفّظ
CAPS = {
    "openrouter": float(os.getenv("V6_CAP_OPENROUTER", "9.8")),
    "together": float(os.getenv("V6_CAP_TOGETHER", "20")),
    "openai": float(os.getenv("V6_CAP_OPENAI", "30")),
    "anthropic": float(os.getenv("V6_CAP_ANTHROPIC", "15")),
    "local": float("inf"),
}
MAX_CONSECUTIVE_FAIL = int(os.getenv("V6_MAX_CONSEC_FAIL", "8"))
WINDOW, MAX_FAIL_RATE = 40, 0.30


class Stopped(Exception):
    """يُرفع عند تفعيل الحارس — يوقف المهمة الحالية دون حفظ نتائج ناقصة."""


class _Guard:
    def __init__(self):
        self.lock = threading.Lock()
        self.stop_reason: str | None = None
        self.spend = {p: 0.0 for p in CAPS}
        self.session_spend = {p: 0.0 for p in CAPS}
        self.calls = {p: 0 for p in CAPS}
        self.consec = {p: 0 for p in CAPS}
        self.window = {p: deque(maxlen=WINDOW) for p in CAPS}
        self.out_dir = None
        self.prices = dict(PRICES)
        self.qconsec: dict[str, int] = {}
        self.mconsec: dict[str, int] = {}                 # فشل متتالٍ لكل نموذج
        self.mwindow: dict[str, deque] = {}
        self.tl = threading.local()                       # عدّاد فشل لكل مهمة (خيط)

    # ── تهيئة ──
    def init(self, out_dir):
        self.out_dir = out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "prices_v6.json"
        if p.exists():
            self.prices.update({k: tuple(v) for k, v in json.loads(p.read_text()).items()})
        led = out_dir / "spend_ledger.jsonl"
        if led.exists():
            for line in led.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                    self.spend[r["provider"]] = self.spend.get(r["provider"], 0.0) + r["usd"]
                except Exception:
                    continue
        if (out_dir / "STOP").exists():
            self.stop_reason = "ملف STOP موجود في results_v6/ — احذفيه للمتابعة"
        print("  [حارس الرصيد] الصرف المسجّل حتى الآن: " +
              ", ".join(f"{p}=${self.spend[p]:.2f}/{CAPS[p]:.0f}" for p in ("openrouter", "together", "openai", "anthropic")))
        for p in ("openrouter", "together", "openai", "anthropic"):
            if self.spend[p] >= CAPS[p]:
                self.stop_reason = (f"صرف {p} المسجّل (${self.spend[p]:.2f}) بلغ السقف ${CAPS[p]:.0f}. "
                                    f"ارفعي السقف: V6_CAP_{p.upper()}=...")

    @property
    def stopped(self) -> bool:
        if self.stop_reason is None and self.out_dir is not None and (self.out_dir / "STOP").exists():
            self.trip("إيقاف يدوي (ملف STOP)")
        return self.stop_reason is not None

    def check(self):
        if self.stopped:
            raise Stopped(self.stop_reason)

    def trip(self, reason: str):
        with self.lock:
            if self.stop_reason is None:
                self.stop_reason = reason
                print("\n" + "!" * 70 + f"\n  ⛔ توقّف حارس الرصيد: {reason}\n" + "!" * 70 + "\n", flush=True)
                if self.out_dir:
                    (self.out_dir / "STOPPED_REASON.txt").write_text(
                        time.strftime("%Y-%m-%d %H:%M:%S") + "\n" + reason + "\n", encoding="utf-8")

    # ── تسجيل استدعاء ──
    def record(self, provider: str, model_id: str, ok: bool, pt: int, ct: int, err: str | None):
        pin, pout = self.prices.get(model_id, DEFAULT_PRICE)
        usd = (pt * pin + ct * pout) / 1e6
        with self.lock:
            self.calls[provider] += 1
            self.spend[provider] += usd
            self.session_spend[provider] += usd
            rate_limited = (not ok) and ("429" in str(err) or "RateLimit" in str(err))
            if not rate_limited:            # 429 = ازدحام مؤقت لا يكلّف شيئاً ⇒ لا يدخل نسبة الفشل
                self.window[provider].append(ok)
            self.consec[provider] = 0 if ok else self.consec[provider] + 1
            if self.out_dir and usd > 0:
                with open(self.out_dir / "spend_ledger.jsonl", "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"t": int(time.time()), "provider": provider, "model": model_id,
                                         "pt": pt, "ct": ct, "usd": round(usd, 6), "ok": ok}) + "\n")
            self.mconsec[model_id] = 0 if ok else self.mconsec.get(model_id, 0) + 1
            mw = self.mwindow.setdefault(model_id, deque(maxlen=WINDOW))
            if not rate_limited:
                mw.append(ok)
            consec = max(self.consec[provider], self.mconsec[model_id])
            w = self.window[provider]
            rate = max((1 - sum(w) / len(w)) if len(w) >= WINDOW else 0.0,
                       (1 - sum(mw) / len(mw)) if len(mw) >= WINDOW else 0.0)
            spent = self.spend[provider]
        if not ok and model_id not in JUDGE_MODELS:     # فشل مولّد (وكيل كتابة) داخل المهمة
            self.tl.fails = getattr(self.tl, "fails", 0) + 1
        if consec >= MAX_CONSECUTIVE_FAIL:
            self.trip(f"{consec} استدعاءات فاشلة متتالية لدى {provider} ({model_id}). آخر خطأ: {str(err)[:300]}")
        elif rate >= MAX_FAIL_RATE:
            self.trip(f"نسبة فشل {rate:.0%} في آخر {WINDOW} استدعاء لدى {provider} ({model_id}). آخر خطأ: {str(err)[:300]}")
        elif spent >= CAPS[provider]:
            self.trip(f"صرف {provider} التقديري ${spent:.2f} بلغ السقف ${CAPS[provider]:.0f}")

    def reset_task(self):
        self.tl.fails = 0

    def task_fails(self) -> int:
        return getattr(self.tl, "fails", 0)

    def quality(self, key: str, ok: bool, detail: str = ""):
        """إشارة جودة (JSON غير صالح، مراجعة مقطوعة...) — تكلّف مالاً دون فائدة إن تكررت."""
        with self.lock:
            n = 0 if ok else self.qconsec.get(key, 0) + 1
            self.qconsec[key] = n
        if n >= MAX_CONSECUTIVE_FAIL:
            self.trip(f"{n} مخرجات غير صالحة متتالية من {key} ({detail[:200]}). "
                      f"غالباً تغيّر سلوك النموذج أو معرّفه — افحصي smoke_v6.py")

    def summary(self) -> str:
        return " | ".join(f"{p} ${self.session_spend[p]:.2f} ({self.calls[p]} call)"
                          for p in ("openrouter", "together", "openai", "anthropic", "local") if self.calls[p])


GUARD = _Guard()


def _provider_of(obj) -> str:
    name = type(obj).__name__.lower()
    mid = str(getattr(obj, "model_id", "")).lower()
    if "openrouter" in name:
        return "openrouter"
    if "together" in name:
        return "together"
    if "openai" in name:
        return "openai"
    if "claude" in name:
        return "anthropic"
    if "allam" in name or "allam" in mid or "llamalocal" in name or "gguf" in mid:
        return "local"
    # العملاء الوهميون (--mock): من معرّف النموذج
    if mid.endswith(":free") or ("/" in mid and mid.split("/")[0] in ("z-ai", "deepseek", "qwen")):
        return "openrouter"
    if "claude" in mid:
        return "anthropic"
    if "gpt" in mid:
        return "openai"
    return "together"


def _wrap(cls):
    if getattr(cls.generate, "_v6_guarded", False):
        return
    orig = cls.generate

    def generate(self, *args, **kwargs):
        if GUARD.stopped:                       # لا استدعاء جديد بعد التوقّف
            raise Stopped(GUARD.stop_reason)
        res = orig(self, *args, **kwargs)
        ok = bool(getattr(res, "ok", False))
        pt = int(getattr(res, "prompt_tokens", 0) or 0)
        ct = int(getattr(res, "completion_tokens", 0) or 0)
        if pt == 0 and ct == 0:                 # بعض المزوّدين لا يعيدون الاستهلاك: تقدير متحفّظ
            msgs = kwargs.get("messages") or (args[0] if args else [])
            pt = int(sum(len(m.get("content", "")) for m in msgs) / 3.5)
            ct = int(len(getattr(res, "text", "") or "") / 3.5)
        GUARD.record(_provider_of(self), str(getattr(self, "model_id", "?")), ok, pt, ct,
                     getattr(res, "error", None))
        if GUARD.stopped:
            raise Stopped(GUARD.stop_reason)
        return res

    generate._v6_guarded = True
    cls.generate = generate


def install(out_dir):
    """يلفّ كل عملاء v5 (يُستدعى من common.setup)."""
    GUARD.init(out_dir)
    import clients.claude_client as cc
    import clients.openai_client as oc
    import clients.together_client as tc
    from clients.base import BaseClient
    targets = set()
    for mod, name in ((cc, "ClaudeClient"), (oc, "OpenAIClient"), (tc, "TogetherClient")):
        obj = getattr(mod, name)
        if isinstance(obj, type):
            targets.add(obj)
    for modname, name in (("clients.allam_local", "AllamLocalClient"), ("clients.allam_mlx", "AllamMlxClient"),
                          ("clients.allam_cuda", "AllamCudaClient"), ("openrouter_client", "OpenRouterClient"),
                          ("llama_local_client", "LlamaLocalClient"), ("together_v6_client", "TogetherV6Client")):
        try:
            mod = __import__(modname, fromlist=[name])
            targets.add(getattr(mod, name))
        except Exception:
            pass
    try:
        import mock_clients
        if os.getenv("V6_MOCK") == "1":
            targets.add(mock_clients.FakeClient)
    except ImportError:
        pass
    for cls in targets:
        if issubclass(cls, BaseClient):
            _wrap(cls)
