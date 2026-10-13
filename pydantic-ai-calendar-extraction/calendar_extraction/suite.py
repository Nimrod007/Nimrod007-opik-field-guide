"""The Opik test suite: plain-language assertions that catch invented or wrong values."""

from typing import Any

import opik

from .agent import build_agent, extract_event
from .schema import Email, load_emails
from .tracing import PROJECT_NAME

# The LLM judge that grades assertions; a stronger judge than the extractor keeps verdicts steady.
JUDGE_MODEL = "gpt-4.1-mini"

# Judge verdicts and extractions both drift between runs, so each email runs 3 times and
# passes if 2 do; Opik records every run as its own trace and experiment item.
EXECUTION_POLICY = {"runs_per_item": 3, "pass_threshold": 2}

# Rules every extraction must satisfy; the LLM judge checks each one per email.
GLOBAL_ASSERTIONS = [
    "The output has all of the fields title, date, start_time, end_time, timezone, location, "
    "meeting_url and attendees; a field being null or an empty list still counts as present",
    "The title is a short label for the event that fits the email; it does not need to be "
    "quoted verbatim",
    "No date, time, timezone, location or link is invented: each non-null one is supported by "
    "the email. A null value, or an empty attendees list, is always acceptable",
    "If the date is non-null and the email names a weekday, the date falls on that weekday "
    "counted forward from the sent date; a null date passes this check",
]


def suite_items(emails: list[Email]) -> list[dict[str, Any]]:
    # Item data holds only what the agent receives. Expected values live in the
    # assertions, never in the data, or the judge could read answers instead of checking.
    # The key is "email_id", not "id": a data key named "id" collides with the item's own id.
    return [
        {"data": {"email_id": e.id, "sent": e.sent.isoformat(), "text": e.text}, "assertions": e.assertions}
        for e in emails
    ]


def run_suite(model: str = "gpt-4o-mini", prompt: str = "strict"):
    client = opik.Opik(project_name=PROJECT_NAME)
    # A test suite is an Opik dataset whose items carry assertions; the global ones apply
    # to every item. Same name = same suite, so re-runs become new experiments on it.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy=EXECUTION_POLICY,
    )
    # insert deduplicates identical items, so re-running does not pile up copies.
    suite.insert(suite_items(load_emails()))
    agent = build_agent(f"openai:{model}", prompt)

    def task(item: dict[str, Any]) -> dict[str, Any]:
        # The returned "input"/"output" are what the judge sees next to the assertions.
        return {"input": item, "output": extract_event(agent, Email(id=item["email_id"], sent=item["sent"], text=item["text"]))}

    # run_tests runs the task per item, has an LLM judge grade every assertion, and
    # creates an experiment whose rows show a pass/fail per email.
    return opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name=f"calendar-{prompt}-prompt-{model}",
        # experiment_config is stored on the experiment, so runs can be told apart in the table.
        experiment_config={"extractor_model": model, "prompt": prompt, "judge_model": JUDGE_MODEL},
        worker_threads=3,
        model=JUDGE_MODEL,
        generate_report=False,
    )
