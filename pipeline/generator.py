"""
generator.py — orchestrator for multi-agent generation.

    Round 0 (initial): SME -> Pedagogy -> Clarity -> Engagement (sequential, each improves the previous)
    Round >=1 (refine): depends on CONDITION:
        - "no_refine"     : no refinement at all
        - "self_refine"   : all 4 agents refine sequentially without targeting
        - "datr_no_guard" : only the agent owning the weak dimension refines
        - "datr_full"     : DATR + regression guard (revert the update if the dim dropped)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from agents import build_all_agents, get_agent_for_dimension, Agent
from clients import get_client


@dataclass
class GenerationRound:
    """Result of a single round."""
    round_num: int
    lecture: str
    agents_called: list[str]   # ["sme", "pedagogy", ...]
    target_dimension: Optional[str] = None
    rolled_back: bool = False  # if the regression guard reverted the update


@dataclass
class GenerationLog:
    """Full log for generating one lecture."""
    model_key: str
    condition: str
    rounds: list[GenerationRound] = field(default_factory=list)
    final_lecture: str = ""
    seed: Optional[int] = None


class LectureGenerator:
    """
    Generates a lecture through the collaboration of 4 agents (all on the same model).
    """

    def __init__(self, model_key: str, retriever=None):
        self.model_key = model_key
        self.client = get_client(model_key)
        self.agents = build_all_agents(self.client)
        self.retriever = retriever          # TextbookRetriever or None

    def _retrieve_context(self) -> str | None:
        """Fetches the top-k textbook passages to inject into SME (query = the topic).
        For small-context models (ALLaM 4096) k is reduced so the prompt fits the window."""
        if self.retriever is None:
            return None
        from config import LECTURE_TOPIC, RAG_TOP_K
        ctx_tokens = getattr(self.client, "context_tokens", 131072)
        k = 2 if ctx_tokens <= 5000 else (4 if ctx_tokens <= 9000 else RAG_TOP_K)
        try:
            return self.retriever.retrieve(LECTURE_TOPIC, k=k)
        except Exception as e:
            print(f"  [RAG] retrieval failed ({type(e).__name__}: {e}) — continuing without context.")
            return None

    # ─── Round 0: initial draft ────────────────────────

    def initial_draft(self) -> str:
        """
        Round 0: SME writes the foundation (with RAG context), then the other agents refine sequentially.
        """
        textbook_context = self._retrieve_context()
        # SME starts from scratch, grounded in the textbook passages
        result = self.agents["sme"].generate_initial(textbook_context=textbook_context)
        if not result.ok:
            raise RuntimeError(f"SME initial generation failed: {result.error}")
        lecture = result.text

        # Pedagogy -> Clarity -> Engagement (each takes the previous and improves it)
        for name in ["pedagogy", "clarity", "engagement"]:
            r = self.agents[name].revise(prior_lecture=lecture)
            if r.ok:
                lecture = r.text
            # on failure, keep the previous version
        return lecture

    # ─── Round ≥1: refinement ──────────────────────────

    def refine_self(
        self, prior_lecture: str, feedback: dict
    ) -> str:
        """
        self_refine: all 4 agents refine sequentially without targeting.
        """
        lecture = prior_lecture
        for name in ["sme", "pedagogy", "clarity", "engagement"]:
            r = self.agents[name].revise(
                prior_lecture=lecture,
                feedback=feedback,
            )
            if r.ok:
                lecture = r.text
        return lecture

    def refine_datr(
        self,
        prior_lecture: str,
        target_dimensions: list[str],
        feedback: dict,
    ) -> tuple[str, list[str]]:
        """
        DATR: only the agents owning the target_dimensions refine,
        each focusing on its own dimension.

        Returns:
            (revised_lecture, agents_called)
        """
        lecture = prior_lecture
        agents_called = []
        # avoid calling the same agent twice if several dimensions map to it
        seen_agents = set()
        for dim in target_dimensions:
            agent = get_agent_for_dimension(dim, self.agents)
            if agent.name in seen_agents:
                continue
            seen_agents.add(agent.name)
            agents_called.append(agent.name)
            r = agent.revise(
                prior_lecture=lecture,
                feedback=feedback,
                target_dimension=dim,
            )
            if r.ok:
                lecture = r.text
        return lecture, agents_called
