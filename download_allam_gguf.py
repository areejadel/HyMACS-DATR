"""
download_allam_gguf.py — download ALLaM-7B GGUF Q4_K_M
====================================================
Downloads from the official repo:
    Omartificial-Intelligence-Space/ALLaM-7B-Instruct-preview-Q4_K_M-GGUF
File size: ~4.26 GB (fits a 16GB-RAM Mac).

The repo and filename come from config.py (or .env):
    ALLAM_GGUF_REPO
    ALLAM_GGUF_FILENAME
    ALLAM_GGUF_PATH   (save location)

Run:
    python download_allam_gguf.py
    python download_allam_gguf.py --search   # dynamic search via HfApi
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

from config import (
    ALLAM_GGUF_PATH,
    ALLAM_GGUF_REPO,
    ALLAM_GGUF_FILENAME,
)


def search_alternative_repos(quant: str = "Q4_K_M") -> list[dict]:
    """Dynamically search HuggingFace for alternative ALLaM GGUF repos."""
    api = HfApi()
    candidates = {}

    for q in ["ALLaM-7B GGUF", "ALLaM 7B Q4", "ALLaM GGUF"]:
        try:
            for m in api.list_models(search=q, limit=20):
                if "gguf" not in m.id.lower() or "allam" not in m.id.lower():
                    continue
                if m.id in candidates:
                    continue
                candidates[m.id] = m
        except Exception as e:
            print(f"  [!] search '{q}' failed: {e}")

    results = []
    for repo_id in candidates:
        try:
            files = api.list_repo_files(repo_id)
            gguf = [f for f in files if f.lower().endswith(".gguf")]
            preferred = [f for f in gguf if quant.lower() in f.lower()]
            chosen = preferred[0] if preferred else (gguf[0] if gguf else None)
            if chosen:
                results.append({"repo_id": repo_id, "filename": chosen})
        except Exception:
            pass
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", action="store_true",
                        help="dynamic search instead of the default repo")
    parser.add_argument("--repo", default=None, help="specific repo_id")
    parser.add_argument("--filename", default=None, help="GGUF filename")
    args = parser.parse_args()

    target = Path(ALLAM_GGUF_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        size_mb = target.stat().st_size / (1024 * 1024)
        print(f"[ok] file already present: {target} ({size_mb:.0f} MB)")
        return

    # Build the candidate list
    if args.repo and args.filename:
        repos = [{"repo_id": args.repo, "filename": args.filename}]
    elif args.search:
        print("Dynamic search for ALLaM GGUF repos on HuggingFace...\n")
        repos = search_alternative_repos()
        if not repos:
            print("[!] No repo found. Try without --search to use the default.")
            sys.exit(1)
    else:
        # The documented default (verified to exist)
        repos = [{"repo_id": ALLAM_GGUF_REPO, "filename": ALLAM_GGUF_FILENAME}]

    print(f"Target: {target}")
    print(f"Candidates ({len(repos)}):")
    for i, r in enumerate(repos, 1):
        print(f"  [{i}] {r['repo_id']} -> {r['filename']}")
    print()

    for i, r in enumerate(repos, 1):
        print(f"[{i}/{len(repos)}] downloading from {r['repo_id']}...")
        try:
            downloaded = hf_hub_download(
                repo_id=r["repo_id"],
                filename=r["filename"],
                local_dir=target.parent,
                local_dir_use_symlinks=False,
            )
            downloaded_path = Path(downloaded)
            if downloaded_path != target:
                downloaded_path.rename(target)
            size_mb = target.stat().st_size / (1024 * 1024)
            print(f"\n[ok] downloaded successfully: {target} ({size_mb:.0f} MB)")
            return
        except Exception as e:
            print(f"  failed: {type(e).__name__}: {e}\n")

    print("=" * 60)
    print("[!] All sources failed.")
    print("Try:")
    print("  python download_allam_gguf.py --search")
    print("or manually via llama.cpp:")
    print("  brew install llama.cpp")
    print("  llama-cli --hf-repo Omartificial-Intelligence-Space/ALLaM-7B-Instruct-preview-Q4_K_M-GGUF \\")
    print("            --hf-file allam-7b-instruct-preview-q4_k_m.gguf -p 'test'")
    sys.exit(1)


if __name__ == "__main__":
    main()
