"""Plant-problem classifier: shared pieces (dataset, metric, seed prompt, model call)."""

import json
import pathlib

import opik
from openai import OpenAI
from opik.integrations.openai import track_openai

LABELS = ["pests", "disease", "overwatering", "underwatering", "nutrient-deficiency", "light"]
MODEL = "gpt-4o-mini"
PROJECT_NAME = "optimizer-plant-problem-classifier"
DATA_PATH = pathlib.Path(__file__).parent / "data" / "problems.json"

# A first-draft prompt: causes in loose prose, and nothing about the exact label wording to use.
SEED_SYSTEM = (
    "You help home gardeners figure out what is wrong with their plants. "
    "The cause is usually pests, a plant disease, too much water, too little water, "
    "a lack of nutrients, or not the right amount of light. "
    "Reply with a short phrase naming the cause."
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


def make_client() -> OpenAI:
    """OpenAI client wrapped for Opik."""
    # track_openai wraps the client: every completion becomes an llm span with
    # token usage and cost, in the project named by OPIK_PROJECT_NAME.
    return track_openai(OpenAI(), project_name=PROJECT_NAME)


@opik.track(name="classify_problem", project_name=PROJECT_NAME)  # one trace per description; the llm span nests inside
def classify(client: OpenAI, system: str, text: str) -> str:
    """Ask the model for a label using `system` as the system prompt."""
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": text}],
    )
    return resp.choices[0].message.content or ""
