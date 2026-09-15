"""
together_client.py — Unified client for the generators on Together AI
==================================================================
Uses the OpenAI-compatible API. One key for:
  - Llama-3-8B-Instruct
  - Llama-3.3-70B-Instruct-Turbo
  - Qwen3-235B-A22B
  - DeepSeek-V4-Pro
  - Gemma-4-31B-Instruct (needs special handling — no system role)
"""
from __future__ import annotations
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

from tenacity import retry_if_exception
from clients.base import BaseClient, GenerationResult
from config import TOGETHER_API_KEY


# Errors worth retrying
_RETRYABLE = (
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.RateLimitError,
    openai.InternalServerError,
)


def _is_retryable(exc: BaseException) -> bool:
    """Retry on network errors + transient 402s from Together.
    Some endpoints (e.g. llama-70b) return 402 sporadically despite available credit —
    a retry makes the call succeed (the 402 is rejected before execution, so no credit is charged)."""
    if isinstance(exc, _RETRYABLE):
        return True
    # 402 (transient credit) + 404 (model momentarily "not found" due to Together instability):
    # both appear and disappear on the same model that actually exists => retry.
    if isinstance(exc, openai.APIStatusError) and getattr(exc, "status_code", None) in (402, 404):
        return True
    return False


def _merge_system_into_user(messages: list[dict]) -> list[dict]:
    """
    Gemma models do not support the 'system' role. Merge system into the first user message.
    """
    if not messages:
        return messages
    if messages[0].get("role") != "system":
        return messages

    sys_content = messages[0]["content"]
    rest = messages[1:]
    if rest and rest[0].get("role") == "user":
        merged = {
            "role": "user",
            "content": f"{sys_content}\n\n---\n\n{rest[0]['content']}",
        }
        return [merged] + rest[1:]
    # no user message — convert system to user
    return [{"role": "user", "content": sys_content}] + rest


def _model_needs_system_merge(model_id: str) -> bool:
    """The Gemma family does not support the system role."""
    mid = model_id.lower()
    return "gemma" in mid


class TogetherClient(BaseClient):
    """Client for Together AI — OpenAI-compatible interface."""

    def __init__(self, model_id: str, label: str = ""):
        super().__init__(model_id, label)
        if not TOGETHER_API_KEY:
            raise RuntimeError("TOGETHER_API_KEY is not set. Put it in .env")
        self.client = OpenAI(
            api_key=TOGETHER_API_KEY,
            base_url="https://api.together.xyz/v1",
            timeout=90.0,      # prevents infinite hangs: any request over 90s fails
            max_retries=0,     # we handle retries ourselves via tenacity (no double retry)
        )
        self._merge_system = _model_needs_system_merge(model_id)

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=2, min=2, max=20),
        stop=stop_after_attempt(6),   # ~30% transient 402 => 6 attempts = >99.9% success
        reraise=False,
    )
    def _call(self, messages, max_tokens, temperature, **kwargs):
        # Disable "thinking" (reasoning) for hybrid models on Together
        # (Gemma-4, Kimi-K2.6, GLM-5.1, ...). Without this, reasoning consumes the
        # token budget and content comes back empty, truncating lectures. Safe for Llama/Qwen/DeepSeek.
        extra = kwargs.pop("extra_body", {}) or {}
        ctk = extra.get("chat_template_kwargs", {})
        ctk.setdefault("enable_thinking", False)
        extra["chat_template_kwargs"] = ctk
        return self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            extra_body=extra,
            **kwargs,
        )

    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1500,
        temperature: float = 0.7,
        **kwargs,
    ) -> GenerationResult:
        try:
            # Gemma does not support the system role — merge it before sending
            if self._merge_system:
                messages = _merge_system_into_user(messages)

            resp = self._call(messages, max_tokens, temperature, **kwargs)
            text = resp.choices[0].message.content or ""
            usage = resp.usage
            text_stripped = text.strip()

            # if the text is empty, return a clear error instead of None
            if not text_stripped:
                finish = resp.choices[0].finish_reason if resp.choices else "?"
                return GenerationResult(
                    text="",
                    model=self.model_id,
                    error=f"Empty response (finish_reason={finish})",
                    prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
                    completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
                )

            return GenerationResult(
                text=text_stripped,
                model=self.model_id,
                prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            )
        except Exception as e:
            return GenerationResult(
                text="",
                model=self.model_id,
                error=f"{type(e).__name__}: {e}",
            )
