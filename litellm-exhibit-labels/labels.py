"""Exhibit-label prompts and the comparison table, independent of any provider."""

import json
import statistics
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).parent / "data" / "artifacts.json"
WORD_LIMIT = 60

# Short model name -> LiteLLM model string. Adding a provider is one more line.
MODELS = {
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "claude-haiku-4-5": "anthropic/claude-haiku-4-5-20251001",
}


@dataclass
class Call:
    """What one completion cost, as seen from the response."""

    model: str
    artifact_id: str
    latency_s: float
    cost_usd: float
    tokens: int
    words: int


def load_artifacts(path: Path = DATA) -> list[dict]:
    return json.loads(path.read_text())


def build_prompt(artifact: dict, word_limit: int = WORD_LIMIT) -> str:
    facts = "\n".join(f"- {fact}" for fact in artifact["facts"])
    return (
        f"Write a museum wall label for this {artifact['kind']} in the Hall of "
        f"Deep Time. Use at most {word_limit} words, a one-line title, and a "
        f"warm, plain tone for visitors aged ten and up.\n\n"
        f"Object: {artifact['name']}\n"
        f"Period: {artifact['period']}\n"
        f"Found at: {artifact['found']}\n"
        f"Facts:\n{facts}\n\n"
        "Use only the facts above; do not invent dates or names."
    )


def word_count(text: str) -> int:
    return len(text.split())


def summarize(calls: list[Call]) -> list[dict]:
    """One row per model: totals and means over its calls."""
    rows = []
    for model in dict.fromkeys(c.model for c in calls):
        mine = [c for c in calls if c.model == model]
        rows.append(
            {
                "model": model,
                "labels": len(mine),
                "tokens": sum(c.tokens for c in mine),
                "cost": sum(c.cost_usd for c in mine),
                "latency": statistics.mean(c.latency_s for c in mine),
                "words": statistics.mean(c.words for c in mine),
            }
        )
    return rows


def format_table(rows: list[dict]) -> str:
    head = (
        f"{'Model':<20} {'Labels':>6} {'Tokens':>7} {'Total cost':>11} "
        f"{'Mean latency':>13} {'Mean words':>11}"
    )
    lines = [head, "-" * len(head)]
    for r in rows:
        lines.append(
            f"{r['model']:<20} {r['labels']:>6} {r['tokens']:>7} "
            f"${r['cost']:>10.6f} {r['latency']:>12.2f}s {r['words']:>11.1f}"
        )
    return "\n".join(lines)
