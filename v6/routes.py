"""
routes.py — من أين يُخدم كل نموذج في v6
========================================
فُحص حيّاً (9 أكتوبر 2026):
  Together «بلا خادم» ما زال يخدم من نماذجنا: Llama-3.3-70B-Instruct-Turbo فقط
  (+ الحكّام Kimi-K3 وGLM-5.2، وDeepSeek-V4-Pro-0813 المؤرّخ).
  Gemma-4-31B وQwen3-235B-2507 وDeepSeek-V4-Pro: نفس الأوزان متاحة على OpenRouter (مدفوع، رخيص).

المسارات:
  ALLaM / Llama-3-8B      ← محلي (كما في v5 / GGUF 4-bit)
  Llama-3.3-70B           ← Together (نفس v5)
  Gemma / Qwen / DeepSeek ← OpenRouter، فقط إذا وُجد OPENROUTER_API_KEY في ../v5/.env
                            (بدونه يُتخطّى النموذج تلقائياً، ولا يتأثر أي شيء آخر)

يمكن تجاوز أي مسار بمتغيّر بيئة:  V6_ROUTE_<model_key>=together:<id> | openrouter:<id> | unavailable:
مثال (البديل المؤرّخ على Together):  V6_ROUTE_deepseek_v3_1=together:deepseek-ai/DeepSeek-V4-Pro-0813
"""
from __future__ import annotations

import os

ROUTES = {
    "allam_7b":      ("v5", None),                                          # كما في v5 (GGUF محلي)
    "llama_3_8b":    ("local_llama", None),
    "llama_3_3_70b": ("together", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    "gemma_4_31b":   ("openrouter", "google/gemma-4-31b-it"),               # نفس أوزان v5
    "deepseek_v3_1": ("openrouter", "deepseek/deepseek-v4-pro"),            # نفس إصدار v5
    "qwen3_235b":    ("openrouter", "qwen/qwen3-235b-a22b-2507"),           # نفس إصدار v5
}
LOCAL_MODELS = {"allam_7b", "llama_3_8b"}


def _norm(mid: str | None) -> str:
    """معرّف مختصر للمقارنة بين المزوّدين (Qwen3-235B-A22B-Instruct-2507-FP8 ≡ qwen3-235b-a22b-2507)."""
    m = (mid or "").lower().split(":")[0].split("/")[-1]
    for suffix in ("-fp8",):
        m = m.replace(suffix, "")
    return m.replace("-instruct", "")


def is_substitute(model_key: str) -> bool:
    """True إذا كان المسار يخدم إصداراً يختلف عن معرّف v5 (فلا يُعدّ «نفس النموذج»)."""
    b, mid = route_of(model_key)
    if b in ("v5", "local_llama", "unavailable"):
        return False
    try:
        from config import GENERATORS
        v5_id = GENERATORS[model_key].api_id
    except Exception:
        return False
    return _norm(mid) != _norm(v5_id)


def available(model_key: str, include_substitutes: bool = False) -> bool:
    b, _ = route_of(model_key)
    if b == "unavailable":
        return False
    if b == "openrouter" and not os.getenv("OPENROUTER_API_KEY"):
        return False
    return include_substitutes or not is_substitute(model_key)


def route_of(model_key: str):
    env = os.getenv(f"V6_ROUTE_{model_key}")
    if env and ":" in env:
        b, i = env.split(":", 1)
        return b, (i or None)
    return ROUTES.get(model_key, ("v5", None))


def make_generator_client(model_key: str, _v5_get_client):
    from config import GENERATORS
    backend, mid = route_of(model_key)
    spec = GENERATORS.get(model_key)
    if backend == "openrouter":
        from openrouter_client import OpenRouterClient
        c = OpenRouterClient(mid, label=spec.label if spec else mid)
    elif backend == "together":
        from together_v6_client import TogetherV6Client
        c = TogetherV6Client(mid, label=spec.label if spec else mid)
    elif backend == "unavailable":
        raise RuntimeError(f"{model_key}: غير متاح حالياً (انظري routes.py)")
    elif backend == "local_llama":
        from llama_local_client import LlamaLocalClient
        c = LlamaLocalClient()
    else:
        return _v5_get_client(model_key)
    if spec is not None:
        c.context_tokens = spec.context_tokens          # نفس ميزانية السياق في v5
    return c


def install():
    """يستبدل clients.get_client بنسخة تحترم المسارات أعلاه (قبل استيراد pipeline)."""
    import clients
    orig = clients.get_client
    if getattr(orig, "_v6_routed", False):
        return

    def get_client(model_key: str):
        from config import GENERATORS
        if model_key in GENERATORS:
            return make_generator_client(model_key, orig)
        return orig(model_key)

    get_client._v6_routed = True
    clients.get_client = get_client


def describe() -> dict:
    out = {}
    for k in ROUTES:
        b, i = route_of(k)
        out[k] = (f"{b}:{i}" if i else b) + (" [substitute]" if is_substitute(k) else "")
    return out
