"""Dataset + experiment: score the referee for hallucination and retrieval quality."""

import json
from pathlib import Path

import opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import ContextPrecision, Hallucination

QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "data" / "questions.json"
DATASET_NAME = "boardgame-rules-qa"
JUDGE_MODEL = "gpt-4o-mini"


def load_questions(path: Path = QUESTIONS_FILE) -> list[dict]:
    items = json.loads(path.read_text())
    for item in items:
        assert {"question", "expected_output"} <= item.keys(), item
    return items


def summarise(means: dict[str, float]) -> str:
    """One line per metric, e.g. '  hallucination_metric: 0.08'."""
    return "\n".join(f"  {name}: {value:.2f}" for name, value in sorted(means.items()))


def run_experiment(app, *, name: str, k: int, task_threads: int = 4):
    client = opik.Opik()
    # The dataset is the fixed question set every experiment is scored on.
    # insert() deduplicates, so re-running does not pile up copies.
    dataset = client.get_or_create_dataset(name=DATASET_NAME)
    dataset.insert(load_questions())

    def task(item: dict) -> dict:
        # app.invoke is the traced graph, so each dataset row also produces a
        # full retrieve/generate trace linked to this experiment's row.
        result = app.invoke({"question": item["question"]})
        # "output" and "context" are the fields the judges read.
        return {"output": result["answer"], "context": result["context"]}

    # evaluate() runs the task over every dataset item, scores each result with
    # both LLM judges and records one experiment. Hallucination checks the
    # answer against the retrieved context (1.0 = unsupported); ContextPrecision
    # asks whether that context was the right one for the question (1.0 = precise).
    evaluation = evaluate(
        dataset=dataset,
        task=task,
        scoring_metrics=[
            Hallucination(model=JUDGE_MODEL),
            ContextPrecision(model=JUDGE_MODEL),
        ],
        scoring_key_mapping={"input": "question"},
        experiment_name=name,
        # experiment_config shows up as columns in the experiment table, so runs
        # with different k can be compared side by side.
        experiment_config={"k": k, "generator": "gpt-4o-mini", "embeddings": "text-embedding-3-small"},
        task_threads=task_threads,
    )
    aggregated = evaluation.aggregate_evaluation_scores().aggregated_scores
    return evaluation, {metric: stats.mean for metric, stats in aggregated.items()}
