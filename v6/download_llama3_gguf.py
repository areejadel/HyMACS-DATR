"""
download_llama3_gguf.py — تنزيل Llama-3-8B-Instruct (GGUF Q4_K_M، ~4.9GB) مرة واحدة
====================================================================================
    python download_llama3_gguf.py
يحفظ في  v6_تقوية/models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf
"""
from __future__ import annotations

import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download, list_repo_files

DEST = Path(__file__).resolve().parent / "models" / "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
REPOS = ["bartowski/Meta-Llama-3-8B-Instruct-GGUF", "QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
         "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF"]


def main():
    if DEST.exists():
        print(f"✓ موجود مسبقاً: {DEST}")
        return
    DEST.parent.mkdir(parents=True, exist_ok=True)
    for repo in REPOS:
        try:
            files = [f for f in list_repo_files(repo) if f.lower().endswith(".gguf") and "q4_k_m" in f.lower()]
            if not files:
                continue
            print(f"تنزيل {files[0]} من {repo} ...")
            p = hf_hub_download(repo, files[0])
            shutil.copy(p, DEST)
            print(f"✓ حُفظ: {DEST}")
            return
        except Exception as e:
            print(f"  تعذّر من {repo}: {type(e).__name__}: {str(e)[:150]}")
    raise SystemExit("✗ لم يُنزَّل النموذج — أرسلي الرسالة أعلاه.")


if __name__ == "__main__":
    main()
