#!/usr/bin/env bash
# يكمل تشغيلات Qwen دون مسح السليم.
# الحَكَمان Kimi-K3 وGLM-5.2 عبر OpenRouter مثبّتين على Together (بعد نفاد رصيد Together) — بعد اجتياز المعايرة.
set -eo pipefail
cd "$(dirname "$0")"; source ../v5/venv/bin/activate; mkdir -p logs
export V6_JUDGE_kimi="openrouter:moonshotai/kimi-k3" V6_JUDGE_glm="openrouter:z-ai/glm-5.2"
export V6_CAP_OPENROUTER="${V6_CAP_OPENROUTER:-24}" V6_CAP_TOGETHER=26 V6_CAP_OPENAI=35 V6_CAP_ANTHROPIC=15 PYTHONUNBUFFERED=1
if [ ! -f results_v6/calibration/PASSED ]; then
  echo "▶ معايرة الحَكَمين (10 محاضرات، ~\$0.3)"
  python calib_judges_or.py 2>&1 | tee logs/calib_judges_or.log
  touch results_v6/calibration/PASSED
fi
python3 - <<'PY'
import json,shutil,time,glob
from degen import is_degenerate
tag=time.strftime("%Y%m%d_%H%M")
for t in ("backprop","normalization"):
    f=f"results_v6/exp1/{t}/runs.jsonl"; shutil.copy(f,f+f".bak_{tag}")
    keep=[];rm=[]
    for l in open(f):
        r=json.loads(l)
        if r["model_key"]=="qwen3_235b" and r["condition"] in ("datr_random_composite","self_refine_composite"):
            props=glob.glob(f"results_v6/exp1/{t}/lectures/proposals/qwen3_235b__{r['condition']}__seed{r['seed']}__it*.md")
            if any(is_degenerate(open(p,encoding='utf-8').read()) for p in props):
                rm.append(r["key"]); continue
        keep.append(l)
    open(f,"w").writelines(keep); print(t,"removed (degenerate):",len(rm),rm)
PY
C="datr_random_composite self_refine_composite"
for T in backprop normalization; do
  python exp1_shared_draft.py --topic $T --models qwen3_235b --conditions $C --workers 3 2>&1 | tee -a logs/rerun_qwen_$T.log
done
echo "✓ انتهى. قولي لـClaude: خلص"
