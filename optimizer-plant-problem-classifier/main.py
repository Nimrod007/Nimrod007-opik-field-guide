"""Optimize the plant-problem classifier prompt with Opik's Agent Optimizer.

The seed prompt names the six causes in loose prose and never says how to
answer, so exact-match accuracy is low. MetaPromptOptimizer scores it on the
labeled descriptions, reasons about the failures and proposes better prompts
within a small trial budget. The score curve lands in Opik, and the winner is
saved to the prompt library next to the seed it beat.
"""

import os
import pathlib

from plant_classifier import MODEL, PROJECT_NAME, SEED_SYSTEM, label_accuracy, load_problems

# Project for the optimization run, its trial experiments and the prompt
# versions; set before the Opik client is created.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
# This dev box may route OpenAI through a local proxy; the example talks to the public API.
os.environ.pop("OPENAI_BASE_URL", None)
os.environ.pop("OPENAI_API_BASE", None)

import dotenv  # noqa: E402

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

import opik  # noqa: E402
from opik.evaluation.metrics.score_result import ScoreResult  # noqa: E402
from opik_optimizer import ChatPrompt, MetaPromptOptimizer  # noqa: E402

DATASET_NAME = "plant-problem-descriptions"
PROMPT_NAME = "plant-triage"
MAX_TRIALS = 6  # candidate prompts the optimizer may evaluate: the cost cap


def metric(dataset_item: dict, llm_output: str) -> ScoreResult:
    """Optimizer metric: (dataset item, model output) -> score."""
    score = label_accuracy(dataset_item["label"], llm_output)
    # The reason is what the optimizer's reasoning model reads about each miss;
    # without the expected label it can see that answers fail but not what they
    # should have said. It is also shown next to the score in Opik.
    reason = "correct" if score else f"expected '{dataset_item['label']}', model said '{llm_output.strip()[:80]}'"
    return ScoreResult(name="label_accuracy", value=score, reason=reason)


def main() -> None:
    client = opik.Opik()
    problems = load_problems()

    # The dataset is the ground truth the optimizer scores every candidate against.
    # Identical rows are deduplicated, so a re-run reuses it.
    dataset = client.get_or_create_dataset(
        name=DATASET_NAME, description="24 fictional gardener descriptions labeled with the real cause"
    )
    dataset.insert(problems)

    # The optimizer fills {text} from each dataset item's "text" field.
    seed = ChatPrompt(name=PROMPT_NAME, system=SEED_SYSTEM, user="{text}", model=f"openai/{MODEL}")

    # Prompt library v1 = the seed, saved before optimizing so the library tells
    # the whole story. Prompts are project-scoped, hence project_name.
    client.create_chat_prompt(
        name=PROMPT_NAME,
        messages=[{"role": "system", "content": SEED_SYSTEM}, {"role": "user", "content": "{{text}}"}],
        change_description="Seed prompt (hand-written, pre-optimization)",
        project_name=PROJECT_NAME,
    )

    # Creates an Optimization run in the project; each trial is an experiment on
    # the dataset, which draws the score curve in the Optimization runs tab.
    optimizer = MetaPromptOptimizer(model=f"openai/{MODEL}", prompts_per_round=3, seed=7, verbose=1)
    result = optimizer.optimize_prompt(
        prompt=seed,
        dataset=dataset,
        metric=metric,
        n_samples=len(problems),
        max_trials=MAX_TRIALS,
        project_name=PROJECT_NAME,
    )

    initial = result.initial_score or 0.0
    best = result.score
    print("\n" + "=" * 64)
    print(f"seed accuracy    : {initial:.3f}")
    print(f"best accuracy    : {best:.3f}  ({best - initial:+.3f})")
    print(f"trials completed : {result.details.get('trials_completed')}  (budget {MAX_TRIALS})")
    print(f"llm calls        : {result.llm_calls}")
    print(f"run link         : {result.get_run_link()}")
    print("=" * 64)

    # Only a real gain earns a new library version.
    if best > initial:
        messages = result.prompt.get_messages()
        for m in messages:  # optimizer placeholders are {text}; the library uses mustache {{text}}
            m["content"] = m["content"].replace("{text}", "{{text}}")
        client.create_chat_prompt(
            name=PROMPT_NAME,
            messages=messages,
            change_description=f"MetaPromptOptimizer winner: {initial:.3f} -> {best:.3f} on {DATASET_NAME}",
            project_name=PROJECT_NAME,
        )
        print(f"\nSaved the winner as a new version of '{PROMPT_NAME}'. Winning system prompt:\n")
        print(messages[0]["content"])
    else:
        print("\nNo improvement over the seed; the library keeps only v1.")

    opik.flush_tracker()  # push any buffered traces before the process exits


if __name__ == "__main__":
    main()
