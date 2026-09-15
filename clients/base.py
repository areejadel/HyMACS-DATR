"""
base.py — Unified interface for all models

Every client (Together/OpenAI/Claude/ALLaM) inherits from BaseClient and implements .generate.
This guarantees the pipeline does not depend on any specific backend.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GenerationResult:
    """Result of a single model call."""
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text)


class BaseClient(ABC):
    """Unified interface for all models."""

    # Context window (input+output). Hosted models are large; ALLaM is small (4096).
    # Used to budget the prompt automatically so ALLaM outputs are not truncated.
    context_tokens: int = 131072

    def __init__(self, model_id: str, label: str = ""):
        self.model_id = model_id
        self.label = label or model_id

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1500,
        temperature: float = 0.7,
        **kwargs,
    ) -> GenerationResult:
        """
        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
            max_tokens: output limit
            temperature: 0.0-1.0
        Returns:
            GenerationResult
        """
        ...

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.label}>"
