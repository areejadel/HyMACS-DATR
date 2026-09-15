"""
external_judge.py — Claude Sonnet for external validation.

Called once at the end (after convergence) for an independent evaluation:
    - Claude is from a different family than the inner judge (OpenAI)
    - breaks self-preference bias (Panickssery 2024)
    - GPT-4o vs Claude scores are compared to compute Cohen's kappa + Spearman rho

Same schema (8 dimensions, 1-10, JSON output).
"""
from __future__ import annotations
import json
import re
from typing import Optional

from clients.claude_client import ClaudeClient
from config import RUBRIC_DIMENSIONS, EXTERNAL_JUDGE


_RUBRIC_DESCRIPTIONS = {
    "academic_accuracy":         "Are definitions, equations, and notation correct?",
    "pedagogical_effectiveness": "Does the lecture teach effectively (scaffolding, examples, prerequisites)?",
    "clarity_organization":      "Is the writing clear and the structure logical?",
    "practical_relevance":       "Are concepts connected to real ML practice?",
    "completeness":              "Are all important sub-topics covered (incl. variants, limitations)?",
    "engagement_potential":      "Does the lecture motivate the reader (hooks, analogies, tension)?",
    "technical_quality":         "Is formatting precise (consistent notation, code blocks, tables)?",
    "innovation":                "Are there fresh angles or non-trivial cross-domain connections?",
}


_JUDGE_SYSTEM_PROMPT = (
    "You are an independent external evaluator of ML educational material. "
    "You have not seen any prior evaluation of this lecture. "
    "Score on 8 dimensions, each from 1 (poor) to 10 (excellent). "
    "Be calibrated and honest — most lectures should score 5-8; reserve 9-10 for "
    "outstanding work and 1-4 for serious deficiencies. Do NOT inflate scores. "
    "Your output is the FINAL source of truth — be rigorous. "
    "Output STRICT JSON only — no markdown fences, no preamble."
)


def _build_user_prompt(lecture: str) -> str:
    rubric_lines = []
    for dim in RUBRIC_DIMENSIONS:
        rubric_lines.append(f"  - {dim}: {_RUBRIC_DESCRIPTIONS[dim]}")
    rubric = "\n".join(rubric_lines)

    schema = {
        "scores": {dim: "<float 1-10>" for dim in RUBRIC_DIMENSIONS},
        "justifications": {dim: "<1-2 sentences>" for dim in RUBRIC_DIMENSIONS},
        "overall": "<float 1-10>",
    }
    schema_str = json.dumps(schema, indent=2)

    max_chars = 25000
    truncated = lecture
    if len(truncated) > max_chars:
        truncated = truncated[:max_chars] + "\n[...truncated...]"

    return (
        "Evaluate the following lecture on these 8 dimensions:\n"
        f"{rubric}\n\n"
        "Output ONLY valid JSON matching this schema:\n"
        f"{schema_str}\n\n"
        "── LECTURE ──\n"
        f"{truncated}\n"
        "── END ──"
    )


class ExternalJudge:
    """Claude Sonnet evaluator, fully separate from the inner judge."""

    def __init__(self):
        self.client = ClaudeClient(
            EXTERNAL_JUDGE.api_id,
            temperature=EXTERNAL_JUDGE.temperature,
            label="Claude Sonnet (external judge)",
        )

    def evaluate(self, lecture: str) -> dict:
        messages = [
            {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(lecture)},
        ]

        # Anthropic has no native JSON mode — rely on the prompt + local _parse_json
        result = self.client.generate(messages=messages, max_tokens=2500)

        if not result.ok:
            return self._empty_result(error=result.error)

        parsed = self._parse_json(result.text)
        parsed["raw"] = result.text
        parsed["error"] = None
        return parsed

    def _parse_json(self, text: str) -> dict:
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    return self._empty_result(error="JSONDecodeError")
            else:
                return self._empty_result(error="No JSON found")

        scores = {dim: float(data.get("scores", {}).get(dim, 0.0)) for dim in RUBRIC_DIMENSIONS}
        justifications = {dim: str(data.get("justifications", {}).get(dim, "")) for dim in RUBRIC_DIMENSIONS}

        try:
            overall = float(data.get("overall", 0.0))
        except (TypeError, ValueError):
            overall = 0.0
        if overall <= 0.0 and any(scores.values()):
            overall = sum(scores.values()) / len(RUBRIC_DIMENSIONS)

        return {
            "scores": scores,
            "justifications": justifications,
            "overall": overall,
        }

    def _empty_result(self, error: Optional[str] = None) -> dict:
        return {
            "scores": {dim: 0.0 for dim in RUBRIC_DIMENSIONS},
            "justifications": {},
            "overall": 0.0,
            "raw": "",
            "error": error,
        }
