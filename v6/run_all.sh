#!/usr/bin/env bash
# run_all.sh — تشغيل تجارب v6 بالترتيب الموصى به
# كل خطوة تُستأنف تلقائياً لو انقطعت: أعيدي نفس الأمر فيكمل من حيث توقّف.
#
#   bash run_all.sh estimate  ← تقدير التكلفة لكل مزوّد (بلا أي استدعاء)
#   bash run_all.sh smoke     ← فحص كل النماذج (أقل من سنت)
#   bash run_all.sh judges    ← تجارب التقييم: 2 ثم 3 ثم 5 ثم 4   (~2–3 ساعات)
#   bash run_all.sh exp1      ← التحسين من نفس المسودة               (~12–14 ساعة، يُفضّل ليلاً)
#   bash run_all.sh analyze   ← التحليل والجداول
#   bash run_all.sh all       ← كل ما سبق بالترتيب
#   WITH_DEEPSEEK=1 bash run_all.sh exp1   ← + DeepSeek-V4-Pro-0813 (بديل، ~$12 إضافية على Together)
set -eo pipefail
cd "$(dirname "$0")"
source ../v5/venv/bin/activate
mkdir -p logs
STAGE="${1:-all}"
W="${WORKERS:-6}"

EXTRA=""
[[ "${WITH_DEEPSEEK:-0}" == "1" ]] && EXTRA="--include-substitutes"

if [[ "$STAGE" == "estimate" ]]; then
  python estimate_cost.py $EXTRA
  exit 0
fi

if [[ "$STAGE" == "smoke" || "$STAGE" == "all" ]]; then
  python smoke_v6.py --with-local | tee logs/smoke.log
fi

if [[ "$STAGE" == "judges" || "$STAGE" == "all" ]]; then
  python exp2_rejudge_panel.py --part both --workers "$W" 2>&1 | tee logs/exp2.log
  python exp3_gpt4o_panel_prompt.py --workers "$W"     2>&1 | tee logs/exp3.log
  python exp5_length_control.py --workers "$W"         2>&1 | tee logs/exp5.log
  python exp4_cross_judge.py --workers "$W"            2>&1 | tee logs/exp4.log
fi

if [[ "$STAGE" == "exp1" || "$STAGE" == "all" ]]; then
  # النموذجان المحليان (ALLaM ثم Llama-3-8B) في الخلفية، واحداً تلو الآخر، بالتوازي مع السحابة
  ( python exp1_shared_draft.py --topic backprop      --models allam_7b   --workers 1 && \
    python exp1_shared_draft.py --topic normalization --models allam_7b   --workers 1 && \
    python exp1_shared_draft.py --topic backprop      --models llama_3_8b --workers 1 && \
    python exp1_shared_draft.py --topic normalization --models llama_3_8b --workers 1 ) \
    > logs/exp1_local.log 2>&1 &
  LOCAL_PID=$!
  python exp1_shared_draft.py --topic backprop      --skip-local $EXTRA --workers "$W" 2>&1 | tee logs/exp1_backprop.log
  python exp1_shared_draft.py --topic normalization --skip-local $EXTRA --workers "$W" 2>&1 | tee logs/exp1_normalization.log
  echo "بانتظار انتهاء النموذجين المحليين (السجل: logs/exp1_local.log)…"
  wait $LOCAL_PID
fi

if [[ "$STAGE" == "analyze" || "$STAGE" == "all" ]]; then
  python analyze_v6.py 2>&1 | tee logs/analyze.log
  echo "✓ افتحي results_v6/report_v6.md"
fi
