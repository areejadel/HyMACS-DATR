"""
claude_client.py — Client for the external judge (Claude Sonnet)
=============================================================
Used as one of the cross-family panel judges.
"""
from __future__ import annotations
import json
import re
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from clients.base import BaseClient, GenerationResult
from config import ANTHROPIC_API_KEY


_RETRYABLE = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)


class ClaudeClient(BaseClient):
    """Client for Anthropic Claude — external judge."""

    def __init__(self, model_id: str = "claude-sonnet-4-6", temperature: float = 0.2, label: str = ""):
        super().__init__(model_id, label)
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Put it in .env")
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.default_temperature = temperature

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=False,
    )
    def _call(self, system_text, user_messages, max_tokens, temperature, **kwargs):
        params = dict(
            model=self.model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=user_messages,
        )
        if system_text:
            params["system"] = system_text
        params.update(kwargs)
        return self.client.messages.create(**params)

    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1500,
        temperature: float | None = None,
        **kwargs,
    ) -> GenerationResult:
        """
        The Anthropic API separates system from messages. Extract system from the messages list.
        """
        if temperature is None:
            temperature = self.default_temperature

        # separate system from the other messages
        system_text = ""
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            else:
                user_messages.append({"role": m["role"], "content": m["content"]})

        try:
            resp = self._call(system_text, user_messages, max_tokens, temperature, **kwargs)
            # extract text from content blocks
            text_parts = [b.text for b in resp.content if hasattr(b, "text")]
            text = "".join(text_parts).strip()
            return GenerationResult(
                text=text,
                model=self.model_id,
                prompt_tokens=resp.usage.input_tokens if resp.usage else 0,
                completion_tokens=resp.usage.output_tokens if resp.usage else 0,
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
        max_tokens: int = 1500,
        temperature: float | None = None,
    ) -> tuple[dict | None, GenerationResult]:
        """
        Anthropic has no response_format=json_object like OpenAI, so we rely on
        prompt engineering + extraction.
        """
        result = self.generate(messages=messages, max_tokens=max_tokens, temperature=temperature)
        if not result.ok:
            return None, result
        try:
            # attempt 1: direct parse
            return json.loads(result.text), result
        except json.JSONDecodeError:
            pass
        # attempt 2: extract a JSON block from the text
        match = re.search(r"\{[\s\S]*\}", result.text)
        if match:
            try:
                return json.loads(match.group(0)), result
            except json.JSONDecodeError as e:
                result.error = f"JSON parse error: {e}"
                return None, result
        result.error = "No JSON found in the output"
        return None, result
