"""
clients/ — unified model interfaces

Every client implements the same interface: .generate(messages, **kwargs) -> str
so the pipeline does not care which backend actually generates (Together/OpenAI/Claude/ALLaM).
"""
from clients.base import BaseClient
from clients.together_client import TogetherClient
from clients.openai_client import OpenAIClient
from clients.claude_client import ClaudeClient

__all__ = ["BaseClient", "TogetherClient", "OpenAIClient", "ClaudeClient", "get_client"]


def get_client(model_key: str):
    """Factory: returns the right client for a model key in config.GENERATORS."""
    from config import GENERATORS, INNER_JUDGE, EXTERNAL_JUDGE

    # Generators
    if model_key in GENERATORS:
        spec = GENERATORS[model_key]
        if spec.backend == "together":
            client = TogetherClient(spec.api_id, label=spec.label)
        elif spec.backend == "local":
            from clients.allam_local import AllamLocalClient
            client = AllamLocalClient(label=spec.label)
        elif spec.backend == "mlx":
            from clients.allam_mlx import AllamMlxClient
            client = AllamMlxClient(label=spec.label)
        elif spec.backend == "cuda":
            from clients.allam_cuda import AllamCudaClient
            client = AllamCudaClient(label=spec.label)
        else:
            raise ValueError(f"Unknown backend for {model_key}: {spec.backend}")
        # correct context window per model (used for prompt budgeting and the Presenter)
        client.context_tokens = spec.context_tokens
        return client

    # Judges
    if model_key == "inner_judge":
        return OpenAIClient(INNER_JUDGE.api_id, temperature=INNER_JUDGE.temperature, label="GPT-4o (inner judge)")
    if model_key == "external_judge":
        return ClaudeClient(EXTERNAL_JUDGE.api_id, temperature=EXTERNAL_JUDGE.temperature, label="Claude (external judge)")

    raise ValueError(f"Unknown model_key: {model_key}")
