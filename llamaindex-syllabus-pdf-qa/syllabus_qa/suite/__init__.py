"""The policy test suite: one question per policy, pass/fail per question."""

from .cases import CASES, DEMO_QUESTIONS, GLOBAL_ASSERTIONS
from .run import run_suite

__all__ = ["CASES", "DEMO_QUESTIONS", "GLOBAL_ASSERTIONS", "run_suite"]
