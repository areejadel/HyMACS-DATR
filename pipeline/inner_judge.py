"""
inner_judge.py — GPT-4o scores a lecture on 8 dimensions.

Returns a dict:
    {
        "scores": {dim: float (1-10)},
        "justifications": {dim: str},
        "suggestions":   {dim: str},
        "overall": float,
    }
"""
from __future__ import annotations
import json
import re
from typing import Optional

from clients.openai_client import OpenAIClient
from config import RUBRIC_DIMENSIONS, INNER_JUDGE


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
    "You are a strict, fair evaluator of ML educational material. "
    "You score lectures on 8 dimensions, each from 1 (poor) to 10 (excellent). "
    "You provide concise justifications and concrete suggestions for improvement. "
    "Be calibrated — most lectures should score in the 5-8 range; reserve 9-10 for "
    "genuinely outstanding work and 1-4 for serious deficiencies. Do NOT inflate scores. "
    "Output STRICT JSON only — no markdown, no preamble, no commentary outside the JSON."
)


def _build_user_prompt(lecture: str) -> str:
    rubric_lines = []
    for dim in RUBRIC_DIMENSIONS:
        rubric_lines.append(f"  - {dim}: {_RUBRIC_DESCRIPTIONS[dim]}")
    rubric = "\n".join(rubric_lines)

    schema = {
        "scores": {dim: "<float 1-10>" for dim in RUBRIC_DIMENSIONS},
        "justifications": {dim: "<1-2 sentence explanation>" for dim in RUBRIC_DIMENSIONS},
        "suggestions": {dim: "<concrete actionable fix, or empty string if none>" for dim in RUBRIC_DIMENSIONS},
        "overall": "<float 1-10, weighted average>",
    }
    schema_str = json.dumps(schema, indent=2)

    # Truncate lecture if too long (GPT-4o context = 128k, but we keep it tight)
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


class InnerJudge:
    """GPT-4o evaluator over the 8 rubric dimensions."""

    def __init__(self):
        self.client = OpenAIClient(
            INNER_JUDGE.api_id,
            temperature=INNER_JUDGE.temperature,
            label="GPT-4o (inner judge)",
        )

    def evaluate(self, lecture: str) -> dict:
        """
        Returns:
            {
                "scores": {dim: float},
                "justifications": {dim: str},
                "suggestions": {dim: str},
                "overall": float,
                "raw": str,           # raw response (for debugging)
                "error": Optional[str],
            }
        """
        messages = [
            {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(lecture)},
        ]

        # OpenAI supports native JSON mode — passed through generate()
        # parsing is handled locally via _parse_json
        try:
            result = self.client.generate(
                messages=messages,
                max_tokens=2500,
                response_format={"type": "json_object"},
            )
        except TypeError:
            # client does not support response_format — plain fallback
            result = self.client.generate(messages=messages, max_tokens=2500)

        if not result.ok:
            return {
                "scores": {dim: 0.0 for dim in RUBRIC_DIMENSIONS},
                "justifications": {},
                "suggestions": {},
                "overall": 0.0,
                "raw": "",
                "error": result.error,
            }

        parsed = self._parse_json(result.text)
        parsed["raw"] = result.text
        parsed["error"] = None
        return parsed

    def _parse_json(self, text: str) -> dict:
        """Try to parse JSON. On failure, return zeros."""
        # strip ```json wrappers
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # second attempt: extract the largest JSON object
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    return self._empty_result(error="JSONDecodeError")
            else:
                return self._empty_result(error="No JSON found")

        # ensure every dimension is present
        scores = {dim: float(data.get("scores", {}).get(dim, 0.0)) for dim in RUBRIC_DIMENSIONS}
        justifications = {dim: str(data.get("justifications", {}).get(dim, "")) for dim in RUBRIC_DIMENSIONS}
        suggestions = {dim: str(data.get("suggestions", {}).get(dim, "")) for dim in RUBRIC_DIMENSIONS}

        # compute overall if missing
        try:
            overall = float(data.get("overall", 0.0))
        except (TypeError, ValueError):
            overall = 0.0
        if overall <= 0.0 and any(scores.values()):
            overall = sum(scores.values()) / len(RUBRIC_DIMENSIONS)

        return {
            "scores": scores,
            "justifications": justifications,
            "suggestions": suggestions,
            "overall": overall,
        }

    def _empty_result(self, error: Optional[str] = None) -> dict:
        return {
            "scores": {dim: 0.0 for dim in RUBRIC_DIMENSIONS},
            "justifications": {},
            "suggestions": {},
            "overall": 0.0,
            "error": error,
        }

    def feedback_for_agents(self, evaluation: dict) -> dict:
        """
        Converts the judge's evaluation into a form the agents can use in .revise().
        """
        feedback = {}
        for dim in RUBRIC_DIMENSIONS:
            feedback[dim] = {
                "score":         evaluation["scores"].get(dim, 0.0),
                "justification": evaluation["justifications"].get(dim, ""),
                "suggestions":   evaluation["suggestions"].get(dim, ""),
            }
        return feedback
