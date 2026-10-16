"""
mock_clients.py — عملاء وهميون لاختبار خطّ v6 كاملاً بدون أي تكلفة API
========================================================================
التفعيل:  V6_MOCK=1 python exp2_rejudge_panel.py ...   (أو --mock في أي سكربت)
- الحَكَم الوهمي يعيد درجات حول علامة QUALITY=x في النص (إن وُجدت) مع ضوضاء.
- الوكيل الوهمي يعيد المسودة نفسها مع تغيير صغير عشوائي في QUALITY.
لا يُستخدم أبداً في التشغيل الحقيقي.
"""
from __future__ import annotations

import hashlib
import json
import random
import re

from clients.base import BaseClient, GenerationResult

_LENIENCY = {"claude": 0.0, "kimi": -0.2, "glm": -0.1, "gpt4o": 1.2}


def _q(text: str) -> float:
    m = re.search(r"QUALITY=([0-9.]+)", text)
    return float(m.group(1)) if m else 5.0


class FakeClient(BaseClient):
    context_tokens = 131072

    def __init__(self, model_id="fake", temperature=0.2, label="fake", **kw):
        super().__init__(model_id, label)

    def generate(self, messages, max_tokens=1500, temperature=0.7, **kwargs):
        import os
        fail = os.getenv("V6_MOCK_FAIL", "")
        if fail and fail in (self.model_id + self.label).lower():
            return GenerationResult(text="", model=self.model_id, error="402 insufficient credits (mock)")
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        user = messages[-1]["content"]
        r = random.Random(hashlib.md5((self.label + user[-400:] + str(random.random())).encode()).hexdigest())
        if "evaluator" in system.lower():
            body = user.split("── LECTURE ──")[-1]
            q = _q(body)
            len_bonus = min(len(body) / 20000, 1.0)
            lab = self.label.split(" ")[0]
            base = q + _LENIENCY.get(lab, 0.0) + (2.0 if lab.startswith("gen:") else 0)
            scores = {d: round(min(10, max(1, base + len_bonus + r.gauss(0, 0.5))), 1) for d in [
                "academic_accuracy", "pedagogical_effectiveness", "clarity_organization",
                "practical_relevance", "completeness", "engagement_potential",
                "technical_quality", "innovation"]}
            out = {"scores": scores, "overall": round(sum(scores.values()) / 8, 2),
                   "justifications": {k: "ok" for k in scores}, "suggestions": {k: "" for k in scores}}
            if r.random() < 0.03:
                return GenerationResult(text="not json", model=self.model_id, prompt_tokens=10, completion_tokens=2)
            return GenerationResult(text=json.dumps(out), model=self.model_id,
                                    prompt_tokens=len(user) // 4, completion_tokens=300)
        # وكيل كتابة
        m = re.search(r"<draft>\n(.*)\n</draft>", user, re.S)
        if m:
            draft = m.group(1)
            q = _q(draft) + r.gauss(0.05, 0.4)
            new = re.sub(r"QUALITY=[0-9.]+", f"QUALITY={max(1, min(9.5, q)):.2f}", draft)
            return GenerationResult(text=new + "\n\n(revised)", model=self.model_id,
                                    prompt_tokens=len(user) // 4, completion_tokens=len(new) // 4)
        return GenerationResult(text=f"QUALITY={r.uniform(2, 8):.2f}\n\nFresh lecture text.\n" * 20,
                                model=self.model_id, prompt_tokens=500, completion_tokens=800)


def install():
    import clients
    import clients.claude_client as cc
    import clients.openai_client as oc
    import clients.together_client as tc

    def fake_get_client(model_key):
        from config import GENERATORS
        c = FakeClient(model_key, label=f"gen:{model_key}")
        if model_key in GENERATORS:
            c.context_tokens = GENERATORS[model_key].context_tokens
        return c

    clients.get_client = fake_get_client
    cc.ClaudeClient = lambda model_id="claude", temperature=0.2, label="claude": FakeClient(model_id, label=label)
    oc.OpenAIClient = lambda model_id="gpt-4o", temperature=0.2, label="gpt4o": FakeClient(model_id, label=label)
    tc.TogetherClient = lambda model_id, label="": FakeClient(model_id, label=label)
    print("⚠️  MOCK MODE — عملاء وهميون، لا استدعاءات API حقيقية")
