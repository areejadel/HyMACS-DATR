"""
together_v6_client.py — عميل Together لـ v6 (حكّام ومولّدات)
==============================================================
الفرق عن clients/together_client.py في v5:
  1) يمرّر درجة الحرارة دائماً (v5 كان يترك حكّام Together على 0.7 الافتراضية).
  2) يوقف «التفكير» بكل الصيغ التي تقبلها نماذج Together الحالية
     (reasoning.enabled=false + chat_template_kwargs.thinking/enable_thinking=false).
     فُحص حيّاً (أكتوبر 2026): Kimi-K3 وGLM-5.2 وDeepSeek-V4-Pro-0813 وLlama-3.3-70B
     تُرجع الجواب مباشرة بلا رموز تفكير ⇒ لا رموز مدفوعة مهدرة.
  3) مهلة أطول (180 ث) للمراجعات الطويلة، وإعادة محاولة على الأخطاء العابرة فقط.
     أخطاء الرصيد (402) تُعاد مرتين فقط ثم تُعتبر فشلاً ⇒ الحارس يوقف التشغيل سريعاً.
"""
from __future__ import annotations

import openai
from openai import OpenAI
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from clients.base import BaseClient, GenerationResult
from clients.together_client import _merge_system_into_user, _model_needs_system_merge


def _retryable(e: BaseException) -> bool:
    if isinstance(e, (openai.APIConnectionError, openai.APITimeoutError, openai.RateLimitError,
                      openai.InternalServerError)):
        return True
    return isinstance(e, openai.APIStatusError) and getattr(e, "status_code", 0) in (402, 408, 409, 429, 502, 503, 504)


NO_THINKING = {"reasoning": {"enabled": False},
               "chat_template_kwargs": {"thinking": False, "enable_thinking": False}}


class TogetherV6Client(BaseClient):
    def __init__(self, model_id: str, label: str = "", temperature: float = 0.7):
        super().__init__(model_id, label)
        from config import TOGETHER_API_KEY
        if not TOGETHER_API_KEY:
            raise RuntimeError("TOGETHER_API_KEY غير موجود في ../v5/.env")
        self.client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1",
                             timeout=180.0, max_retries=0)
        self.default_temperature = temperature
        self._merge_system = _model_needs_system_merge(model_id)

    @retry(retry=retry_if_exception(_retryable), wait=wait_exponential(multiplier=2, min=4, max=60),
           stop=stop_after_attempt(8), reraise=True)
    def _call(self, messages, max_tokens, temperature, **kwargs):
        return self.client.chat.completions.create(
            model=self.model_id, messages=messages, max_tokens=max_tokens,
            temperature=temperature, extra_body=dict(NO_THINKING), **kwargs)

    def generate(self, messages, max_tokens: int = 1500, temperature: float | None = None,
                 **kwargs) -> GenerationResult:
        if temperature is None:
            temperature = self.default_temperature
        kwargs.pop("extra_body", None)
        if self._merge_system:
            messages = _merge_system_into_user(messages)
        try:
            resp = self._call(messages, max_tokens, temperature, **kwargs)
            text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
            u = resp.usage
            pt = getattr(u, "prompt_tokens", 0) if u else 0
            ct = getattr(u, "completion_tokens", 0) if u else 0
            if not text:
                fr = resp.choices[0].finish_reason if resp.choices else "?"
                return GenerationResult(text="", model=self.model_id, prompt_tokens=pt, completion_tokens=ct,
                                        error=f"Empty response (finish_reason={fr})")
            return GenerationResult(text=text, model=self.model_id, prompt_tokens=pt, completion_tokens=ct)
        except Exception as e:
            return GenerationResult(text="", model=self.model_id, error=f"{type(e).__name__}: {e}")
