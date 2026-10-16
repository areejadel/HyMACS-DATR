#!/usr/bin/env bash
# run_extra.sh — Gemma-4-31B + Qwen3-235B-2507 + DeepSeek-V4-Pro عبر OpenRouter (نفس نماذج v5)
#   exp4: كل واحد منها يحكم على الـ36 محاضرة (التفضيل الذاتي)
#   exp1: التحسين من نفس المسودة للنماذج الثلاثة في الموضوعين
# آمن بالتوازي مع exp1 المحلي (ALLaM / Llama-8B)، ويُستأنف إذا انقطع: أعيدي نفس الأمر.
#   caffeinate -i bash run_extra.sh
set -eo pipefail
cd "$(dirname "$0")"
source ../v5/venv/bin/activate
mkdir -p logs
W="${WORKERS:-3}"
if ! grep -q '^OPENROUTER_API_KEY=..*' ../v5/.env; then
  echo "⚠️  أضيفي سطر OPENROUTER_API_KEY=sk-or-... إلى ../v5/.env أولاً"; exit 1
fi
NEW="gemma_4_31b deepseek_v3_1 qwen3_235b"
python exp4_cross_judge.py --only-judges gen:gemma_4_31b gen:deepseek_v3_1 gen:qwen3_235b --workers "$W" 2>&1 | tee logs/extra_exp4.log
python exp1_shared_draft.py --topic backprop      --models $NEW --workers "$W" 2>&1 | tee logs/extra_exp1_backprop.log
python exp1_shared_draft.py --topic normalization --models $NEW --workers "$W" 2>&1 | tee logs/extra_exp1_normalization.log
echo "✓ انتهى — بعد انتهاء exp1 المحلي أيضاً: bash run_all.sh analyze"
