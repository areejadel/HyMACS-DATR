"""رصد المخرجات المنحطّة من المزوّد (لوحظت في Qwen3-235B عبر OpenRouter، 24–25 أكتوبر 2026):
  (أ) حلقة تكرار: "In In In ..."         ← نسبة الكلمات الفريدة < 0.10
  (ب) هيكل بلا محتوى: كل سطر نثري كلمة واحدة ("We", "Let", "1.", "-")  ← نسبة الأسطر-البذرة ≥ 0.35
عُيّرت على 537 محاضرة/مقترح: كل المحاضرات الحقيقية ≤ 0.27 (الوسيط 0.01)، والمنحطّة ≥ 0.41."""
import re

def stub_fraction(t: str) -> float:
    L = [l.strip() for l in (t or "").splitlines() if l.strip()]
    prose = [l for l in L if not l.startswith(("#", "$", "\\", "|", "```", "---"))]
    if len(prose) < 20:
        return 0.0
    stub = sum(1 for l in prose if re.fullmatch(r"(?:[-*>]|\d+\.)?\s*[^\s]{0,15}", l))
    return stub / len(prose)

def is_degenerate(t: str) -> bool:
    w = (t or "").split()
    if len(w) < 200:
        return False
    return len(set(w)) / len(w) < 0.10 or stub_fraction(t) >= 0.35
