"""
allam_local.py — ALLaM-7B-Instruct-preview on Apple Silicon (Plan A)
==============================================================
Uses llama-cpp-python + GGUF Q4_K_M on Apple Metal.
Memory: ~5GB RAM. Speed: ~25-40 token/sec on an M-series chip.

Note: context window = 4096 tokens (input + output together).
"""
from __future__ import annotations
import os
import threading
from pathlib import Path

from clients.base import BaseClient, GenerationResult
from config import ALLAM_GGUF_PATH


# Singleton model — lazy loaded
_model = None
_lock = threading.Lock()
_load_lock = threading.Lock()


def _ensure_loaded():
    """Load the model only once (singleton)."""
    global _model
    if _model is not None:
        return _model
    with _load_lock:
        if _model is not None:
            return _model

        gguf_path = Path(ALLAM_GGUF_PATH)
        if not gguf_path.exists():
            raise FileNotFoundError(
                f"GGUF file not found: {gguf_path}\n"
                "  run first: python download_allam_gguf.py"
            )

        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python is not installed.\n"
                "  pip install llama-cpp-python\n"
                "  (on Mac it builds automatically with Metal support)"
            )

        print(f"[ALLaM] loading model from {gguf_path}...")
        _model = Llama(
            model_path=str(gguf_path),
            n_ctx=4096,           # ALLaM context window
            n_gpu_layers=-1,      # all layers on the Apple Metal GPU
            n_threads=os.cpu_count() or 8,
            verbose=False,
            seed=-1,              # random
        )
        print(f"[ALLaM] ready")
        return _model


class AllamLocalClient(BaseClient):
    """ALLaM-7B via llama-cpp-python on Apple Metal."""

    context_tokens = 4096   # ALLaM window (input+output), matches n_ctx

    def __init__(self, label: str = "ALLaM-7B (local)"):
        super().__init__("ALLaM-AI/ALLaM-7B-Instruct-preview", label)
        # loaded lazily in .generate to avoid import-time delay

    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1500,
        temperature: float = 0.7,
        **kwargs,
    ) -> GenerationResult:
        try:
            model = _ensure_loaded()

            # remaining tokens. context = 4096
            # input length is computed by llama.cpp itself;
            # we request max_tokens bounded by what remains
            top_p = kwargs.pop("top_p", 0.9)

            with _lock:   # serialize calls (single model, opened once)
                resp = model.create_chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stream=False,
                )

            text = resp["choices"][0]["message"]["content"] or ""
            usage = resp.get("usage", {})
            return GenerationResult(
                text=text.strip(),
                model=self.model_id,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )
        except Exception as e:
            return GenerationResult(
                text="",
                model=self.model_id,
                error=f"{type(e).__name__}: {e}",
            )
