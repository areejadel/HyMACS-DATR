"""
judge_panel.py — external judge panel
================================================
Instead of a single external judge, we use a panel of 3 cross-family judges
and take the median for each dimension. This reduces single-judge bias and
raises reliability (Verga et al. 2024, "Replacing Judges with Juries").

Every panel judge is from a family different from all six generators -> breaks
self-preference (Panickssery et al. 2024). Each judge's score is kept separately
to compute panel agreement (Krippendorff alpha) and the self-preference matrix later.

Output:
    {
      "per_judge": { "judge_claude": {scores, overall, error}, ... },
      "median_scores": {dim: float},   # median across judges per dimension
      "overall": float,                # median of the overalls
      "n_ok": int,                     # how many judges succeeded
    }
"""
from __future__ import annotations
import json
import re
from statistics import median
from typing import Optional

from config import RUBRIC_DIMENSIONS, EXTERNAL_PANEL, TEMPERATURE_EVAL, JudgeSpec


_RUBRIC_DESCRIPTIONS = {
    "academic_accuracy":         "Are definitions, equations, and notation correct?",
    "pedagogical_effectiveness": "Does the lecture teach effectively (scaffolding, examples, prerequisites)?",
    "clarity_organization":      "Is the writing clear and the structure logical?",
    "practical_relevance":       "Are concepts connected to real practice in the field?",
    "completeness":              "Are all important sub-topics covered (incl. variants, limitations)?",
    "engagement_potential":      "Does the lecture motivate the reader (hooks, analogies, tension)?",
    "technical_quality":         "Is formatting precise (consistent notation, code blocks, tables)?",
    "innovation":                "Are there fresh angles or non-trivial cross-domain connections?",
}

_JUDGE_SYSTEM_PROMPT = (
    "You are an independent external evaluator of university-level educational material. "
    "You have not seen any prior evaluation of this lecture. "
    "Score on 8 dimensions, each from 1 (poor) to 10 (excellent). "
    "Be calibrated and honest — most lectures should score 5-8; reserve 9-10 for "
    "outstanding work and 1-4 for serious deficiencies. Do NOT inflate scores. "
    "Output STRICT JSON only — no markdown fences, no preamble."
)


def _build_user_prompt(lecture: str) -> str:
    rubric = "\n".join(f"  - {d}: {_RUBRIC_DESCRIPTIONS[d]}" for d in RUBRIC_DIMENSIONS)
    schema = {
        "scores": {d: "<float 1-10>" for d in RUBRIC_DIMENSIONS},
        "justifications": {d: "<1-2 sentences>" for d in RUBRIC_DIMENSIONS},
        "overall": "<float 1-10>",
    }
    truncated = lecture if len(lecture) <= 25000 else lecture[:25000] + "\n[...truncated...]"
    return (
        "Evaluate the following lecture on these 8 dimensions:\n"
        f"{rubric}\n\n"
        "Output ONLY valid JSON matching this schema:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "── LECTURE ──\n"
        f"{truncated}\n"
        "── END ──"
    )


def _make_client(spec: JudgeSpec):
    """Builds the appropriate client for a panel judge based on its backend."""
    if spec.backend == "anthropic":
        from clients.claude_client import ClaudeClient
        return ClaudeClient(spec.api_id, temperature=spec.temperature, label=f"{spec.role} ({spec.api_id})")
    if spec.backend == "openai":
        from clients.openai_client import OpenAIClient
        return OpenAIClient(spec.api_id, temperature=spec.temperature, label=f"{spec.role} ({spec.api_id})")
    if spec.backend == "together":
        from clients.together_client import TogetherClient
        return TogetherClient(spec.api_id, label=f"{spec.role} ({spec.api_id})")
    raise ValueError(f"Unknown backend for judge: {spec.backend}")


def _parse_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*", "", (text or "").strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if not m:
            return {"scores": {d: 0.0 for d in RUBRIC_DIMENSIONS}, "justifications": {}, "overall": 0.0,
                    "error": "No JSON found"}
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"scores": {d: 0.0 for d in RUBRIC_DIMENSIONS}, "justifications": {}, "overall": 0.0,
                    "error": "JSONDecodeError"}
    scores = {d: float(data.get("scores", {}).get(d, 0.0) or 0.0) for d in RUBRIC_DIMENSIONS}
    justifs = {d: str(data.get("justifications", {}).get(d, "")) for d in RUBRIC_DIMENSIONS}
    try:
        overall = float(data.get("overall", 0.0) or 0.0)
    except (TypeError, ValueError):
        overall = 0.0
    if overall <= 0.0 and any(scores.values()):
        overall = sum(scores.values()) / len(RUBRIC_DIMENSIONS)
    return {"scores": scores, "justifications": justifs, "overall": overall, "error": None}


class _SingleJudge:
    def __init__(self, spec: JudgeSpec):
        self.spec = spec
        self.client = _make_client(spec)

    def evaluate(self, lecture: str) -> dict:
        messages = [
            {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(lecture)},
        ]
        # Only OpenAI supports native JSON mode; Anthropic/Together rely on
        # the strict prompt + _parse_json (strips ```json fences and extracts {...}).
        if self.spec.backend == "openai":
            result = self.client.generate(messages=messages, max_tokens=2500,
                                          response_format={"type": "json_object"})
        else:
            result = self.client.generate(messages=messages, max_tokens=2500)
        if not getattr(result, "ok", False):
            return {"scores": {d: 0.0 for d in RUBRIC_DIMENSIONS}, "justifications": {},
                    "overall": 0.0, "error": getattr(result, "error", "no result"), "raw": ""}
        parsed = _parse_json(result.text)
        parsed["raw"] = result.text
        return parsed


class JudgePanel:
    """External judge panel -> median per dimension."""

    def __init__(self, specs: Optional[list[JudgeSpec]] = None):
        self.specs = specs if specs is not None else EXTERNAL_PANEL
        self.judges = [_SingleJudge(s) for s in self.specs]

    def evaluate(self, lecture: str) -> dict:
        per_judge: dict[str, dict] = {}
        for judge in self.judges:
            per_judge[judge.spec.role] = judge.evaluate(lecture)

        ok = [r for r in per_judge.values() if not r.get("error")]
        n_ok = len(ok)

        median_scores: dict[str, float] = {}
        for dim in RUBRIC_DIMENSIONS:
            vals = [r["scores"][dim] for r in ok if r["scores"].get(dim, 0.0) > 0]
            median_scores[dim] = round(float(median(vals)), 3) if vals else 0.0

        overalls = [r["overall"] for r in ok if r.get("overall", 0.0) > 0]
        overall = round(float(median(overalls)), 3) if overalls else 0.0

        return {
            "per_judge": per_judge,
            "median_scores": median_scores,
            "overall": overall,
            "n_ok": n_ok,
            "error": None if n_ok > 0 else "all panel judges failed",
        }


if __name__ == "__main__":
    panel = JudgePanel()
    print("Panel judges:", [s.role for s in panel.specs])
