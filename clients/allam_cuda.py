"""
allam_cuda.py — ALLaM-7B on an NVIDIA GPU (Plan B)
=================================================
For running on Lambda Labs / vast.ai / RunPod when Plan A fails.
Uses transformers + fp16 + CUDA.

Note: context window = 4096 tokens. An overflow guard is applied.
"""
from __future__ import annotations
import threading

from clients.base import BaseClient, GenerationResult


_MAX_CTX = 4096
_OVERFLOW_RESERVE = 64   # safety margin for EOS and headers

_model = None
_tokenizer = None
_lock = threading.Lock()
_load_lock = threading.Lock()


def _ensure_loaded():
    """Load ALLaM once on the GPU."""
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    with _load_lock:
        if _model is not None:
            return _model, _tokenizer

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
        except ImportError:
            raise ImportError(
                "transformers/torch are not installed.\n"
                "  pip install -r requirements_cuda.txt"
            )

        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is not available. This client requires an NVIDIA GPU.\n"
                "  to run on Mac: use ALLAM_BACKEND=local"
            )

        model_id = "ALLaM-AI/ALLaM-7B-Instruct-preview"
        print(f"[ALLaM-CUDA] loading {model_id}...")
        _tokenizer = AutoTokenizer.from_pretrained(model_id)
        _model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True,
        )
        _model.eval()
        device = next(_model.parameters()).device
        print(f"[ALLaM-CUDA] ready on {device}")
        return _model, _tokenizer


class AllamCudaClient(BaseClient):
    """ALLaM-7B via transformers + CUDA."""

    context_tokens = 4096   # ALLaM window (input+output)

    def __init__(self, label: str = "ALLaM-7B (CUDA)"):
        super().__init__("ALLaM-AI/ALLaM-7B-Instruct-preview", label)

    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 1500,
        temperature: float = 0.7,
        **kwargs,
    ) -> GenerationResult:
        try:
            import torch
            model, tokenizer = _ensure_loaded()

            top_p = kwargs.pop("top_p", 0.9)
            do_sample = temperature > 0.0

            # apply the chat template
            prompt = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            n_input = len(tokenizer.encode(prompt))

            # overflow guard
            available = _MAX_CTX - n_input - _OVERFLOW_RESERVE
            if available <= 0:
                return GenerationResult(
                    text="",
                    model=self.model_id,
                    error=f"Context overflow: input={n_input}, ctx={_MAX_CTX}",
                )
            actual_max = min(max_tokens, available)

            with _lock:   # serialize GPU calls
                inputs = tokenizer([prompt], return_tensors="pt")
                # vocab clamp (safety)
                vocab_size = model.config.vocab_size
                ids = inputs["input_ids"]
                if (ids >= vocab_size).any() or (ids < 0).any():
                    inputs["input_ids"] = ids.clamp(0, vocab_size - 1)

                device = next(model.parameters()).device
                inputs = {k: v.to(device) for k, v in inputs.items()}

                with torch.no_grad():
                    out = model.generate(
                        **inputs,
                        max_new_tokens=actual_max,
                        do_sample=do_sample,
                        temperature=temperature if do_sample else 1.0,
                        top_p=top_p,
                        pad_token_id=tokenizer.eos_token_id,
                    )
                new_tokens = out[0][inputs["input_ids"].shape[1]:]
                text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

            return GenerationResult(
                text=text,
                model=self.model_id,
                prompt_tokens=n_input,
                completion_tokens=len(new_tokens),
            )

        except Exception as e:
            return GenerationResult(
                text="",
                model=self.model_id,
                error=f"{type(e).__name__}: {e}",
            )
