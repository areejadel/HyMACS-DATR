"""
judges.py — حكّام v6 بإعدادات موحّدة
=====================================
الإصلاحات مقارنةً بـ v5:
  1) درجة الحرارة 0.2 تُمرَّر صراحةً لكل حَكَم (في v5 كان Kimi وGLM يعملان بـ 0.7
     لأن judge_panel.py لا يمرّر temperature لعميل Together).
  2) الدرجة المركّبة = متوسط الأبعاد الثمانية (كما تصف الورقة)، ونحفظ أيضاً
     حقل overall الذي يكتبه الحَكَم بنفسه للمقارنة.
  3) أنواع البرومبت:
       panel          = برومبت اللوحة في v5 حرفياً (judge_panel.py)
       panel_compact  = نفس البرومبت لكن مخطط JSON بالدرجات فقط (ليتّسع لنافذة ALLaM)
       inner          = برومبت الحَكَم الداخلي في v5 حرفياً (يذكر ML)
       inner_neutral  = برومبت الحَكَم الداخلي بعد جعله محايداً للموضوع
"""
from __future__ import annotations

import json
import time

from common import DIMS, JUDGE_TEMPERATURE, composite, median_scores, truncate_at_paragraph

# الحكّام الخارجيون
# v5: Claude-sonnet-4-6 + Kimi-K2.6 + GLM-5.1 (على Together).
# أكتوبر 2026: Together أوقف Kimi-K2.6 وGLM-5.1 (فُحص حيّاً) ⇒ أقرب خلَف من نفس العائلة على Together:
#   Kimi-K3 (Moonshot) و GLM-5.2 (Zhipu) — تبقى اللوحة ثلاث عائلات مختلفة كما في v5.
# تجاوز أي حَكَم:  V6_JUDGE_kimi=together:<id>  أو  openrouter:<id>
V5_JUDGE_IDS = {"claude": "claude-sonnet-4-6", "kimi": "moonshotai/Kimi-K2.6", "glm": "zai-org/GLM-5.1",
                "gpt4o": "gpt-4o"}
JUDGE_SPECS = {
    "claude": ("anthropic", "claude-sonnet-4-6"),
    "kimi":   ("together",  "moonshotai/Kimi-K3"),
    "glm":    ("together",  "zai-org/GLM-5.2"),
    "gpt4o":  ("openai",    "gpt-4o"),
}
import os as _os
for _r in list(JUDGE_SPECS):
    _e = _os.getenv(f"V6_JUDGE_{_r}")
    if _e and ":" in _e:
        JUDGE_SPECS[_r] = tuple(_e.split(":", 1))


def judge_changed_since_v5(role: str) -> bool:
    return JUDGE_SPECS[role][1].lower() != V5_JUDGE_IDS.get(role, "").lower()


PANEL3 = ["claude", "kimi", "glm"]

_clients: dict = {}


def _client_for(role: str):
    """role ∈ JUDGE_SPECS أو 'gen:<model_key>' (المولّد نفسه كحَكَم)."""
    if role in _clients:
        return _clients[role]
    if role.startswith("gen:"):
        from clients import get_client
        c = get_client(role[4:])
    else:
        backend, api_id = JUDGE_SPECS[role]
        if backend == "anthropic":
            from clients.claude_client import ClaudeClient
            c = ClaudeClient(api_id, temperature=JUDGE_TEMPERATURE, label=role)
        elif backend == "openai":
            from clients.openai_client import OpenAIClient
            c = OpenAIClient(api_id, temperature=JUDGE_TEMPERATURE, label=role)
        elif backend == "openrouter":
            import common
            if common.MOCK:
                from mock_clients import FakeClient
                c = FakeClient(api_id, label=role)
            else:
                from openrouter_client import OpenRouterClient
                c = OpenRouterClient(api_id, label=role, temperature=JUDGE_TEMPERATURE)
        else:
            import common
            if common.MOCK:
                from mock_clients import FakeClient
                c = FakeClient(api_id, label=role)
            else:
                from together_v6_client import TogetherV6Client
                c = TogetherV6Client(api_id, label=role, temperature=JUDGE_TEMPERATURE)
    _clients[role] = c
    return c


def model_id_of(role: str) -> str:
    if role.startswith("gen:"):
        return str(getattr(_client_for(role), "model_id", role))
    return JUDGE_SPECS[role][1]


# ─────────────────────────────────────────────────────────────
#  البرومبتات
# ─────────────────────────────────────────────────────────────
NEUTRAL_INNER_SYSTEM = (
    "You are a strict, fair evaluator of university-level educational material. "
    "You score lectures on 8 dimensions, each from 1 (poor) to 10 (excellent). "
    "You provide concise justifications and concrete suggestions for improvement. "
    "Be calibrated — most lectures should score in the 5-8 range; reserve 9-10 for "
    "genuinely outstanding work and 1-4 for serious deficiencies. Do NOT inflate scores. "
    "Output STRICT JSON only — no markdown, no preamble, no commentary outside the JSON."
)


def build_messages(prompt: str, lecture: str) -> list[dict]:
    if prompt == "panel":
        from pipeline.judge_panel import _JUDGE_SYSTEM_PROMPT, _build_user_prompt
        return [{"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(lecture)}]
    if prompt == "panel_compact":
        from pipeline.judge_panel import _JUDGE_SYSTEM_PROMPT, _RUBRIC_DESCRIPTIONS
        rubric = "\n".join(f"  - {d}: {_RUBRIC_DESCRIPTIONS[d]}" for d in DIMS)
        schema = {"scores": {d: "<float 1-10>" for d in DIMS}, "overall": "<float 1-10>"}
        user = ("Evaluate the following lecture on these 8 dimensions:\n"
                f"{rubric}\n\nOutput ONLY valid JSON matching this schema (no justifications):\n"
                f"{json.dumps(schema, indent=2)}\n\n── LECTURE ──\n{lecture}\n── END ──")
        return [{"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user}]
    if prompt in ("inner", "inner_neutral"):
        import pipeline.inner_judge as ij
        user = ij._build_user_prompt(lecture)
        system = ij._JUDGE_SYSTEM_PROMPT
        if prompt == "inner_neutral":
            system = NEUTRAL_INNER_SYSTEM
            user = user.replace("real ML practice", "real practice in the field")
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]
    raise ValueError(prompt)


def _parse(text: str) -> dict:
    from pipeline.judge_panel import _parse_json
    return _parse_json(text)


# ─────────────────────────────────────────────────────────────
#  حَكَم واحد
# ─────────────────────────────────────────────────────────────
def judge(role: str, lecture: str, prompt: str = "panel", max_chars: int | None = None,
          max_tokens: int | None = None, retries: int = 2) -> dict:
    """يقيّم محاضرة بحَكَم واحد. يعيد dict فيه scores/composite/overall_reported/tokens."""
    text = truncate_at_paragraph(lecture, max_chars) if max_chars else lecture
    if max_tokens is None:
        max_tokens = 900 if prompt == "panel_compact" else 2500
        if role == "gen:allam_7b":
            max_tokens = min(max_tokens, 900)
    messages = build_messages(prompt, text)
    client = _client_for(role)
    kwargs = {"max_tokens": max_tokens, "temperature": JUDGE_TEMPERATURE}
    if role in JUDGE_SPECS and JUDGE_SPECS[role][0] == "openai":
        kwargs["response_format"] = {"type": "json_object"}
    last_err, pt, ct = None, 0, 0
    for attempt in range(retries + 1):
        res = client.generate(messages=messages, **kwargs)
        pt += getattr(res, "prompt_tokens", 0) or 0
        ct += getattr(res, "completion_tokens", 0) or 0
        if not getattr(res, "ok", False):
            last_err = getattr(res, "error", "no result")
            time.sleep(2 * (attempt + 1))
            continue
        p = _parse(res.text)
        comp = composite(p.get("scores"))
        if p.get("error") or comp != comp:          # NaN = بُعد ناقص
            last_err = p.get("error") or "missing dimension score"
            from guard import GUARD
            GUARD.quality(f"judge:{role}", False, f"{last_err}: {res.text[:120]!r}")
            continue
        from guard import GUARD
        GUARD.quality(f"judge:{role}", True)
        return {"role": role, "model_id": model_id_of(role), "prompt": prompt,
                "scores": p["scores"], "composite": comp,
                "overall_reported": p.get("overall", 0.0),
                "input_chars": len(text), "truncated": len(text) < len(lecture),
                "prompt_tokens": pt, "completion_tokens": ct, "attempts": attempt + 1,
                "served_by": getattr(res, "served_by", None), "error": None}
    return {"role": role, "model_id": model_id_of(role), "prompt": prompt,
            "scores": {d: 0.0 for d in DIMS}, "composite": float("nan"),
            "overall_reported": 0.0, "input_chars": len(text),
            "truncated": len(text) < len(lecture), "prompt_tokens": pt,
            "completion_tokens": ct, "attempts": retries + 1, "error": str(last_err)}


def panel_eval(lecture: str, roles=PANEL3, prompt: str = "panel", max_chars=None) -> dict:
    """لوحة كاملة → وسيط كل بُعد + المركّبة (متوسط الوسائط)."""
    per = {r: judge(r, lecture, prompt=prompt, max_chars=max_chars) for r in roles}
    ok = [v for v in per.values() if not v.get("error")]
    med = median_scores(ok)
    return {"per_judge": per, "median_scores": med, "composite": composite(med),
            "n_ok": len(ok), "roles": list(roles), "prompt": prompt,
            "error": None if len(ok) == len(roles) else
                     f"partial panel ({len(ok)}/{len(roles)}) — will be retried"}


def neutralize_inner_judge():
    """يجعل الحَكَم الداخلي في v5 محايداً للموضوع (بدون تعديل الملف على القرص)."""
    import pipeline.inner_judge as ij
    ij._JUDGE_SYSTEM_PROMPT = NEUTRAL_INNER_SYSTEM
    ij._RUBRIC_DESCRIPTIONS["practical_relevance"] = "Are concepts connected to real practice in the field?"
    return ij
