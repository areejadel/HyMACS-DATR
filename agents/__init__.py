"""
agents/ — the 4 specialized agents in the HyMACS architecture.

Each agent covers a subset of the 8 rubric dimensions:
    - SME        : academic_accuracy, practical_relevance, completeness
    - Pedagogy   : pedagogical_effectiveness
    - Clarity    : clarity_organization, technical_quality
    - Engagement : engagement_potential, innovation

Usage:
    from agents import SMEAgent, PedagogyAgent, ClarityAgent, EngagementAgent
    sme = SMEAgent(client)
    output = sme.contribute(topic, prior_lecture=None)
"""
from agents.base import Agent
from agents.sme import SMEAgent
from agents.pedagogy import PedagogyAgent
from agents.clarity import ClarityAgent
from agents.engagement import EngagementAgent
from agents.presenter import PresenterAgent

__all__ = [
    "Agent",
    "SMEAgent",
    "PedagogyAgent",
    "ClarityAgent",
    "EngagementAgent",
    "PresenterAgent",
    "get_agent_for_dimension",
    "build_all_agents",
]


def build_all_agents(client) -> dict[str, Agent]:
    """Returns a dict: agent_name -> Agent instance, all on the same client."""
    return {
        "sme":        SMEAgent(client),
        "pedagogy":   PedagogyAgent(client),
        "clarity":    ClarityAgent(client),
        "engagement": EngagementAgent(client),
    }


def get_agent_for_dimension(dim: str, agents: dict[str, Agent]) -> Agent:
    """Returns the agent responsible for a given dimension (per DIMENSION_TO_AGENT)."""
    from config import DIMENSION_TO_AGENT
    agent_name = DIMENSION_TO_AGENT.get(dim)
    if agent_name is None:
        raise ValueError(f"No agent for dimension: {dim}")
    return agents[agent_name]
