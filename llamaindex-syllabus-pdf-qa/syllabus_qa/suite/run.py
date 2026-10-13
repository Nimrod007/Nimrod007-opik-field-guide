"""Build the Opik test suite and run it against the query engine."""

import opik

from ..config import PROJECT_NAME, SUITE_NAME
from ..qa import ask, unsupported_numbers
from .cases import CASES, GLOBAL_ASSERTIONS


def run_suite(engine):
    client = opik.Opik()
    # A test suite is a dataset whose items carry assertions; an LLM judge grades each
    # answer against them. Inserting identical items again is deduplicated.
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME, project_name=PROJECT_NAME, global_assertions=GLOBAL_ASSERTIONS
    )
    suite.insert([
        {"data": {"question": c["question"]}, "assertions": c["assertions"]} for c in CASES
    ])

    def task(item: dict) -> dict:
        answer = ask(engine, item["question"])
        # Retrieved excerpts go into the output so the judge can check the
        # "no invented numbers" assertion against what retrieval actually returned.
        return {
            "input": item,
            "output": {
                "answer": answer.text,
                "retrieved_from": answer.files,
                # Deterministic check next to the LLM judge; it shows up as a guardrail span.
                "numbers_not_in_excerpts": unsupported_numbers(answer.text, answer.excerpts),
                "retrieved_excerpts": answer.excerpts,
            },
        }

    # run_tests creates an experiment: one row per question, pass/fail per assertion.
    # The judge uses Opik's default model; do not pass a judge override with reasoning_effort.
    return opik.run_tests(test_suite=suite, task=task, worker_threads=3, generate_report=False)


def print_result(result) -> None:
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} questions passed)")
    for item in result.item_results.values():
        question = item.test_results[0].test_case.task_output["input"]["question"]
        print(f"  [{'PASS' if item.passed else 'FAIL'}] {question}")
        if not item.passed:
            for run in item.test_results:
                for score in run.score_results:
                    if score.scoring_failed or score.value != 1:
                        print(f"         failed: {score.name}: {score.reason}")
    if result.experiment_url:
        print(f"\nView the run: {result.experiment_url}")
