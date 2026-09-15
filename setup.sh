#!/usr/bin/env bash
# ================================================================
# setup.sh — set up the environment on Apple Silicon (M-series)
# ================================================================
# Builds a venv, installs all packages, sets up ALLaM via MLX.
# Usage:  bash setup.sh
set -e

echo "========================================================"
echo "  Environment setup on Apple Silicon"
echo "========================================================"

# ── 1) Check it is Apple Silicon ──
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
  echo "[!] architecture = $ARCH (expected arm64). Make sure you are using a native Apple Silicon Python."
else
  echo "[ok] Apple Silicon (arm64) — MLX supported."
fi

# ── 2) Check Python 3.11+ ──
if ! command -v python3 >/dev/null 2>&1; then
  echo "[x] Python not installed. Install it: brew install python@3.12"
  exit 1
fi
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
echo "[ok] Python $PYV"

# ── 3) Create venv ──
if [ ! -d "venv" ]; then
  echo "-> creating the virtual environment venv ..."
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip -q

# ── 4) Install packages ──
echo "-> installing requirements (may take a few minutes) ..."
pip install -r requirements.txt -q

# ── 5) MLX for ALLaM (Apple Silicon) ──
echo "-> ensuring mlx-lm (run ALLaM locally) ..."
pip install -U mlx-lm -q || echo "[!] mlx-lm install failed — use ALLAM_BACKEND=local (GGUF) instead."

# ── 6) .env ──
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "-> created .env from the template. [!] open it and fill in the three keys + TOPIC + textbook paths."
else
  echo "[ok] .env exists."
fi

# ── 7) Summary ──
echo ""
echo "========================================================"
echo "  [ok] Setup complete. Next steps:"
echo "========================================================"
echo "  1) Fill in .env:  keys (Together/OpenAI/Anthropic) + ALLAM_BACKEND=mlx"
echo "  2) Place the RAG textbooks under ./books/  (Deep Learning + Database Systems)"
echo "  3) Activate the env:   source venv/bin/activate"
echo "  4) Smoke test:         python run_v5.py --smoke --skip-allam   (API only, ~3 min)"
echo "  5) ALLaM smoke test:   python run_v5.py --smoke --models allam_7b"
echo "  6) Full run:           python run_v5.py --topic backprop --resume"
echo "========================================================"
