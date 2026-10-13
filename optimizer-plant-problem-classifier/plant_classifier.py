"""Plant-problem classifier: shared pieces (dataset, metric, seed prompt, model call)."""

import json
import pathlib

from openai import OpenAI

LABELS = ["pests", "disease", "overwatering", "underwatering", "nutrient-deficiency", "light"]
MODEL = "gpt-4o-mini"
DATA_PATH = pathlib.Path(__file__).parent / "data" / "problems.json"

# A first-draft prompt: categories in loose prose, nothing about the answer format.
SEED_SYSTEM = (
    "You help home gardeners figure out what is wrong with their plants. "
    "The cause is usually pests, a plant disease, too much water, too little water, "
    "a lack of nutrients, or not the right amount of light. Say which one it is."
)


def load_problems() -> list[dict]:
    """Return the labeled descriptions as [{"text": ..., "label": ...}, ...]."""
    return json.loads(DATA_PATH.read_text())


def label_accuracy(expected: str, answer: str) -> float:
    """Exact match after trimming case, whitespace and punctuation.

    "Overwatering." passes; "It looks like overwatering" does not, so the
    output format is part of what a prompt has to get right.
    """
    return 1.0 if answer.strip().lower().strip(".!\"'` *") == expected else 0.0


def classify(client: OpenAI, system: str, text: str) -> str:
    """Ask the model for a label using `system` as the system prompt."""
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": text}],
    )
    return resp.choices[0].message.content or ""
