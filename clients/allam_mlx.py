"""
allam_mlx.py — ALLaM-7B via MLX-LM (Apple Silicon native)
==========================================================
The cleaner alternative on Apple Silicon when GGUF fails.

MLX = Apple's official ML framework, optimized for Apple Silicon (M1/M2/M3/M4/M5).
Converts the model automatically from HuggingFace safetensors -> MLX format on disk.
Supports 4-bit quantization natively.

Memory: ~5-6GB RAM (4-bit quantized).
Speed: ~30-50 token/sec on an M-series chip.

Install:
    pip install mlx-lm

Selected automatically when ALLAM_BACKEND=mlx in .env.
"""
from __future__ import annotations
import threading

from clients.base import BaseClient, GenerationResult
from config import ALLAM_MLX_REPO


_model = None
_tokenizer = None
_lock = threading.Lock()
_load_lock = threading.Lock()


def _ensure_loaded():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    with _load_lock:
        if _model is not None:
            return _model, _tokenizer

        try:
            from mlx_lm import load
        except ImportError:
            raise ImportError(
                "mlx-lm is not installed.\n"
                "  pip install mlx-lm\n"
                "  (works only on Apple Silicon — M1/M2/M3/M4/M5)"
            )

        print(f"[ALLaM-MLX] loading {ALLAM_MLX_REPO}...")
        print("  (the first run takes 3-10 minutes to download from HuggingFace)")
        _model, _tokenizer = load(ALLAM_MLX_REPO)
        print("[ALLaM-MLX] ready")
        return _model, _tokenizer


def _format_chat_prompt(messages: list[dict], tokenizer) -> str:
    """Apply the tokenizer's chat template."""
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            pass
    # fallback
    parts = []
    for m in messages:
        role = m["role"].upper()
        parts.append(f"[{role}]\n{m['content']}\n")
    parts.append("[ASSISTANT]\n")
    return "\n".join(parts)


class AllamMlxClient(BaseClient):
    """ALLaM-7B via MLX-LM on Apple Silicon."""

    context_tokens = 4096   # ALLaM window (input+output)

    def __init__(self, label: str = "ALLaM-7B (MLX)"):
        super().__init__("ALLaM-AI/ALLaM-7B-Instruct-preview", label)

    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1500,
        temperature: float = 0.7,
        **kwargs,
    ) -> GenerationResult:
        try:
            from mlx_lm import generate as mlx_generate
            model, tokenizer = _ensure_loaded()

            prompt = _format_chat_prompt(messages, tokenizer)
            n_input = len(tokenizer.encode(prompt))

            # overflow guard (4096 context)
            if n_input + max_tokens > 4000:
                max_tokens = max(100, 4000 - n_input)

            with _lock:
                # MLX generate signature: (model, tokenizer, prompt, max_tokens, ...)
                # in recent versions temperature is passed via a sampler
                try:
                    from mlx_lm.sample_utils import make_sampler
                    sampler = make_sampler(temp=temperature)
                    text = mlx_generate(
                        model, tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        sampler=sampler,
                        verbose=False,
                    )
                except ImportError:
                    # fallback for older versions
                    text = mlx_generate(
                        model, tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temp=temperature,
                        verbose=False,
                    )

            text = (text or "").strip()
            return GenerationResult(
                text=text,
                model=self.model_id,
                prompt_tokens=n_input,
                completion_tokens=len(tokenizer.encode(text)) if text else 0,
            )
        except Exception as e:
            return GenerationResult(
                text="",
                model=self.model_id,
                error=f"{type(e).__name__}: {e}",
            )
