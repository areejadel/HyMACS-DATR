"""
openai_client.py — Client for the inner judge (GPT-4o)
==================================================
Supports structured output via JSON schema to score the 8 dimensions.
"""
from __future__ import annotations
import json
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

from clients.base import BaseClient, GenerationResult
from config import OPENAI_API_KEY


_RETRYABLE = (
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.RateLimitError,
    openai.InternalServerError,
)


class OpenAIClient(BaseClient):
    """Client for OpenAI — uses GPT-4o as the inner judge."""

    def __init__(self, model_id: str = "gpt-4o", temperature: float = 0.2, label: str = ""):
        super().__init__(model_id, label)
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set. Put it in .env")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.default_temperature = temperature

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=False,
    )
    def _call(self, messages, max_tokens, temperature, response_format=None, **kwargs):
        params = dict(
            model=self.model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response_format:
            params["response_format"] = response_format
        params.update(kwargs)
        return self.client.chat.completions.create(**params)

    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1500,
        temperature: float | None = None,
        response_format=None,
        **kwargs,
    ) -> GenerationResult:
        if temperature is None:
            temperature = self.default_temperature
        try:
            resp = self._call(messages, max_tokens, temperature, response_format=response_format, **kwargs)
            text = resp.choices[0].message.content or ""
            usage = resp.usage
            return GenerationResult(
                text=text.strip(),
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

    def generate_json(
        self,
        messages: list[dict],
        schema: dict,
        max_tokens: int = 1500,
        temperature: float | None = None,
    ) -> tuple[dict | None, GenerationResult]:
        """
        Returns (parsed_dict, raw_result).
        parsed_dict = None if parsing or generation failed.
        """
        result = self.generate(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        if not result.ok:
            return None, result
        try:
            parsed = json.loads(result.text)
            return parsed, result
        except json.JSONDecodeError as e:
            result.error = f"JSON parse error: {e}"
            return None, result
