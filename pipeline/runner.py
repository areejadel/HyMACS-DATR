"""
runner.py — runs a single experiment (model × condition × seed).

Execution flow:
    1. LectureGenerator.initial_draft()
    2. InnerJudge.evaluate() -> scores + feedback
    3. depending on the condition:
       - no_refine     : stop
       - self_refine   : refine_self() up to max_iterations
       - datr_no_guard : refine_datr() up to max_iterations or the quality threshold
       - datr_full     : datr + regression guard (rollback if a dim dropped)
    4. ExternalJudge.evaluate() on the final lecture
    5. save everything to JSON
"""
from __future__ import annotations
import copy
import os
import json
import time
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import (
    MAX_ITERATIONS,
    QUALITY_THRESHOLD,
    RUBRIC_DIMENSIONS,
    RESULTS_DIR,
    USE_PANEL,
    RAG_ENABLED,
)
from pipeline.generator import LectureGenerator
from pipeline.inner_judge import InnerJudge
from pipeline.datr_router import DATRRouter, DATRDecision
from pipeline.external_judge import ExternalJudge
from pipeline.judge_panel import JudgePanel
from agents.presenter import PresenterAgent
from clients import get_client


@dataclass
class IterationRecord:
    iteration: int
    lecture: str
    inner_scores: dict           # 8 dimensions
    inner_overall: float
    inner_justifications: dict
    inner_suggestions: dict
    target_dimensions: list[str] = field(default_factory=list)
    agents_called: list[str] = field(default_factory=list)
    rolled_back: bool = False
    elapsed_sec: float = 0.0


@dataclass
class RunResult:
    """Result of a single run."""
    run_id: str
    model_key: str
    condition: str
    seed: int
    timestamp: str
    iterations: list[IterationRecord] = field(default_factory=list)
    final_lecture: str = ""
    final_inner_scores: dict = field(default_factory=dict)
    final_inner_overall: float = 0.0
    external_scores: dict = field(default_factory=dict)       # = the median if panel, else the single judge
    external_overall: float = 0.0
    external_justifications: dict = field(default_factory=dict)
    # Judge panel — each judge's score kept separately (for agreement alpha and the self-preference matrix)
    panel_per_judge: dict = field(default_factory=dict)
    panel_n_ok: int = 0
    final_slides_json: dict = field(default_factory=dict)
    slides_validation_warnings: list[str] = field(default_factory=list)
    total_elapsed_sec: float = 0.0
    error: Optional[str] = None

    def to_json(self) -> dict:
        d = asdict(self)
        return d


def run_single(
    model_key: str,
    condition: str,
    seed: int,
    save: bool = True,
    verbose: bool = True,
) -> RunResult:
    """
    Runs a single experiment and returns a RunResult.
    """
    run_id = f"{model_key}__{condition}__seed{seed}__{int(time.time())}"
    result = RunResult(
        run_id=run_id,
        model_key=model_key,
        condition=condition,
        seed=seed,
        timestamp=datetime.utcnow().isoformat(),
    )

    random.seed(seed)
    t_start = time.time()

    try:
        if verbose:
            print(f"\n{'='*70}")
            print(f"  RUN: {run_id}")
            print(f"{'='*70}")

        # ─── Setup ────────────────────────────────────
        retriever = None
        if RAG_ENABLED:
            from pipeline.rag import get_retriever
            retriever = get_retriever()          # singleton — built once per topic
        gen = LectureGenerator(model_key, retriever=retriever)
        inner = InnerJudge()
        external = JudgePanel() if USE_PANEL else ExternalJudge()
        router = DATRRouter()

        # ─── Round 0: initial draft ──────────────────
        if verbose:
            print(f"  [Round 0] generating initial draft...")
        t0 = time.time()
        lecture = gen.initial_draft()
        eval0 = inner.evaluate(lecture)
        if eval0.get("error"):
            result.error = f"Inner judge round 0 failed: {eval0['error']}"
            return _finalize(result, t_start, save)

        result.iterations.append(IterationRecord(
            iteration=0,
            lecture=lecture,
            inner_scores=eval0["scores"],
            inner_overall=eval0["overall"],
            inner_justifications=eval0["justifications"],
            inner_suggestions=eval0["suggestions"],
            target_dimensions=[],
            agents_called=["sme", "pedagogy", "clarity", "engagement"],
            elapsed_sec=time.time() - t0,
        ))

        if verbose:
            print(f"    initial overall: {eval0['overall']:.2f}")
            print(f"    weakest dims: {sorted(eval0['scores'].items(), key=lambda x: x[1])[:3]}")

        # ─── Refinement rounds (depending on condition) ──────
        if condition != "no_refine":
            for it in range(1, MAX_ITERATIONS + 1):
                prior_record = result.iterations[-1]
                prior_lecture = prior_record.lecture
                prior_scores = prior_record.inner_scores
                prior_eval = {
                    "scores": prior_scores,
                    "overall": prior_record.inner_overall,
                    "justifications": prior_record.inner_justifications,
                    "suggestions": prior_record.inner_suggestions,
                }

                # continue?
                decision = router.decide(
                    prior_eval,
                    max_reached=(it > MAX_ITERATIONS),
                )
                if not decision.should_continue:
                    if verbose:
                        print(f"  [stop] {decision.reason}")
                    break

                if verbose:
                    print(f"  [Round {it}] {decision.reason}")

                t_iter = time.time()
                feedback = inner.feedback_for_agents(prior_eval)

                # choose the refinement strategy
                if condition == "self_refine":
                    new_lecture = gen.refine_self(prior_lecture, feedback)
                    agents_called = ["sme", "pedagogy", "clarity", "engagement"]
                    target_dims = []
                elif condition in ("datr_no_guard", "datr_full"):
                    new_lecture, agents_called = gen.refine_datr(
                        prior_lecture,
                        decision.target_dimensions,
                        feedback,
                    )
                    target_dims = decision.target_dimensions
                else:
                    raise ValueError(f"Unknown condition: {condition}")

                # evaluate the new lecture
                new_eval = inner.evaluate(new_lecture)
                if new_eval.get("error"):
                    if verbose:
                        print(f"    inner judge failed at iter {it}: {new_eval['error']}")
                    break

                rolled_back = False
                # Regression guard (datr_full only)
                if condition == "datr_full":
                    should_rollback, regressed = router.check_regression(
                        prior_scores, new_eval["scores"], target_dims
                    )
                    if should_rollback:
                        if verbose:
                            print(f"    [!] rollback! regressed dims: {regressed}")
                        # keep the old version (do not record the update in final)
                        new_lecture = prior_lecture
                        new_eval = prior_eval
                        rolled_back = True

                result.iterations.append(IterationRecord(
                    iteration=it,
                    lecture=new_lecture,
                    inner_scores=new_eval["scores"],
                    inner_overall=new_eval["overall"],
                    inner_justifications=new_eval.get("justifications", {}),
                    inner_suggestions=new_eval.get("suggestions", {}),
                    target_dimensions=target_dims,
                    agents_called=agents_called,
                    rolled_back=rolled_back,
                    elapsed_sec=time.time() - t_iter,
                ))

                if verbose:
                    print(f"    new overall: {new_eval['overall']:.2f} ({'rolled back' if rolled_back else 'accepted'})")

        # ─── Final lecture = last iteration ───────────
        final = result.iterations[-1]
        result.final_lecture = final.lecture
        result.final_inner_scores = final.inner_scores
        result.final_inner_overall = final.inner_overall

        # ─── External evaluation (judge panel -> median) ──────
        if verbose:
            mode = "panel (median of 3)" if USE_PANEL else "single Claude judge"
            print(f"  [external] {mode} evaluating...")
        ext_eval = external.evaluate(result.final_lecture)
        if ext_eval.get("error"):
            result.error = f"External evaluation failed: {ext_eval['error']}"
        elif USE_PANEL:
            # JudgePanel -> median_scores + per_judge
            result.external_scores = ext_eval["median_scores"]
            result.external_overall = ext_eval["overall"]
            result.panel_per_judge = ext_eval.get("per_judge", {})
            result.panel_n_ok = ext_eval.get("n_ok", 0)
        else:
            # single ExternalJudge
            result.external_scores = ext_eval["scores"]
            result.external_overall = ext_eval["overall"]
            result.external_justifications = ext_eval.get("justifications", {})

        if verbose:
            print(f"    inner final  : {result.final_inner_overall:.2f}")
            print(f"    external     : {result.external_overall:.2f}")

        # ─── Presenter: structure final lecture into slides ──────
        # Same generator model, no external AI — preserves attribution.
        if result.final_lecture and not result.error:
            if verbose:
                print(f"  [presenter] structuring lecture into slides...")
            try:
                presenter = PresenterAgent(get_client(model_key))
                slides_json = presenter.structure(result.final_lecture)
                result.final_slides_json = slides_json
                # Lazy-import to avoid a circular import at module load.
                from pipeline.slide_renderer import validate_slides_json
                warnings = validate_slides_json(slides_json)
                result.slides_validation_warnings = warnings
                if verbose:
                    if "error" in slides_json:
                        print(f"    presenter parse failed: {slides_json['error']}")
                    else:
                        n_slides = len(slides_json.get("slides", []))
                        print(f"    structured into {n_slides} slides "
                              f"({len(warnings)} validation warning(s))")
            except Exception as pe:
                # Don't let Presenter failure tank the run — slides are
                # an additive output, not part of the core RQ scoring.
                result.final_slides_json = {"error": f"{type(pe).__name__}: {pe}"}
                if verbose:
                    print(f"    presenter raised: {pe}")

    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"
        if verbose:
            print(f"  [x] EXCEPTION: {result.error}")

    return _finalize(result, t_start, save)


def result_filename(model_key: str, condition: str, seed: int) -> str:
    """Deterministic filename (no timestamp) per (model, condition, seed).
    => re-running overwrites the same file instead of creating duplicates."""
    return f"{model_key}__{condition}__seed{seed}.json"


def _finalize(result: RunResult, t_start: float, save: bool) -> RunResult:
    result.total_elapsed_sec = time.time() - t_start
    if save:
        out_dir = Path(RESULTS_DIR) / "runs"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / result_filename(result.model_key, result.condition, result.seed)
        # Atomic write: write to a temp file then replace — if power/credit is
        # interrupted mid-write, the old file stays intact and a half-written file is never produced.
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(result.to_json(), f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)   # atomic on the same filesystem
    return result
