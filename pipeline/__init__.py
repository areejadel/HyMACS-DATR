"""
pipeline/ — orchestration layer for HyMACS.

Execution flow:
    LectureGenerator(model_key, agents) -> initial draft
    InnerJudge.evaluate(draft)          -> 8-dim scores + feedback
    DATRRouter.decide(scores)           -> which dimensions need refinement
    LectureGenerator.refine(...)        -> revised draft
    [loop until convergence or max_iters]
    ExternalJudge.evaluate(final)       -> independent validation
"""
from pipeline.generator     import LectureGenerator
from pipeline.inner_judge   import InnerJudge
from pipeline.datr_router   import DATRRouter
from pipeline.external_judge import ExternalJudge
from pipeline.runner        import run_single, RunResult, IterationRecord
from pipeline.slide_renderer import render_slides_json, validate_slides_json

__all__ = [
    "LectureGenerator", "InnerJudge", "DATRRouter", "ExternalJudge",
    "run_single", "RunResult", "IterationRecord",
    "render_slides_json", "validate_slides_json",
]
