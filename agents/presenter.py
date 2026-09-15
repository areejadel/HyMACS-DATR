"""
presenter.py — Presentation Specialist (slide-structured output).

The fifth (and final) HyMACS specialist. Whereas SME / Pedagogy / Clarity /
Engagement collaborate on the *content* of the lecture, the Presenter takes
the consolidated lecture and emits a **slide-structured JSON** that is then
mechanically rendered to PPTX by `pipeline.slide_renderer` (no AI in the
rendering step — see Section 5 of the paper).

The constraints below are not arbitrary; they are grounded in:

  • Mayer's Cognitive Theory of Multimedia Learning (CTML, 2009)
      — Coherence, Signaling, Redundancy, Spatial-/Temporal-Contiguity,
        Segmenting, Modality principles.
  • Sweller's Cognitive Load Theory (CLT, 1988).
  • Reynolds' "Presentation Zen" (2008) — slide-density guidelines.
  • Atkinson's "Beyond Bullet Points" (2008) — title-as-takeaway pattern.

Output JSON schema (validated by `pipeline.slide_renderer`):

    {
      "title":     "<≤ 8 words — declarative takeaway>",
      "subtitle":  "<≤ 12 words — 1-line topic frame>",
      "slides": [
        {
          "type":          "title" | "content" | "math" | "exercise" | "summary",
          "title":         "<≤ 8 words>",
          "subtitle":      "...",                    # title slide (optional)
          "agenda":        ["...", "..."],           # TITLE slide ONLY: 3-5 outline bullets
          "bullets":       ["...", "..."],           # content/summary only
          "equation_tex":  "...",                    # math only (LaTeX inline)
          "equation_caption": "...",                 # math only
          "exercise_prompt": "...",                  # exercise only
          "speaker_notes": "<2–4 sentences, ~30–80 words>"
        },
        ...
      ]
    }
"""
from __future__ import annotations
import json
import re
from typing import Optional

from agents.base import Agent
from clients.base import GenerationResult


# ─── Schema constants (also referenced by slide_renderer) ─────
SLIDE_COUNT_MIN = 12
SLIDE_COUNT_MAX = 15
TITLE_MAX_WORDS = 10
BULLET_MAX_WORDS = 22          # was 15 — allow richer, more professional bullets
BULLETS_PER_CONTENT_MIN = 4    # was 3 — push for substantive coverage
BULLETS_PER_CONTENT_MAX = 6    # was 5
AGENDA_MIN = 3
AGENDA_MAX = 5
AGENDA_ITEM_MAX_WORDS = 12
SPEAKER_NOTES_WORDS_MIN = 50   # was 30 — notes must be substantive
SPEAKER_NOTES_WORDS_MAX = 130  # was 80
ALLOWED_TYPES = {"title", "content", "math", "exercise", "summary"}


class PresenterAgent(Agent):
    """
    Final specialist. Transforms consolidated lecture text into a
    slide-structured JSON object subject to research-grounded constraints.

    Note: This agent does NOT alter the *content* of the lecture; it
    chunks/structures the existing material. Conceptually it sits at the
    end of the HyMACS pipeline (Section 3.3 of the paper).
    """

    name = "presenter"
    role = "Presentation Specialist"
    focus_dimensions = []  # Presenter does not own a rubric dimension.

    system_prompt = (
        "You are a senior ML lecturer preparing a professional university-level slide deck.\n"
        "You will be given a consolidated lecture (already written). Your job is to "
        "convert it into a clean, substantive, professional slide deck as a single JSON object.\n\n"
        "QUALITY BAR — read carefully:\n"
        "  • Treat this as a real graduate-level lecture deck. Not a teaser. Not a wireframe.\n"
        "  • Every slide must have real content: a clear, specific point — not a label.\n"
        "  • Bullets state CONCRETE claims, definitions, intuitions, examples, formulas, "
        "or mechanisms. Bullets are NEVER one-word fragments.\n"
        "  • Use specific terminology and real names where the lecture provides them "
        "(e.g., 'PyTorch autograd', 'Adam optimizer', 'cross-entropy loss', "
        "'ResNet skip connection') — do not water them down.\n"
        "  • Speaker notes are FULL sentences a lecturer would actually say — they "
        "extend, motivate, and contextualize the slide; they NEVER repeat bullets verbatim.\n"
        "  • Slide TITLES are takeaways, not topics. Write 'Backprop is the chain rule on "
        "a computational graph' — not 'Backpropagation'.\n"
        "  • Stay faithful to the provided lecture. You may reorganize, tighten, and "
        "rephrase, but do NOT invent claims, citations, or examples not present in it.\n\n"
        "FIELD-USAGE RULES (very important — these decide where content shows up on the slide):\n"
        "  • For type='math' slides: put the equation in `equation_tex` (LaTeX, no $ "
        "delimiters), and a 1-sentence intuition in `equation_caption`. DO NOT put the "
        "equation inside `bullets`. Math slides may also include 2–4 short `bullets` that "
        "explain the equation's terms or implications, but the equation itself MUST live "
        "in `equation_tex`.\n"
        "  • For type='exercise' slides: put the full task statement in `exercise_prompt` "
        "(2–4 sentences, with concrete numbers / variables). DO NOT put the task in "
        "`bullets`. You MAY include 2–4 short `bullets` listing hints or sub-steps.\n"
        "  • For type='content' and type='summary' slides: use `bullets` only.\n"
        "  • Every slide (including type='title') must have `speaker_notes`.\n\n"
        "DECK SHAPE (in this exact order):\n"
        "  • Slide 1 (type='title'): talk title + subtitle + an `agenda` array of "
        f"{AGENDA_MIN}–{AGENDA_MAX} short outline bullets previewing the lecture.\n"
        "  • Middle slides: a balanced mix of 'content' (~7–9 slides), 'math' (≥2 slides "
        "with real equations), and 'exercise' (≥1 slide).\n"
        "  • Final slide (type='summary'): closing key-takeaways slide.\n\n"
        "HARD CONSTRAINTS (your output WILL be validated):\n"
        f"  • Total slides: {SLIDE_COUNT_MIN}–{SLIDE_COUNT_MAX}.\n"
        f"  • Slide title: ≤ {TITLE_MAX_WORDS} words.\n"
        f"  • Agenda (title slide only): {AGENDA_MIN}–{AGENDA_MAX} items, "
        f"each ≤ {AGENDA_ITEM_MAX_WORDS} words.\n"
        f"  • Bullets per content/summary slide: {BULLETS_PER_CONTENT_MIN}–"
        f"{BULLETS_PER_CONTENT_MAX}.\n"
        f"  • Each bullet: ≤ {BULLET_MAX_WORDS} words. Bullets must be full noun-phrase or "
        "short-sentence claims — never one-word labels.\n"
        f"  • Speaker notes: {SPEAKER_NOTES_WORDS_MIN}–{SPEAKER_NOTES_WORDS_MAX} words "
        "(3–5 full sentences) on EVERY slide, including the title slide.\n"
        "  • At least 2 'math' slides — each with a non-empty `equation_tex` (real LaTeX).\n"
        "  • At least 1 'exercise' slide — with a non-empty `exercise_prompt`.\n"
        "  • Exactly 1 'summary' slide, and it MUST be the final slide.\n"
        "  • Slide `type` must be one of: title, content, math, exercise, summary.\n\n"
        "OUTPUT FORMAT — single valid JSON object only. No markdown fences, no preamble, "
        "no commentary. Begin with `{` and end with `}`.\n"
        "**Write in English only.** Never produce Arabic, Chinese, or any other language.\n"
        "JSON safety: escape every backslash inside strings (use `\\\\` for one backslash "
        "in LaTeX), escape every double quote inside strings, no trailing commas.\n\n"
        "── REFERENCE EXAMPLE (shape and quality bar — do NOT copy this content) ──\n"
        "{\n"
        '  "title": "Backprop Is Calculus on a Computational Graph",\n'
        '  "subtitle": "How gradients flow through composed functions",\n'
        '  "slides": [\n'
        "    {\n"
        '      "type": "title",\n'
        '      "title": "Backprop Is Calculus on a Computational Graph",\n'
        '      "subtitle": "How gradients flow through composed functions",\n'
        '      "agenda": [\n'
        '        "Why gradients drive learning",\n'
        '        "Forward pass: caching activations",\n'
        '        "Backward pass: chain rule on the graph",\n'
        '        "A worked two-layer numerical example",\n'
        '        "Failure modes: vanishing and exploding gradients"\n'
        "      ],\n"
        '      "speaker_notes": "Open by anchoring the audience: training a deep network is '
        "just minimizing a scalar loss over millions of parameters. The question is how to do "
        "that efficiently. Backprop is not a new algorithm — it is the chain rule from calculus "
        'applied systematically to a computational graph. Preview where the worked example lands."\n'
        "    },\n"
        "    {\n"
        '      "type": "content",\n'
        '      "title": "A Network Is a Composition of Differentiable Functions",\n'
        '      "bullets": [\n'
        '        "Each layer maps inputs to outputs through a differentiable function",\n'
        '        "Stacking gives us a single composed function f(g(h(x)))",\n'
        '        "The loss L is a scalar at the end of this composition",\n'
        '        "Training adjusts every parameter to reduce L on average",\n'
        '        "Differentiability is what makes gradient-based learning possible"\n'
        "      ],\n"
        '      "speaker_notes": "Emphasize that nothing in a feed-forward network is mysterious. '
        "Each layer is a function, and stacking them produces another function. The loss reduces "
        "this entire composition to a single number. Our task is to compute the sensitivity of "
        "that number to every weight in the network — that is the gradient. Differentiability "
        'is the structural property that makes the whole pipeline tractable."\n'
        "    },\n"
        "    {\n"
        '      "type": "math",\n'
        '      "title": "The Chain Rule, Applied to Every Edge",\n'
        '      "equation_tex": "\\\\frac{\\\\partial L}{\\\\partial w} = \\\\frac{\\\\partial L}'
        "{\\\\partial y} \\\\cdot \\\\frac{\\\\partial y}{\\\\partial z} \\\\cdot "
        "\\\\frac{\\\\partial z}{\\\\partial w}\",\n"
        '      "equation_caption": "Local gradients multiply along the path from the loss back to the weight.",\n'
        '      "bullets": [\n'
        '        "Each factor is a local Jacobian computed during the forward pass",\n'
        '        "Backprop reuses these locals — every weight update is one graph traversal",\n'
        '        "This is why training cost scales linearly with parameters, not quadratically"\n'
        "      ],\n"
        '      "speaker_notes": "Walk through the equation slowly. The left side is the quantity '
        "we want — how much the loss changes when we nudge a single weight. The right side "
        "decomposes into a product of local gradients that the forward pass has already cached. "
        "This decomposition is the entire content of backprop in one line, and it is what makes "
        'training a billion-parameter model computationally feasible at all."\n'
        "    },\n"
        "    {\n"
        '      "type": "exercise",\n'
        '      "title": "Try It: Two-Layer Network With ReLU",\n'
        '      "exercise_prompt": "Given y = w2 * relu(w1 * x + b1) + b2 and squared loss '
        "L = (y - t)^2 with x = 1.0, t = 0.5, w1 = 0.8, w2 = -1.2, b1 = 0.1, b2 = 0.0: "
        '(a) compute the forward pass; (b) derive dL/dw1 by hand; (c) report which term vanishes when w1 * x + b1 < 0.",\n'
        '      "bullets": [\n'
        '        "Hint: ReLU\\u2019s derivative is the indicator 1[z > 0]",\n'
        '        "Hint: chain through the output, then the activation, then the linear layer",\n'
        '        "Discuss why a negative pre-activation kills the gradient signal"\n'
        "      ],\n"
        '      "speaker_notes": "Give students four minutes. The goal is to feel the chain rule '
        "unroll layer by layer. They should produce one term per layer, with ReLU contributing "
        "an indicator function that switches off when the pre-activation is negative. The "
        "vanishing case is the entire point — it explains why dead ReLUs and bad initialization "
        'matter in practice."\n'
        "    },\n"
        "    {\n"
        '      "type": "summary",\n'
        '      "title": "What To Remember About Backpropagation",\n'
        '      "bullets": [\n'
        '        "Backprop is the chain rule applied to a computational graph, nothing more",\n'
        '        "The forward pass caches activations; the backward pass reuses them",\n'
        '        "Every parameter receives exactly one gradient per training step",\n'
        '        "Vanishing gradients motivate ReLU, batch norm, and residual connections",\n'
        '        "Modern frameworks like PyTorch and TensorFlow automate this with autograd"\n'
        "      ],\n"
        '      "speaker_notes": "Close by tying the math back to engineering decisions students '
        "will actually make: activation choice, weight initialization, network depth, optimizer. "
        "The chain rule is the invariant — everything else in modern deep learning is engineering "
        "around the failure modes of that single equation. Mention PyTorch autograd as the "
        'standard implementation they will use in practice."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "── END OF REFERENCE EXAMPLE ──\n"
        "The example above is shortened to 5 slides; YOUR output MUST contain "
        f"{SLIDE_COUNT_MIN}–{SLIDE_COUNT_MAX} slides total, with at least 2 'math' "
        "slides and at least 1 'exercise' slide.\n"
    )

    # ------------------------------------------------------------------
    def structure(self, final_lecture: str, topic: Optional[str] = None) -> dict:
        """
        Convert the final lecture text to a slide-structured JSON.

        Strategy:
            1. First call: standard prompt, parse output via 5-strategy parser.
            2. If parse fails, do ONE repair pass — feed the bad output and the
               parser error back to the model and ask it to return valid JSON.
            This pattern recovers most "almost-JSON" failures (stray commas,
            unescaped backslashes, trailing prose) on smaller models without
            burning a second full generation budget.

        Returns the parsed dict on success, or {'error': ...} on failure.
        """
        topic = topic or "Backpropagation in Deep Learning"

        # ── Context budgeting: avoids 422 on small-window models (Llama-3-8B = 8192) ──
        ctx = getattr(self.client, "context_tokens", 131072)
        sys_tok = len(self.system_prompt) // 4          # estimated system-prompt tokens
        margin, fixed_user = 500, 400
        # Very small window (ALLaM 4096): the Presenter does not fit (system prompt alone ~2100).
        # Skip it cleanly — slides are an extra output, not part of the research-question evaluation.
        if ctx - sys_tok - fixed_user - margin - 375 < 1500:
            return {"error": "skipped: model context too small for Presenter (slides optional)"}
        out_budget = 4000                               # output tokens for the slide JSON
        lecture_tok_budget = ctx - out_budget - sys_tok - fixed_user - margin
        if lecture_tok_budget < 600:                    # narrow context — reduce output
            out_budget = max(2200, ctx - sys_tok - fixed_user - 800 - margin)
            lecture_tok_budget = ctx - out_budget - sys_tok - fixed_user - margin
        max_lec_chars = max(1500, lecture_tok_budget * 4)
        lecture = final_lecture
        if len(lecture) > max_lec_chars:
            lecture = lecture[:max_lec_chars] + "\n[...truncated for slide structuring...]"

        user_msg = (
            f"Topic: {topic}\n"
            "**Output language: English only.**\n\n"
            "── CONSOLIDATED LECTURE ──\n"
            f"{lecture}\n"
            "── END OF LECTURE ──\n\n"
            "Transform the lecture above into a professional slide deck as a single JSON "
            "object that follows the schema and quality bar in your system prompt.\n\n"
            "Specifically:\n"
            "  • Use the lecture's actual equations, definitions, and examples — preserve "
            "specifics (variable names, numerical values, concrete framework names like "
            "PyTorch / TensorFlow / Adam / ReLU / cross-entropy) rather than abstracting "
            "them away.\n"
            "  • Put every equation in `equation_tex` (LaTeX, with \\\\ escaping) — never "
            "inside `bullets`.\n"
            "  • Put every exercise task in `exercise_prompt` — never inside `bullets`.\n"
            "  • Bullets must be substantive claims, not labels. Speaker notes must be "
            "3–5 full sentences a lecturer would actually say.\n"
            "  • Do NOT invent claims, citations, or examples not present in the lecture; "
            "you may rephrase, chunk, and tighten.\n\n"
            "Output the JSON object ONLY — no prose, no fences."
        )
        result: GenerationResult = self._call(user_msg, max_tokens=out_budget)
        if not result.ok:
            return {"error": f"Presenter LLM call failed: {result.error}"}

        parsed = _parse_slides_json(result.text)
        if "error" not in parsed:
            return parsed

        # ── Repair pass — one shot at fixing malformed JSON ──────────
        bad_output = result.text or ""
        # Cap the size we feed back so we don't blow the context window
        # on small-context models (e.g., Llama-3-8B = 8192).
        _cap = min(8000, max_lec_chars)
        if len(bad_output) > _cap:
            bad_output = bad_output[:_cap] + "\n…[truncated]"

        repair_msg = (
            "Your previous response could not be parsed as JSON.\n"
            f"Parser error: {parsed['error']}\n\n"
            "── YOUR PREVIOUS OUTPUT ──\n"
            f"{bad_output}\n"
            "── END ──\n\n"
            "Return the SAME content but as a single, valid JSON object that "
            "conforms to the schema in the system prompt. Common fixes:\n"
            "  • escape every backslash inside strings (use \\\\\\\\ for one backslash)\n"
            "  • remove trailing commas before } or ]\n"
            "  • close every opened brace and bracket\n"
            "  • do not wrap the JSON in markdown fences\n"
            "  • do not add any prose before `{` or after `}`\n\n"
            "Output the corrected JSON object ONLY."
        )
        repair: GenerationResult = self._call(repair_msg, max_tokens=out_budget)
        if not repair.ok:
            return {
                "error": f"Presenter parse failed and repair LLM call failed: "
                         f"first={parsed['error']} | repair={repair.error}"
            }

        repaired = _parse_slides_json(repair.text)
        if "error" in repaired:
            return {
                "error": f"Presenter parse failed twice. "
                         f"first={parsed['error']} | repair={repaired['error']}"
            }
        # Mark that this was salvaged via repair — useful for the report.
        repaired["_repaired"] = True
        return repaired


# ─── JSON parsing (5-strategy fallback, mirrors inner_judge) ─────
def _parse_slides_json(raw: str) -> dict:
    """
    Five-strategy JSON parser, mirroring the inner-judge parser.
    Returns parsed dict on success or {'error': '...'} on failure.
    """
    if not raw or not raw.strip():
        return {"error": "Empty response"}

    # 1. direct
    try:
        return json.loads(raw)
    except Exception:
        pass

    # 2. code-fence ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # 3. greedy curly-brace block
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    # 4. trim trailing/leading non-JSON
    s = raw.strip()
    first = s.find("{")
    last = s.rfind("}")
    if first != -1 and last != -1 and last > first:
        try:
            return json.loads(s[first:last + 1])
        except Exception:
            pass

    # 5. last resort — strip Python-style trailing commas
    if first != -1 and last != -1 and last > first:
        candidate = re.sub(r",\s*([}\]])", r"\1", s[first:last + 1])
        try:
            return json.loads(candidate)
        except Exception as e:
            return {"error": f"All 5 parse strategies failed: {e}"}

    return {"error": "No JSON object found"}
