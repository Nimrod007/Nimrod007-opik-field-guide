"""A deterministic cousin of the judge's "no invented numbers" assertion."""

import re

import opik

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_in(text: str) -> set[str]:
    return {m.group().rstrip(",.").replace(",", "") for m in _NUMBER.finditer(text)}


# type="guardrail" makes this its own span with a distinct icon: it nests under the
# suite's evaluation_task trace, with the answer as input and the flagged numbers as output.
@opik.track(type="guardrail", name="citation_guard")
def unsupported_numbers(answer: str, excerpts: list[str]) -> list[str]:
    """Numbers that appear in the answer but in none of the retrieved excerpts."""
    return sorted(numbers_in(answer) - numbers_in(" ".join(excerpts)))
