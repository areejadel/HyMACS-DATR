"""
slide_renderer.py — Mechanical PPTX renderer (NO AI).

This module is intentionally simple and deterministic. It takes the
slide-structured JSON produced by :class:`agents.presenter.PresenterAgent`
and emits a `.pptx` file using ``python-pptx``.

Why a *mechanical* renderer?
----------------------------
Per Section 5 of the paper, all *semantic* transformation is performed by
the model under test (via the Presenter specialist). The rendering step
must add **zero** new content — otherwise the faculty would be evaluating
"model quality × renderer quality" instead of model quality alone. Using
``python-pptx`` (a pure XML-manipulation library) preserves the cleanest
possible attribution of slide quality to the generator model.

This module:
    1. Validates the JSON against the schema constants from ``presenter``.
    2. Maps each slide ``type`` → a layout + a small set of placeholders.
    3. Writes the speaker notes verbatim into the notes_slide.
    4. Applies a single, neutral visual theme (no decorative graphics,
       no model-specific styling, no emojis, no clip-art).

Public surface:
    render_slides_json(slides_json: dict, out_path: Path | str,
                       *, topic: str | None = None) -> Path
    validate_slides_json(slides_json: dict) -> list[str]   # returns list of errors
"""
from __future__ import annotations
import io
import re
from pathlib import Path
from typing import Optional, Union

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from agents.presenter import (
    SLIDE_COUNT_MIN,
    SLIDE_COUNT_MAX,
    TITLE_MAX_WORDS,
    BULLET_MAX_WORDS,
    BULLETS_PER_CONTENT_MIN,
    BULLETS_PER_CONTENT_MAX,
    AGENDA_MIN,
    AGENDA_MAX,
    AGENDA_ITEM_MAX_WORDS,
    SPEAKER_NOTES_WORDS_MIN,
    SPEAKER_NOTES_WORDS_MAX,
    ALLOWED_TYPES,
)


# ─── Visual theme (neutral, single palette) ───────────────────────────
SLIDE_W = Inches(13.333)        # 16:9 widescreen
SLIDE_H = Inches(7.5)

COLOR_BG          = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_TITLE       = RGBColor(0x10, 0x35, 0x6F)   # deep navy
COLOR_TITLE_LIGHT = RGBColor(0x5C, 0x7A, 0xA8)   # softer navy (sub-headings)
COLOR_BODY        = RGBColor(0x21, 0x21, 0x21)   # near-black
COLOR_ACCENT      = RGBColor(0xC0, 0x39, 0x2B)   # accent (math/exercise)
COLOR_ACCENT_BG   = RGBColor(0xFD, 0xF2, 0xF0)   # tint for exercise/math wash
COLOR_AGENDA_BG   = RGBColor(0xF4, 0xF7, 0xFB)   # very light navy wash for agenda
COLOR_RULE        = RGBColor(0xCF, 0xD8, 0xDC)   # subtle separator
COLOR_NOTES       = RGBColor(0x55, 0x55, 0x55)
COLOR_BULLET_DOT  = RGBColor(0x10, 0x35, 0x6F)   # bullet glyph color

FONT_TITLE = "Calibri"
FONT_BODY  = "Calibri"
FONT_MONO  = "Consolas"

PT_TITLE_TITLESLIDE = 40
PT_SUBTITLE         = 22
PT_TITLE_CONTENT    = 30
PT_BULLET           = 22
PT_BULLET_TIGHT     = 20
PT_EQUATION         = 26
PT_CAPTION          = 16
PT_FOOTER           = 11
PT_EXERCISE         = 22

MARGIN_X = Inches(0.6)
MARGIN_TOP = Inches(0.5)
MARGIN_BOT = Inches(0.55)


# ─── Word-count helper ───────────────────────────────────────────────
_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
def _word_count(s: str) -> int:
    if not s:
        return 0
    return len(_WORD_RE.findall(s))


# ─── Schema validation ───────────────────────────────────────────────
def validate_slides_json(slides_json: dict) -> list[str]:
    """
    Return a list of human-readable validation errors.
    Empty list ⇒ JSON is fully compliant with the Presenter schema.

    NOTE: The renderer is *tolerant* — it will still attempt to render
    even if there are warnings (we report them but do not raise). This
    matches the regression-guard philosophy: don't lose work because of
    a single off-by-one bullet.
    """
    errs: list[str] = []
    if not isinstance(slides_json, dict):
        return [f"Top-level JSON must be a dict, got {type(slides_json).__name__}"]
    if "error" in slides_json:
        return [f"Slides JSON contains error: {slides_json['error']}"]

    for k in ("title", "subtitle", "slides"):
        if k not in slides_json:
            errs.append(f"missing top-level field: {k!r}")

    title = slides_json.get("title", "")
    if not isinstance(title, str) or not title.strip():
        errs.append("'title' must be non-empty string")
    elif _word_count(title) > TITLE_MAX_WORDS:
        errs.append(f"top title >'{TITLE_MAX_WORDS}' words: {_word_count(title)}")

    slides = slides_json.get("slides", [])
    if not isinstance(slides, list):
        errs.append("'slides' must be a list")
        return errs

    if len(slides) < SLIDE_COUNT_MIN or len(slides) > SLIDE_COUNT_MAX:
        errs.append(
            f"slide count {len(slides)} outside [{SLIDE_COUNT_MIN}, {SLIDE_COUNT_MAX}]"
        )

    have_math = have_exercise = have_summary = False
    for i, sl in enumerate(slides):
        if not isinstance(sl, dict):
            errs.append(f"slide[{i}] is not a dict")
            continue
        st = sl.get("type")
        if st not in ALLOWED_TYPES:
            errs.append(f"slide[{i}] has invalid type {st!r}")
        if st == "math":      have_math = True
        if st == "exercise":  have_exercise = True
        if st == "summary":   have_summary = True

        ttl = sl.get("title", "")
        if not isinstance(ttl, str) or not ttl.strip():
            errs.append(f"slide[{i}] missing title")
        elif _word_count(ttl) > TITLE_MAX_WORDS:
            errs.append(f"slide[{i}] title too long: {_word_count(ttl)} words")

        if st == "title":
            agenda = sl.get("agenda")
            if not isinstance(agenda, list) or not agenda:
                errs.append(f"slide[{i}] (title) missing 'agenda' list")
            else:
                if len(agenda) < AGENDA_MIN or len(agenda) > AGENDA_MAX:
                    errs.append(
                        f"slide[{i}] agenda has {len(agenda)} items "
                        f"(expected {AGENDA_MIN}-{AGENDA_MAX})"
                    )
                for j, a in enumerate(agenda):
                    if not isinstance(a, str) or not a.strip():
                        errs.append(f"slide[{i}].agenda[{j}] empty/non-string")
                    elif _word_count(a) > AGENDA_ITEM_MAX_WORDS:
                        errs.append(
                            f"slide[{i}].agenda[{j}] too long: "
                            f"{_word_count(a)} words "
                            f"(max {AGENDA_ITEM_MAX_WORDS})"
                        )

        if st in ("content", "summary"):
            bullets = sl.get("bullets", [])
            if not isinstance(bullets, list):
                errs.append(f"slide[{i}] 'bullets' must be a list")
            else:
                if len(bullets) < BULLETS_PER_CONTENT_MIN or len(bullets) > BULLETS_PER_CONTENT_MAX:
                    errs.append(
                        f"slide[{i}] has {len(bullets)} bullets (expected "
                        f"{BULLETS_PER_CONTENT_MIN}-{BULLETS_PER_CONTENT_MAX})"
                    )
                for j, b in enumerate(bullets):
                    if not isinstance(b, str) or not b.strip():
                        errs.append(f"slide[{i}].bullets[{j}] empty/non-string")
                        continue
                    if _word_count(b) > BULLET_MAX_WORDS:
                        errs.append(
                            f"slide[{i}].bullets[{j}] too long: "
                            f"{_word_count(b)} words"
                        )

        if st == "math":
            if not sl.get("equation_tex", "").strip():
                errs.append(f"slide[{i}] math slide missing 'equation_tex'")

        if st == "exercise":
            if not sl.get("exercise_prompt", "").strip():
                errs.append(f"slide[{i}] exercise slide missing 'exercise_prompt'")

        notes = sl.get("speaker_notes", "")
        if not isinstance(notes, str) or not notes.strip():
            errs.append(f"slide[{i}] missing speaker_notes")
        else:
            wc = _word_count(notes)
            if wc < SPEAKER_NOTES_WORDS_MIN or wc > SPEAKER_NOTES_WORDS_MAX:
                errs.append(
                    f"slide[{i}] speaker_notes {wc} words "
                    f"(expected {SPEAKER_NOTES_WORDS_MIN}-{SPEAKER_NOTES_WORDS_MAX})"
                )

    if not have_math:
        errs.append("no 'math' slide present (≥1 required)")
    if not have_exercise:
        errs.append("no 'exercise' slide present (≥1 required)")
    if not have_summary:
        errs.append("no 'summary' slide present (exactly 1 required)")
    # Structural ordering: title first, summary last
    if slides:
        if isinstance(slides[0], dict) and slides[0].get("type") != "title":
            errs.append("first slide must be type='title'")
        if isinstance(slides[-1], dict) and slides[-1].get("type") != "summary":
            errs.append("last slide must be type='summary'")
    return errs


# ─── Low-level helpers ───────────────────────────────────────────────
def _set_solid_bg(slide, color: RGBColor) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_text_box(
    slide,
    *,
    left: Emu, top: Emu, width: Emu, height: Emu,
    text: str,
    font_name: str = FONT_BODY,
    font_size: int = PT_BULLET,
    bold: bool = False,
    italic: bool = False,
    color: RGBColor = COLOR_BODY,
    align: int = PP_ALIGN.LEFT,
    anchor: int = MSO_ANCHOR.TOP,
):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)

    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return tb


def _add_bulleted_list(
    slide,
    *,
    left: Emu, top: Emu, width: Emu, height: Emu,
    bullets: list[str],
    font_size: int = PT_BULLET,
    color: RGBColor = COLOR_BODY,
):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)

    for i, b in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8)
        run = p.add_run()
        # Scrub inline LaTeX ($x$, \frac{a}{b}, etc.) → readable Unicode.
        run.text = f"•  {_scrub_inline_latex(str(b))}"
        run.font.name = FONT_BODY
        run.font.size = Pt(font_size)
        run.font.color.rgb = color
    return tb


def _add_horizontal_rule(slide, *, left: Emu, top: Emu, width: Emu) -> None:
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Emu(9525))  # ~1pt
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_RULE
    line.line.fill.background()


def _add_left_accent_bar(slide, *, color: RGBColor = COLOR_TITLE) -> None:
    """Thin colored bar down the left edge — gives every slide a consistent
    visual identity without being noisy."""
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Emu(0), Emu(0), Inches(0.18), SLIDE_H,
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()


def _add_filled_block(
    slide, *, left: Emu, top: Emu, width: Emu, height: Emu,
    color: RGBColor,
) -> None:
    block = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    block.fill.solid()
    block.fill.fore_color.rgb = color
    block.line.fill.background()


def _add_slide_header(slide, title: str, *, color: RGBColor = COLOR_TITLE) -> Emu:
    """Standard header for content/math/exercise/summary slides. Returns
    the y-coordinate just below the header (where body should start)."""
    header_top = MARGIN_TOP
    header_h = Inches(0.85)
    _add_text_box(
        slide,
        left=MARGIN_X, top=header_top,
        width=SLIDE_W - 2 * MARGIN_X, height=header_h,
        text=title,
        font_name=FONT_TITLE, font_size=PT_TITLE_CONTENT,
        bold=True, color=color, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.MIDDLE,
    )
    rule_top = header_top + header_h + Inches(0.05)
    _add_horizontal_rule(slide, left=MARGIN_X, top=rule_top, width=SLIDE_W - 2 * MARGIN_X)
    return rule_top + Inches(0.25)


def _add_footer(slide, page_num: int, total_pages: int, topic: str) -> None:
    foot_top = SLIDE_H - MARGIN_BOT + Inches(0.05)
    _add_text_box(
        slide,
        left=MARGIN_X, top=foot_top,
        width=SLIDE_W - 2 * MARGIN_X, height=Inches(0.3),
        text=f"{topic}    ·    {page_num} / {total_pages}",
        font_name=FONT_BODY, font_size=PT_FOOTER,
        color=COLOR_NOTES, align=PP_ALIGN.RIGHT,
        anchor=MSO_ANCHOR.MIDDLE,
    )


def _set_speaker_notes(slide, notes: str) -> None:
    notes_tf = slide.notes_slide.notes_text_frame
    # Scrub any inline LaTeX so the notes pane shows readable Unicode,
    # not raw \frac{...}{...}.
    notes_tf.text = _scrub_inline_latex(notes or "")


# ─── Per-type slide renderers ───────────────────────────────────────
def _render_title_slide(
    prs: Presentation, *,
    title: str, subtitle: str, agenda: list[str], speaker_notes: str,
) -> None:
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    _set_solid_bg(slide, COLOR_BG)
    _add_left_accent_bar(slide, color=COLOR_TITLE)

    # ── Title block (upper third) ────────────────────────────
    title_top = Inches(0.85)
    _add_text_box(
        slide,
        left=MARGIN_X + Inches(0.2), top=title_top,
        width=SLIDE_W - 2 * MARGIN_X - Inches(0.2), height=Inches(1.5),
        text=title,
        font_name=FONT_TITLE, font_size=PT_TITLE_TITLESLIDE,
        bold=True, color=COLOR_TITLE, align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )

    # Accent rule under title
    rule_left = SLIDE_W / 2 - Inches(1.5)
    _add_horizontal_rule(
        slide,
        left=rule_left, top=title_top + Inches(1.55),
        width=Inches(3.0),
    )

    # Subtitle directly under rule
    _add_text_box(
        slide,
        left=MARGIN_X, top=title_top + Inches(1.7),
        width=SLIDE_W - 2 * MARGIN_X, height=Inches(0.6),
        text=subtitle,
        font_name=FONT_BODY, font_size=PT_SUBTITLE,
        italic=True, color=COLOR_TITLE_LIGHT, align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )

    # ── Agenda block (lower two thirds) ──────────────────────
    if agenda:
        agenda_top = title_top + Inches(2.6)
        agenda_h   = SLIDE_H - agenda_top - Inches(0.8)
        agenda_w   = Inches(8.5)
        agenda_left = (SLIDE_W - agenda_w) // 2

        # Soft tint background
        _add_filled_block(
            slide,
            left=agenda_left, top=agenda_top,
            width=agenda_w, height=agenda_h,
            color=COLOR_AGENDA_BG,
        )

        # "In this lecture" label
        _add_text_box(
            slide,
            left=agenda_left + Inches(0.4), top=agenda_top + Inches(0.25),
            width=agenda_w - Inches(0.8), height=Inches(0.45),
            text="IN THIS LECTURE",
            font_name=FONT_BODY, font_size=13,
            bold=True, color=COLOR_TITLE,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE,
        )

        # Numbered agenda items
        items_top = agenda_top + Inches(0.85)
        items_h   = agenda_h - Inches(1.1)
        tb = slide.shapes.add_textbox(
            agenda_left + Inches(0.5), items_top,
            agenda_w - Inches(1.0), items_h,
        )
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.05)
        tf.margin_right = Inches(0.05)
        for i, item in enumerate(agenda):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            p.alignment = PP_ALIGN.LEFT
            p.space_after = Pt(8)

            # Number prefix in accent color
            r_num = p.add_run()
            r_num.text = f"{i + 1}.  "
            r_num.font.name = FONT_TITLE
            r_num.font.size = Pt(20)
            r_num.font.bold = True
            r_num.font.color.rgb = COLOR_TITLE

            # Item text (scrub any inline LaTeX)
            r_txt = p.add_run()
            r_txt.text = _scrub_inline_latex(str(item))
            r_txt.font.name = FONT_BODY
            r_txt.font.size = Pt(20)
            r_txt.font.color.rgb = COLOR_BODY

    _set_speaker_notes(slide, speaker_notes)


def _render_content_slide(
    prs: Presentation, *,
    title: str, bullets: list[str], speaker_notes: str,
    page_num: int, total_pages: int, topic: str,
) -> None:
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    _set_solid_bg(slide, COLOR_BG)
    _add_left_accent_bar(slide, color=COLOR_TITLE)

    body_top = _add_slide_header(slide, title)
    body_h = SLIDE_H - body_top - MARGIN_BOT - Inches(0.2)
    # Choose font size based on bullet count
    font_size = PT_BULLET if len(bullets) <= 4 else PT_BULLET_TIGHT
    _add_bulleted_list(
        slide,
        left=MARGIN_X + Inches(0.2), top=body_top,
        width=SLIDE_W - 2 * MARGIN_X - Inches(0.4),
        height=body_h,
        bullets=bullets,
        font_size=font_size,
    )
    _add_footer(slide, page_num, total_pages, topic)
    _set_speaker_notes(slide, speaker_notes)


# ─── LaTeX → PNG rendering for math slides ──────────────────────────
# Models emit `equation_tex` as LaTeX strings (e.g. "\\frac{\\partial L}{\\partial w}").
# Without rendering, those show up as raw backslash commands on the slide.
# We use matplotlib's mathtext (already a project dep) to rasterize each
# equation into a transparent PNG that we can drop into the slide via
# python-pptx `add_picture`. If matplotlib fails (unsupported macro, syntax
# error), we fall back to a Unicode-substituted plain-text rendering so the
# slide still has *something* meaningful instead of raw `\frac{...}` code.

_LATEX_UNICODE_FALLBACK = {
    r"\partial":   "∂",
    r"\nabla":     "∇",
    r"\cdot":      "·",
    r"\odot":      "⊙",
    r"\otimes":    "⊗",
    r"\times":     "×",
    r"\top":       "ᵀ",
    r"\to":        "→",
    r"\rightarrow":"→",
    r"\leftarrow": "←",
    r"\Rightarrow":"⇒",
    r"\leq":       "≤",
    r"\geq":       "≥",
    r"\neq":       "≠",
    r"\approx":    "≈",
    r"\sum":       "Σ",
    r"\prod":      "Π",
    r"\int":       "∫",
    r"\infty":     "∞",
    r"\alpha":     "α",
    r"\beta":      "β",
    r"\gamma":     "γ",
    r"\delta":     "δ",
    r"\epsilon":   "ε",
    r"\zeta":      "ζ",
    r"\eta":       "η",
    r"\theta":     "θ",
    r"\lambda":    "λ",
    r"\mu":        "μ",
    r"\pi":        "π",
    r"\rho":       "ρ",
    r"\sigma":     "σ",
    r"\tau":       "τ",
    r"\phi":       "φ",
    r"\psi":       "ψ",
    r"\omega":     "ω",
    r"\Gamma":     "Γ",
    r"\Delta":     "Δ",
    r"\Theta":     "Θ",
    r"\Lambda":    "Λ",
    r"\Sigma":     "Σ",
    r"\Phi":       "Φ",
    r"\Omega":     "Ω",
}


def _strip_outer_math_delims(s: str) -> str:
    """Strip $...$, $$...$$, \\(...\\), \\[...\\] outer delimiters."""
    s = s.strip()
    if s.startswith("$$") and s.endswith("$$"):
        s = s[2:-2].strip()
    elif s.startswith("$") and s.endswith("$"):
        s = s[1:-1].strip()
    elif s.startswith(r"\[") and s.endswith(r"\]"):
        s = s[2:-2].strip()
    elif s.startswith(r"\(") and s.endswith(r"\)"):
        s = s[2:-2].strip()
    return s


def _split_tex_lines(tex: str) -> list[str]:
    """
    LaTeX `\\\\` is a line break inside math; mathtext does not support it,
    so we split on it and render each line independently.
    """
    parts = re.split(r"\\\\\s*", tex)
    out = [p.strip() for p in parts if p and p.strip()]
    return out or [tex.strip()]


def _latex_to_unicode_fallback(tex: str) -> str:
    """
    Cheap LaTeX → readable Unicode conversion. Used only when matplotlib
    rendering fails. Not a full LaTeX implementation — just enough to make
    raw `\frac{a}{b}` look like `(a)/(b)` and Greek letters render properly.
    """
    s = tex
    # \frac{a}{b} → (a)/(b)
    for _ in range(4):  # nested fracs — apply a few passes
        s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    # \sqrt{a} → √(a)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    # \mathbf{x} / \mathcal{X} / \boldsymbol{x} / \mathrm{x} → x
    s = re.sub(r"\\(?:mathbf|mathcal|mathrm|boldsymbol|bm|vec|hat|tilde|bar)\{([^{}]*)\}", r"\1", s)
    # _{...} → _... ; ^{...} → ^...
    s = re.sub(r"_\{([^{}]+)\}", r"_\1", s)
    s = re.sub(r"\^\{([^{}]+)\}", r"^\1", s)
    # Greek/operator commands
    for k, v in sorted(_LATEX_UNICODE_FALLBACK.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)
    # Strip remaining backslashes from unknown commands
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = s.replace("{", "").replace("}", "")
    return s.strip()


# ─── Inline LaTeX cleanup for non-equation text ──────────────────────
# Bullets / agenda items / exercise prompts / speaker notes routinely
# contain inline math like  "Compute $\frac{\partial L}{\partial w_l}$".
# We don't want to rasterize every bullet to PNG (too brittle, layout
# nightmare), so instead we scrub them: convert any $...$, \(...\),
# \[...\], or bare \cmd inside the string to a readable Unicode
# equivalent using the same fallback as math slides.
_INLINE_MATH_PATTERNS = [
    (re.compile(r"\$\$([^$]+?)\$\$",       re.DOTALL), 1),
    (re.compile(r"\$([^$\n]+?)\$",         re.DOTALL), 1),
    (re.compile(r"\\\[(.+?)\\\]",          re.DOTALL), 1),
    (re.compile(r"\\\((.+?)\\\)",          re.DOTALL), 1),
]


def _scrub_inline_latex(text: str) -> str:
    """
    Convert any inline LaTeX inside a non-equation string into readable
    Unicode. Idempotent and forgiving — if no LaTeX is present, returns
    the string unchanged.
    """
    if not text or not isinstance(text, str):
        return text
    s = text
    # 1. Inline-math regions ($...$, \(..\), \[..\])
    for pat, _ in _INLINE_MATH_PATTERNS:
        s = pat.sub(lambda m: _latex_to_unicode_fallback(m.group(1)), s)
    # 2. Bare LaTeX commands outside math delimiters (defensive — some
    #    models forget the dollar signs entirely, e.g. "compute \frac{a}{b}")
    if "\\" in s:
        s = _latex_to_unicode_fallback(s)
    return s


def _scrub_inline_latex_in_list(items: list) -> list:
    return [_scrub_inline_latex(str(x)) if x is not None else "" for x in items]


def _render_latex_to_png_bytes(
    tex: str,
    *,
    fontsize: int = 28,
    color_hex: str = "#103569",
    dpi: int = 200,
) -> Optional[bytes]:
    """
    Render a LaTeX math expression (or multi-line equation separated by
    `\\\\`) to PNG bytes via matplotlib. Returns None on failure.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    cleaned = _strip_outer_math_delims(tex.strip())
    lines = _split_tex_lines(cleaned)
    if not lines:
        return None

    # Compose one mathtext block, one $...$ per line joined with newlines.
    body = "\n".join(f"${ln}$" for ln in lines)

    # Heuristic figure size — height grows with line count.
    n_lines = len(lines)
    fig_w = 12.0
    fig_h = max(0.9 * n_lines + 0.4, 1.2)

    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_alpha(0.0)
    try:
        fig.text(
            0.5, 0.5, body,
            ha="center", va="center",
            fontsize=fontsize, color=color_hex,
        )
        buf = io.BytesIO()
        fig.savefig(
            buf, format="png",
            bbox_inches="tight", pad_inches=0.15,
            transparent=True,
        )
        buf.seek(0)
        data = buf.read()
    except Exception:
        data = None
    finally:
        plt.close(fig)
    return data


def _render_math_slide(
    prs: Presentation, *,
    title: str, equation_tex: str, equation_caption: str,
    speaker_notes: str,
    page_num: int, total_pages: int, topic: str,
    bullets: Optional[list] = None,   # fallback if equation_tex is empty
) -> None:
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    _set_solid_bg(slide, COLOR_BG)
    _add_left_accent_bar(slide, color=COLOR_TITLE)

    body_top = _add_slide_header(slide, title, color=COLOR_TITLE)

    # ── Tolerant content resolution ──
    # Many models put the equation in bullets instead of equation_tex.
    # Accept whatever source is available without altering the content.
    bullets = [b for b in (bullets or []) if str(b).strip()]
    eq_text = (equation_tex or "").strip()
    extra_bullets: list[str] = []
    if not eq_text and bullets:
        eq_text = str(bullets[0]).strip()
        extra_bullets = [str(b).strip() for b in bullets[1:]]
    elif eq_text and bullets:
        extra_bullets = [str(b).strip() for b in bullets]

    # Equation: render via matplotlib mathtext if it's LaTeX-shaped; else
    # fall back to plain text. We treat the input as LaTeX whenever it
    # contains a backslash command or sub/super-script, which covers all
    # outputs from current models.
    eq_h = Inches(2.4)
    eq_top = body_top + Inches(0.3)
    eq_left = MARGIN_X + Inches(0.6)
    eq_width = SLIDE_W - 2 * MARGIN_X - Inches(1.2)

    def _looks_like_latex(s: str) -> bool:
        return bool(re.search(r"\\[a-zA-Z]+|[\^_]\{|\\\\", s)) or "$" in s

    if eq_text:
        png_bytes: Optional[bytes] = None
        if _looks_like_latex(eq_text):
            png_bytes = _render_latex_to_png_bytes(
                eq_text,
                fontsize=28,
                color_hex="#103569",   # COLOR_TITLE in hex
                dpi=200,
            )
        if png_bytes:
            try:
                pic = slide.shapes.add_picture(
                    io.BytesIO(png_bytes),
                    eq_left, eq_top,
                    width=eq_width,
                )
                # If matplotlib produced something taller than our slot,
                # python-pptx scaled by width and the height may overflow;
                # cap it so the caption still fits.
                max_h = Inches(2.8)
                if pic.height > max_h:
                    scale = max_h / pic.height
                    pic.width = int(pic.width * scale)
                    pic.height = max_h
                    pic.left = eq_left + (eq_width - pic.width) // 2
            except Exception:
                # Picture insert failed — degrade to text.
                png_bytes = None

        if not png_bytes:
            # Text fallback — replace common LaTeX with Unicode so the
            # slide still reads as math instead of `\frac{a}{b}`.
            display_eq = (
                _latex_to_unicode_fallback(_strip_outer_math_delims(eq_text))
                if _looks_like_latex(eq_text) else eq_text
            )
            _add_text_box(
                slide,
                left=eq_left, top=eq_top,
                width=eq_width, height=eq_h,
                text=display_eq,
                font_name=FONT_MONO, font_size=PT_EQUATION,
                bold=False, color=COLOR_ACCENT,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
            )

    caption = _scrub_inline_latex((equation_caption or "").strip())
    cap_top = eq_top + eq_h + Inches(0.1)
    if caption:
        _add_text_box(
            slide,
            left=MARGIN_X + Inches(0.6), top=cap_top,
            width=SLIDE_W - 2 * MARGIN_X - Inches(1.2), height=Inches(0.8),
            text=caption,
            font_name=FONT_BODY, font_size=PT_CAPTION,
            italic=True, color=COLOR_NOTES,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP,
        )
        cap_top = cap_top + Inches(0.9)

    # Extra bullets (sub-explanations) below equation
    if extra_bullets:
        list_h = SLIDE_H - cap_top - MARGIN_BOT - Inches(0.4)
        if list_h > Inches(0.6):
            _add_bulleted_list(
                slide,
                left=MARGIN_X + Inches(0.4), top=cap_top + Inches(0.1),
                width=SLIDE_W - 2 * MARGIN_X - Inches(0.8),
                height=list_h,
                bullets=extra_bullets,
                font_size=PT_BULLET_TIGHT,
            )

    _add_footer(slide, page_num, total_pages, topic)
    _set_speaker_notes(slide, speaker_notes)


def _render_exercise_slide(
    prs: Presentation, *,
    title: str, exercise_prompt: str, speaker_notes: str,
    page_num: int, total_pages: int, topic: str,
    bullets: Optional[list] = None,   # fallback if exercise_prompt is empty
) -> None:
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    _set_solid_bg(slide, COLOR_BG)
    _add_left_accent_bar(slide, color=COLOR_ACCENT)

    body_top = _add_slide_header(slide, title, color=COLOR_ACCENT)

    # "Try this" tag
    _add_text_box(
        slide,
        left=MARGIN_X + Inches(0.2), top=body_top,
        width=Inches(2.5), height=Inches(0.5),
        text="▶ TRY THIS",
        font_name=FONT_BODY, font_size=14,
        bold=True, color=COLOR_ACCENT,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE,
    )

    # ── Tolerant content resolution ──
    # Many models put the exercise in bullets instead of exercise_prompt.
    # Scrub any inline LaTeX ($x$, \frac{a}{b}, etc.) to readable Unicode.
    bullets = [_scrub_inline_latex(str(b).strip())
               for b in (bullets or []) if str(b).strip()]
    prompt_text = _scrub_inline_latex((exercise_prompt or "").strip())

    body_left = MARGIN_X + Inches(0.2)
    body_w    = SLIDE_W - 2 * MARGIN_X - Inches(0.4)
    body_y    = body_top + Inches(0.55)
    body_h    = SLIDE_H - body_y - MARGIN_BOT - Inches(0.3)

    if prompt_text and not bullets:
        # case: one long prompt
        _add_text_box(
            slide,
            left=body_left, top=body_y,
            width=body_w, height=body_h,
            text=prompt_text,
            font_name=FONT_BODY, font_size=PT_EXERCISE,
            color=COLOR_BODY,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
        )
    elif bullets and not prompt_text:
        # case: the exercise is given as bullets
        font_size = PT_EXERCISE if len(bullets) <= 4 else PT_BULLET_TIGHT
        _add_bulleted_list(
            slide,
            left=body_left, top=body_y,
            width=body_w, height=body_h,
            bullets=bullets, font_size=font_size,
        )
    elif prompt_text and bullets:
        # mixed case: prompt as a sub-heading + steps as bullets
        prompt_h = Inches(1.0)
        _add_text_box(
            slide,
            left=body_left, top=body_y,
            width=body_w, height=prompt_h,
            text=prompt_text,
            font_name=FONT_BODY, font_size=PT_EXERCISE,
            color=COLOR_BODY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
        )
        list_y = body_y + prompt_h + Inches(0.1)
        list_h = SLIDE_H - list_y - MARGIN_BOT - Inches(0.3)
        font_size = PT_BULLET if len(bullets) <= 4 else PT_BULLET_TIGHT
        _add_bulleted_list(
            slide,
            left=body_left, top=list_y,
            width=body_w, height=list_h,
            bullets=bullets, font_size=font_size,
        )
    # otherwise fully empty — leave it with the title only

    _add_footer(slide, page_num, total_pages, topic)
    _set_speaker_notes(slide, speaker_notes)


def _render_summary_slide(
    prs: Presentation, *,
    title: str, bullets: list[str], speaker_notes: str,
    page_num: int, total_pages: int, topic: str,
) -> None:
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    _set_solid_bg(slide, COLOR_BG)
    _add_left_accent_bar(slide, color=COLOR_TITLE)

    body_top = _add_slide_header(slide, title, color=COLOR_TITLE)

    # ── Soft tinted block to frame the takeaways ──
    block_left = MARGIN_X + Inches(0.2)
    block_w    = SLIDE_W - 2 * MARGIN_X - Inches(0.4)
    block_top  = body_top
    block_h    = SLIDE_H - body_top - MARGIN_BOT - Inches(0.4)
    _add_filled_block(
        slide,
        left=block_left, top=block_top,
        width=block_w, height=block_h,
        color=COLOR_AGENDA_BG,
    )

    # ── "Key takeaways" sub-label ──
    _add_text_box(
        slide,
        left=block_left + Inches(0.4), top=block_top + Inches(0.25),
        width=Inches(6.0), height=Inches(0.45),
        text="KEY TAKEAWAYS",
        font_name=FONT_BODY, font_size=13,
        bold=True, color=COLOR_TITLE,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE,
    )

    # ── Numbered takeaways (mirror title-slide agenda style) ──
    items_top = block_top + Inches(0.95)
    items_h   = block_h - Inches(1.2)
    tb = slide.shapes.add_textbox(
        block_left + Inches(0.5), items_top,
        block_w - Inches(1.0), items_h,
    )
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    font_size = 22 if len(bullets) <= 4 else 20
    for i, b in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8)
        r_num = p.add_run()
        r_num.text = f"{i + 1}.  "
        r_num.font.name = FONT_TITLE
        r_num.font.size = Pt(font_size)
        r_num.font.bold = True
        r_num.font.color.rgb = COLOR_TITLE
        r_txt = p.add_run()
        r_txt.text = _scrub_inline_latex(str(b))
        r_txt.font.name = FONT_BODY
        r_txt.font.size = Pt(font_size)
        r_txt.font.color.rgb = COLOR_BODY

    _add_footer(slide, page_num, total_pages, topic)
    _set_speaker_notes(slide, speaker_notes)


# ─── Public entry point ─────────────────────────────────────────────
def render_slides_json(
    slides_json: dict,
    out_path: Union[Path, str],
    *,
    topic: Optional[str] = None,
    strict: bool = False,
) -> Path:
    """
    Render the slide-structured JSON to a .pptx file.

    Args:
        slides_json: dict produced by :meth:`PresenterAgent.structure`.
        out_path:    destination .pptx path (will be created/overwritten).
        topic:       footer label; defaults to slides_json['title'].
        strict:      if True, raise ValueError on any validation error.
                     Otherwise validation errors are returned alongside
                     the rendered file (and printed to stdout).

    Returns:
        Path to the written .pptx file.

    Raises:
        ValueError if the JSON is unrenderable (missing/invalid 'slides'
        list, or schema errors when ``strict=True``).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    errors = validate_slides_json(slides_json)
    fatal = (
        not isinstance(slides_json, dict)
        or not isinstance(slides_json.get("slides"), list)
        or not slides_json.get("slides")
    )
    if fatal:
        raise ValueError(
            f"Cannot render slides: {'; '.join(errors) or 'no slides'}"
        )
    if errors and strict:
        raise ValueError("Slide JSON validation errors: " + "; ".join(errors))
    if errors:
        # Non-fatal — log but proceed.
        print(f"[slide_renderer] {len(errors)} validation warning(s):")
        for e in errors:
            print(f"   • {e}")

    slides        = slides_json.get("slides", [])
    # ── Tolerant deck-title resolution ──────────────────────
    # Many models put title/subtitle inside slide[0] instead of at the
    # top level (it's redundant). Fall back gracefully so we don't
    # render "Lecture" as the deck title.
    deck_title = slides_json.get("title", "").strip()
    deck_subtitle = slides_json.get("subtitle", "").strip()
    if (not deck_title or not deck_subtitle) and slides and isinstance(slides[0], dict):
        first = slides[0]
        if not deck_title:
            deck_title = (first.get("title") or "").strip() or "Lecture"
        if not deck_subtitle:
            deck_subtitle = (first.get("subtitle") or "").strip()
    deck_title = deck_title or "Lecture"
    footer_topic  = topic or deck_title

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    total_pages = len(slides)
    for i, sl in enumerate(slides):
        st = sl.get("type", "content")
        page_num = i + 1
        title  = sl.get("title", "")
        notes  = sl.get("speaker_notes", "")
        try:
            if st == "title":
                _render_title_slide(
                    prs,
                    title=title or deck_title,
                    subtitle=sl.get("subtitle", deck_subtitle),
                    agenda=sl.get("agenda", []) or [],
                    speaker_notes=notes,
                )
            elif st == "content":
                _render_content_slide(
                    prs,
                    title=title,
                    bullets=sl.get("bullets", []),
                    speaker_notes=notes,
                    page_num=page_num, total_pages=total_pages,
                    topic=footer_topic,
                )
            elif st == "math":
                _render_math_slide(
                    prs,
                    title=title,
                    equation_tex=sl.get("equation_tex", ""),
                    equation_caption=sl.get("equation_caption", ""),
                    speaker_notes=notes,
                    page_num=page_num, total_pages=total_pages,
                    topic=footer_topic,
                    bullets=sl.get("bullets") or [],
                )
            elif st == "exercise":
                _render_exercise_slide(
                    prs,
                    title=title,
                    exercise_prompt=sl.get("exercise_prompt", ""),
                    speaker_notes=notes,
                    page_num=page_num, total_pages=total_pages,
                    topic=footer_topic,
                    bullets=sl.get("bullets") or [],
                )
            elif st == "summary":
                _render_summary_slide(
                    prs,
                    title=title,
                    bullets=sl.get("bullets", []),
                    speaker_notes=notes,
                    page_num=page_num, total_pages=total_pages,
                    topic=footer_topic,
                )
            else:
                # Unknown type → render as content
                _render_content_slide(
                    prs,
                    title=title or f"Slide {page_num}",
                    bullets=sl.get("bullets", [str(sl)[:200]]),
                    speaker_notes=notes,
                    page_num=page_num, total_pages=total_pages,
                    topic=footer_topic,
                )
        except Exception as e:
            print(f"[slide_renderer] WARN: slide {page_num} ({st}) failed: {e}")
            continue

    prs.save(str(out_path))
    return out_path


# ─── CLI for ad-hoc testing ─────────────────────────────────────────
if __name__ == "__main__":
    import argparse, json, sys
    ap = argparse.ArgumentParser(description="Render slide JSON → PPTX.")
    ap.add_argument("input_json", help="path to slide JSON file")
    ap.add_argument("output_pptx", help="path to write .pptx")
    ap.add_argument("--topic", default=None)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        sj = json.load(f)
    out = render_slides_json(sj, args.output_pptx, topic=args.topic, strict=args.strict)
    print(f"wrote {out}")
