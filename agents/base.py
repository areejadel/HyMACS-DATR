"""
base.py — Agent abstract class
==============================
Every agent in the system:
    1. takes a client (any generator: Llama / Qwen / DeepSeek / ALLaM)
    2. has a role + focus_dimensions
    3. produces a contribution or a revision
"""
from __future__ import annotations
from abc import ABC
from typing import Optional

from clients.base import BaseClient, GenerationResult
from config import LECTURE_TOPIC, LECTURE_REFERENCE, LECTURE_TARGET_LENGTH, TEMPERATURE_GEN


class Agent(ABC):
    """Shared base for every agent."""

    name: str = ""              # "sme" / "pedagogy" / ...
    role: str = ""              # human-readable
    focus_dimensions: list[str] = []
    system_prompt: str = ""
    uses_rag: bool = False      # SME only = True (receives textbook context)

    def __init__(self, client: BaseClient):
        self.client = client

    def __repr__(self):
        return f"<{self.__class__.__name__} via {self.client.label}>"

    # ─── Context budgeting (prevents exceeding small windows, e.g. ALLaM = 4096) ──
    def _budget(self) -> dict:
        """
        Sets output limits and input truncation based on the model's context window.
        Small-window models (e.g. ALLaM, 4096) get smaller inputs and outputs so that
        (input + output) does not exceed the window and truncate the lecture.
        Estimate: 1 token ≈ 4 characters; a safety margin is kept.
        """
        ctx = getattr(self.client, "context_tokens", 131072)
        if ctx <= 5000:    # ALLaM (4096)
            return {"small": True,  "max_out": 2200, "prior_chars": 2400, "rag_chars": 1100}
        if ctx <= 9000:    # Llama-3-8B-Lite (8192) and similar — medium window
            return {"small": True,  "max_out": 3500, "prior_chars": 4500, "rag_chars": 3500}
        return {"small": False, "max_out": 4500, "prior_chars": 8000, "rag_chars": 6500}

    # ─── Generation modes ──────────────────────────────

    def generate_initial(
        self,
        topic: str = LECTURE_TOPIC,
        reference: str = LECTURE_REFERENCE,
        target_length: int = LECTURE_TARGET_LENGTH,
        textbook_context: str | None = None,
    ) -> GenerationResult:
        """
        Round 0: the first contribution — there is no prior lecture yet.
        Each agent writes from its own perspective. SME receives textbook context (RAG).
        """
        b = self._budget()
        ctx = textbook_context if self.uses_rag else None
        if ctx and len(ctx) > b["rag_chars"]:
            ctx = ctx[:b["rag_chars"]] + "\n[...]"
        user_msg = self._build_initial_user_prompt(topic, reference, target_length, ctx)
        return self._call(user_msg, max_tokens=b["max_out"])

    def revise(
        self,
        prior_lecture: str,
        topic: str = LECTURE_TOPIC,
        feedback: Optional[dict] = None,
        target_dimension: Optional[str] = None,
    ) -> GenerationResult:
        """
        Round >=1: improves the prior lecture based on feedback.

        Args:
            prior_lecture: the lecture text from the previous round
            feedback: dict from inner_judge: {dimension: {score, justification}}
            target_dimension: under DATR, the specific dimension to target
        """
        b = self._budget()
        user_msg = self._build_revision_user_prompt(
            prior_lecture, topic, feedback, target_dimension, max_prior_chars=b["prior_chars"]
        )
        return self._call(user_msg, max_tokens=b["max_out"])

    # ─── Internal helpers ──────────────────────────────

    def _call(self, user_content: str, max_tokens: int) -> GenerationResult:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user",   "content": user_content},
        ]
        return self.client.generate(
            messages=messages,
            max_tokens=max_tokens,
            temperature=TEMPERATURE_GEN,
        )

    # ─── User-prompt builders (structured XML format) ──────────────────
    # Clear tags + RAG injection + precise instructions.

    def _build_initial_user_prompt(
        self, topic: str, reference: str, target_length: int,
        textbook_context: str | None = None,
    ) -> str:
        ctx = ""
        if textbook_context:
            ctx = (
                "<textbook_context>\n"
                f"{textbook_context}\n"
                "</textbook_context>\n"
                "Use the context above as your PRIMARY source and cite passages inline "
                "as [1], [2], … matching their numbers. Prefer it over memory; if it is "
                "insufficient for a point, say what is missing rather than inventing it.\n\n"
            )
        return (
            "<task>\nWrite a complete, university-level lecture on the topic below, "
            f"from your perspective as {self.role}.\n</task>\n\n"
            f"<topic>{topic}</topic>\n"
            f"<reference>{reference}</reference>\n"
            f"<target_length>~{target_length} characters (≈ a 30-minute lecture)</target_length>\n"
            f"<focus>Prioritize the rubric dimensions you own: {', '.join(self.focus_dimensions)}.</focus>\n\n"
            f"{ctx}"
            "<language>English only. Do not use Arabic, Chinese, or any other language.</language>\n\n"
            "Follow your <method> and meet your <quality_bar>. "
            "Output the lecture body only — no meta-commentary, no '# Lecture' header."
        )

    def _build_revision_user_prompt(
        self,
        prior_lecture: str,
        topic: str,
        feedback: Optional[dict],
        target_dimension: Optional[str],
        max_prior_chars: int = 8000,
    ) -> str:
        prior = prior_lecture
        if len(prior) > max_prior_chars:
            prior = prior[:max_prior_chars] + "\n[...truncated...]"

        scope = ""
        if target_dimension:
            scope = (
                f"<scope>Improve ONLY '{target_dimension}'. Preserve verbatim any part that is "
                "already strong on other dimensions — do not rewrite it.</scope>\n\n"
            )

        fb = ""
        if feedback:
            relevant = [target_dimension] if target_dimension else self.focus_dimensions
            lines = []
            for dim in relevant:
                if dim in feedback:
                    f = feedback[dim]
                    line = f"- {dim}: score={f.get('score', '?')}/10 — {f.get('justification', '')}".strip()
                    lines.append(line)
                    if f.get("suggestions"):
                        lines.append(f"  fix: {f['suggestions']}")
            if lines:
                fb = "<evaluator_feedback>\n" + "\n".join(lines) + "\n</evaluator_feedback>\n\n"

        return (
            f"<task>Revise the draft below from your perspective as {self.role}, raising its "
            "quality on your owned dimensions.</task>\n\n"
            f"<topic>{topic}</topic>\n\n"
            f"{scope}{fb}"
            f"<draft>\n{prior}\n</draft>\n\n"
            "<language>English only.</language>\n\n"
            "Apply your <method>, meet your <quality_bar>, then output the full revised "
            "lecture body only — no meta-commentary, no preamble."
        )
