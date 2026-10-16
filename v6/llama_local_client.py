"""
llama_local_client.py — Llama-3-8B-Instruct محلياً (llama.cpp + GGUF 4-bit)
============================================================================
لماذا؟ Llama-3-8B (الأصلي، نافذة 8K) لم يعد متاحاً «بلا خادم» على Together ولا على OpenRouter.
في v5 كان يُخدم عبر Together «Lite» (نسخة مكمّمة 4-bit). نشغّل هنا نفس النموذج بنسخة
GGUF Q4_K_M محلياً على جهازك (نفس أسلوب ALLaM)، ونذكر ذلك في الورقة.

التنزيل مرة واحدة:   python download_llama3_gguf.py
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

from clients.base import BaseClient, GenerationResult

V6_DIR = Path(__file__).resolve().parent
GGUF_PATH = Path(os.getenv("LLAMA3_8B_GGUF_PATH", str(V6_DIR / "models" / "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf")))

_model = None
_lock = threading.Lock()
_load_lock = threading.Lock()


def _ensure_loaded():
    global _model
    if _model is not None:
        return _model
    with _load_lock:
        if _model is None:
            if not GGUF_PATH.exists():
                raise FileNotFoundError(f"ملف GGUF غير موجود: {GGUF_PATH}\n  شغّلي: python download_llama3_gguf.py")
            from llama_cpp import Llama
            print(f"[Llama-3-8B] تحميل {GGUF_PATH.name} ...")
            _model = Llama(model_path=str(GGUF_PATH), n_ctx=8192, n_gpu_layers=-1,
                           n_threads=os.cpu_count() or 8, verbose=False, seed=-1)
            print("[Llama-3-8B] جاهز ✓")
    return _model


def release():
    """تحرير الذاكرة (لتشغيل نموذج محلي آخر بعده في نفس العملية)."""
    global _model
    _model = None
    import gc
    gc.collect()


class LlamaLocalClient(BaseClient):
    context_tokens = 8192

    def __init__(self, label: str = "Llama-3-8B (local Q4_K_M)"):
        super().__init__("meta-llama/Meta-Llama-3-8B-Instruct@GGUF-Q4_K_M", label)

    def generate(self, messages, max_tokens: int = 1500, temperature: float = 0.7, **kwargs) -> GenerationResult:
        try:
            m = _ensure_loaded()
            with _lock:
                resp = m.create_chat_completion(messages=messages, max_tokens=max_tokens,
                                                temperature=temperature, top_p=kwargs.pop("top_p", 0.9),
                                                stream=False)
            text = (resp["choices"][0]["message"]["content"] or "").strip()
            u = resp.get("usage", {})
            if not text:
                return GenerationResult(text="", model=self.model_id, error="Empty response")
            return GenerationResult(text=text, model=self.model_id, prompt_tokens=u.get("prompt_tokens", 0),
                                    completion_tokens=u.get("completion_tokens", 0))
        except Exception as e:
            return GenerationResult(text="", model=self.model_id, error=f"{type(e).__name__}: {e}")
