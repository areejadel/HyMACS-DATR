"""
openrouter_client.py — عميل OpenRouter (واجهة متوافقة مع OpenAI)
=================================================================
لماذا؟ في أكتوبر 2026 أوقفت Together الخدمة «بلا خادم» (serverless) لـ:
Kimi-K2.6، GLM-5.1، Qwen3-235B-2507، Gemma-4-31B، DeepSeek-V4-Pro (غير المؤرّخ)، Llama-3-8B.
نفس هذه النماذج (بنفس الإصدار) متاحة على OpenRouter، فنستخدمه بدلاً منها.

المفتاح: أضيفي إلى ../v5/.env السطر:
    OPENROUTER_API_KEY=sk-or-...
"""
from __future__ import annotations

import os

from openai import OpenAI
import openai
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from clients.base import BaseClient, GenerationResult


def _retryable(e: BaseException) -> bool:
    if isinstance(e, (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError,
                      openai.InternalServerError)):
        return True
    return isinstance(e, openai.APIStatusError) and getattr(e, "status_code", 0) in (408, 409, 429, 502, 503, 504)


PINNED = {
    "google/gemma-4-31b-it": ["DeepInfra"],
    "deepseek/deepseek-v4-pro": ["StreamLake"],
    "qwen/qwen3-235b-a22b-2507": ["Nebius"],
    # Llama-3.3-70B لم يعد «بلا خادم» على Together (أكتوبر 2026) ⇒ نفس الأوزان عبر OpenRouter بدقة FP8 مثل Turbo
    "meta-llama/llama-3.3-70b-instruct": ["DeepInfra"],
    # حَكَما اللجنة عبر OpenRouter بعد نفاد رصيد Together (25 أكتوبر 2026) ⇒ مثبّتان على Together نفسه، بلا بديل
    "moonshotai/kimi-k3": ["Together"],
    "z-ai/glm-5.2": ["Together"],
}
NO_FALLBACK = {"moonshotai/kimi-k3", "z-ai/glm-5.2"}


class OpenRouterClient(BaseClient):
    def __init__(self, model_id: str, label: str = "", temperature: float = 0.7):
        super().__init__(model_id, label)
        key = os.getenv("OPENROUTER_API_KEY", "")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY غير موجود. أضيفيه إلى ../v5/.env")
        self.client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1",
                             timeout=180.0, max_retries=0)
        self.default_temperature = temperature
        # إيقاف «التفكير» للنماذج الهجينة (كما في v5 مع Together) حتى لا تُستهلك الرموز في التفكير
        self.extra = {"reasoning": {"enabled": False}}
        # تثبيت المزوّد لكل نموذج (نفس من خدمه في الفحص) حتى تأتي كل استدعاءات النموذج من نفس المضيف؛
        # البديل مسموح فقط إن تعطّل المضيف. المزوّد الفعلي يُسجّل في served_by.
        order = os.getenv("OPENROUTER_PROVIDER_ORDER", "").strip()
        pinned = [p.strip() for p in order.split(",") if p.strip()] if order else PINNED.get(model_id.split(":")[0])
        if pinned:
            self.extra["provider"] = {"order": pinned,
                                      "allow_fallbacks": model_id.split(":")[0] not in NO_FALLBACK}
        if model_id.split(":")[0] in NO_FALLBACK:   # نفس إعدادات TogetherV6Client
            self.extra["chat_template_kwargs"] = {"thinking": False, "enable_thinking": False}

    @retry(retry=retry_if_exception(_retryable), wait=wait_exponential(multiplier=2, min=2, max=30),
           stop=stop_after_attempt(5), reraise=True)
    def _call(self, messages, max_tokens, temperature, **kwargs):
        return self.client.chat.completions.create(
            model=self.model_id, messages=messages, max_tokens=max_tokens,
            temperature=temperature, extra_body=self.extra, **kwargs)

    def generate(self, messages, max_tokens: int = 1500, temperature: float | None = None,
                 **kwargs) -> GenerationResult:
        if temperature is None:
            temperature = self.default_temperature
        kwargs.pop("response_format", None)
        if "gemma" in self.model_id.lower():      # كما في v5: Gemma بلا دور system ⇒ يُدمج في أول رسالة
            from clients.together_client import _merge_system_into_user
            messages = _merge_system_into_user(messages)
        try:
            resp = self._call(messages, max_tokens, temperature, **kwargs)
            text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
            usage = resp.usage
            pt = getattr(usage, "prompt_tokens", 0) if usage else 0
            ct = getattr(usage, "completion_tokens", 0) if usage else 0
            extra = getattr(resp, "model_extra", None) or {}
            served = extra.get("provider") or getattr(resp, "provider", None)
            if not text:
                fr = resp.choices[0].finish_reason if resp.choices else "?"
                r = GenerationResult(text="", model=self.model_id, prompt_tokens=pt, completion_tokens=ct,
                                     error=f"Empty response (finish_reason={fr})")
            else:
                r = GenerationResult(text=text, model=self.model_id, prompt_tokens=pt, completion_tokens=ct)
            r.served_by = served
            return r
        except Exception as e:
            return GenerationResult(text="", model=self.model_id, error=f"{type(e).__name__}: {e}")
