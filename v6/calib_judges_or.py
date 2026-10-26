"""معايرة: هل Kimi-K3 وGLM-5.2 عبر OpenRouter (المثبّت على Together) يعطيان نفس درجات Together المباشر؟
يعيد تقييم 10 محاضرات نهائية لها درجات محفوظة من Together ويقارن. يخرج بكود 0 إن نجح، 1 إن فشل."""
import json, glob, os, sys, statistics as st
os.environ.setdefault("V6_JUDGE_kimi", "openrouter:moonshotai/kimi-k3")
os.environ.setdefault("V6_JUDGE_glm", "openrouter:z-ai/glm-5.2")
import common
common.setup("backprop", mock=("--mock" in sys.argv) or None)
from judges import judge, DIMS, JUDGE_SPECS
E1 = common.OUT_DIR / "exp1"
print("routes:", JUDGE_SPECS["kimi"], JUDGE_SPECS["glm"])
recs = []
for t in ("backprop", "normalization"):
    for l in open(E1 / t / "runs.jsonl", encoding="utf-8"):
        r = json.loads(l)
        if r["condition"] in ("datr_random_composite", "self_refine_composite") and r["model_key"] != "qwen3_235b" \
           and not r.get("error") and not r.get("final_is_draft") and r["panel"]["n_ok"] == 3:
            f = str(E1 / t / "lectures" / f"{r['model_key']}__{r['condition']}__seed{r['seed']}.md")
            if os.path.exists(f): recs.append((r, f))
# عيّنة متنوعة ثابتة: محاضرتان من كل نموذج
by = {}
for r, f in sorted(recs, key=lambda x: x[0]["key"]):
    by.setdefault(r["model_key"], []).append((r, f))
sample = []
for i in range(10):                       # توزيع دوري على النماذج حتى 10 محاضرات
    for m in sorted(by):
        if i < len(by[m]) and len(sample) < 10: sample.append(by[m][i])
diffs = {"kimi": [], "glm": []}; pd = []; served = set()
for r, f in sample:
    lec = open(f, encoding="utf-8").read()
    new = {}
    for role in ("kimi", "glm"):
        j = judge(role, lec, prompt="panel")
        if j.get("error"): print("  ✗", role, j["error"][:150]); sys.exit(1)
        served.add(str(j.get("served_by"))); new[role] = j
        diffs[role].append(j["composite"] - r["panel"]["per_judge"][role]["composite"])
    old_med = r["panel"]["composite"]
    sc = {d: st.median([r["panel"]["per_judge"]["claude"]["scores"][d], new["kimi"]["scores"][d], new["glm"]["scores"][d]]) for d in DIMS}
    pd.append(sum(sc.values()) / len(sc) - old_med)
    print(f"  {r['key'][:55]:55s} kimi {diffs['kimi'][-1]:+.2f}  glm {diffs['glm'][-1]:+.2f}  panel {pd[-1]:+.2f}")
res = {k: {"mean": round(st.mean(v), 3), "mae": round(st.mean(abs(x) for x in v), 3)} for k, v in diffs.items()}
res["panel"] = {"mean": round(st.mean(pd), 3), "mae": round(st.mean(abs(x) for x in pd), 3)}
res["served_by"] = sorted(served); res["n"] = len(sample)
print(json.dumps(res, ensure_ascii=False, indent=1))
CD = common.OUT_DIR / "calibration"; CD.mkdir(exist_ok=True)
json.dump(res, open(CD / "judges_openrouter_vs_together.json", "w"), indent=1)
ok = abs(res["panel"]["mean"]) <= 0.15 and res["panel"]["mae"] <= 0.25
if "--mock" not in sys.argv and not all("together" in s.lower() for s in served):
    print("✗ مزوّد غير Together خدم الطلب:", served); ok = False
print("✓ المعايرة ناجحة" if ok else "✗ المعايرة فشلت — لن نكمل")
sys.exit(0 if ok else 1)
