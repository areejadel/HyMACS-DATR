#!/usr/bin/env bash
# run_baselines.sh — خطّا أساس إضافيان طلبهما المراجعون، على نفس الـ60 مسودة:
#   datr_random_composite : DATR يختار بُعدين عشوائيين + حارس مركّب (نفس التكلفة)
#   self_refine_composite : Self-Refine + حارس مركّب
# آمن للإيقاف والإعادة: أعيدي نفس الأمر ويكمل من حيث توقف.
#   caffeinate -i bash run_baselines.sh
set -eo pipefail
cd "$(dirname "$0")"
source ../v5/venv/bin/activate
mkdir -p logs
W="${WORKERS:-3}"
export V6_CAP_OPENROUTER="${V6_CAP_OPENROUTER:-15}"
export V6_CAP_TOGETHER="${V6_CAP_TOGETHER:-26}"
export V6_CAP_OPENAI="${V6_CAP_OPENAI:-30}"
export V6_CAP_ANTHROPIC="${V6_CAP_ANTHROPIC:-15}"
C="datr_random_composite self_refine_composite"
export PYTHONUNBUFFERED=1
# Llama-3.3-70B-Instruct-Turbo لم يعد متاحاً «بلا خادم» على Together ⇒ نفس الأوزان عبر OpenRouter
export V6_ROUTE_llama_3_3_70b="${V6_ROUTE_llama_3_3_70b:-openrouter:meta-llama/llama-3.3-70b-instruct}"

if pgrep -f "exp1_shared_draft.py.*--models (allam_7b|llama_3_8b)" >/dev/null; then
  echo "▶ النموذجان المحليان يعملان أصلاً في الخلفية — لن أشغّل نسخة ثانية"
  LOCAL_PID=""
else
echo "▶ النموذجان المحليان في الخلفية (السجل: logs/baselines_local.log)"
( python exp1_shared_draft.py --topic backprop      --models allam_7b   --workers 1 --conditions $C && \
  python exp1_shared_draft.py --topic normalization --models allam_7b   --workers 1 --conditions $C && \
  python exp1_shared_draft.py --topic backprop      --models llama_3_8b --workers 1 --conditions $C && \
  python exp1_shared_draft.py --topic normalization --models llama_3_8b --workers 1 --conditions $C ) \
  >> logs/baselines_local.log 2>&1 &
LOCAL_PID=$!
fi

echo "▶ النماذج السحابية"
python exp1_shared_draft.py --topic backprop      --skip-local --include-substitutes --conditions $C --workers "$W" 2>&1 | tee logs/baselines_backprop.log
python exp1_shared_draft.py --topic normalization --skip-local --include-substitutes --conditions $C --workers "$W" 2>&1 | tee logs/baselines_normalization.log

echo "بانتظار انتهاء النموذجين المحليين… (tail -f logs/baselines_local.log)"
[ -n "$LOCAL_PID" ] && wait $LOCAL_PID || echo "(تابعي المحليين: tail -f logs/baselines_local.log)"
echo "✓ انتهى كل شيء. أرسلي لـClaude: results_v6/exp1 + results_v6/spend_ledger.jsonl"
