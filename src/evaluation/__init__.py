from __future__ import annotations

from typing import Any


__all__ = ["EvaluationBundle", "JudgeVerdict", "build_test_set", "evaluate_pipeline"]


def __getattr__(name: str) -> Any:
    """Load evaluation components only when they are requested.

    Test-set generation only needs pandas. Keeping the heavier metrics/Ragas
    imports lazy prevents an optional evaluation backend from blocking it.
    """
    if name == "build_test_set":
        from .testset import build_test_set

        return build_test_set
    if name in {"EvaluationBundle", "JudgeVerdict", "evaluate_pipeline"}:
        from .metrics import EvaluationBundle, JudgeVerdict, evaluate_pipeline

        return {
            "EvaluationBundle": EvaluationBundle,
            "JudgeVerdict": JudgeVerdict,
            "evaluate_pipeline": evaluate_pipeline,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
