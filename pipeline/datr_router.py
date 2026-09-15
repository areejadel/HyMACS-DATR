"""
datr_router.py — DATR (Dimension-Aware Targeted Refinement)

Takes scores from inner_judge and decides:
    1. Is refinement needed at all? (if overall >= QUALITY_THRESHOLD -> stop)
    2. Which dimension(s) are weakest? (sort ascending, take the worst k)
    3. Is there a regression? (if a dim dropped > REGRESSION_TOLERANCE from the previous round)
"""
from __future__ import annotations
from dataclasses import dataclass

from config import (
    RUBRIC_DIMENSIONS,
    QUALITY_THRESHOLD,
    REGRESSION_TOLERANCE,
)


@dataclass
class DATRDecision:
    should_continue: bool                    # continue refining?
    target_dimensions: list[str]             # the weak dimensions
    weakest_score: float
    overall: float
    reason: str                              # decision explanation for logging


class DATRRouter:
    """DATR routing logic + regression guard."""

    def __init__(
        self,
        quality_threshold: float = QUALITY_THRESHOLD,
        regression_tolerance: float = REGRESSION_TOLERANCE,
        top_k_weakest: int = 2,                 # how many dimensions to improve per round
    ):
        self.quality_threshold = quality_threshold
        self.regression_tolerance = regression_tolerance
        self.top_k = top_k_weakest

    def decide(self, evaluation: dict, max_reached: bool = False) -> DATRDecision:
        """
        Args:
            evaluation: output from InnerJudge.evaluate()
            max_reached: have we reached MAX_ITERATIONS?
        """
        scores = evaluation["scores"]
        overall = evaluation.get("overall", 0.0)

        # 1) if we reached max_iterations
        if max_reached:
            return DATRDecision(
                should_continue=False,
                target_dimensions=[],
                weakest_score=min(scores.values()) if scores else 0.0,
                overall=overall,
                reason="max_iterations reached",
            )

        # 2) if quality is excellent -> stop
        if overall >= self.quality_threshold:
            return DATRDecision(
                should_continue=False,
                target_dimensions=[],
                weakest_score=min(scores.values()) if scores else 0.0,
                overall=overall,
                reason=f"overall ({overall:.2f}) >= threshold ({self.quality_threshold})",
            )

        # 3) sort the dimensions ascending (weakest first)
        sorted_dims = sorted(
            RUBRIC_DIMENSIONS,
            key=lambda d: scores.get(d, 0.0),
        )
        weakest = sorted_dims[: self.top_k]
        weakest_score = scores.get(weakest[0], 0.0) if weakest else 0.0

        return DATRDecision(
            should_continue=True,
            target_dimensions=weakest,
            weakest_score=weakest_score,
            overall=overall,
            reason=f"targeting weakest {self.top_k}: {weakest} (score={weakest_score:.2f})",
        )

    def check_regression(
        self,
        prior_scores: dict,
        new_scores: dict,
        target_dimensions: list[str],
    ) -> tuple[bool, list[str]]:
        """
        Regression guard: did any dimension drop > tolerance from the previous round?

        Returns:
            (should_rollback, regressed_dimensions)
        """
        regressed = []
        for dim in RUBRIC_DIMENSIONS:
            old = prior_scores.get(dim, 0.0)
            new = new_scores.get(dim, 0.0)
            drop = old - new
            if drop > self.regression_tolerance:
                regressed.append(dim)

        # roll back only if the regression hit a dimension that was NOT targeted (collateral damage)
        non_target_regression = [d for d in regressed if d not in target_dimensions]

        if non_target_regression:
            return True, non_target_regression

        # no rollback if the regression is confined to the targeted dimensions (somewhat expected)
        return False, regressed
