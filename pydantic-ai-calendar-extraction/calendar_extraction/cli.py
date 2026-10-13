"""Command line: `calendar-extraction extract|suite`."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .agent import PROMPTS, build_agent, extract_event
from .grounding import grounding_issues
from .schema import load_emails
from .tracing import flush_tracing, setup_tracing


def cmd_extract(args: argparse.Namespace) -> None:
    setup_tracing()
    agent = build_agent()
    for email in load_emails():
        if args.id and email.id != args.id:
            continue
        print(f"[{email.id}] {email.text[:60]!r}...")
        event = extract_event(agent, email)
        print(json.dumps(event, indent=2))
        for issue in grounding_issues(email, event):
            print(f"  WARNING: {issue}")
        print()
    flush_tracing()


def cmd_suite(args: argparse.Namespace) -> None:
    from opik.api_objects.dataset.test_suite.test_suite_result import is_score_passed

    from .suite import run_suite

    setup_tracing()
    result = run_suite(args.model, args.prompt)
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} emails)")
    for item_result in result.item_results.values():
        item = item_result.test_results[0].test_case.task_output["input"]
        verdict = "PASS" if item_result.passed else "FAIL"
        print(f"  [{verdict}] {item['email_id']} ({item_result.runs_passed}/{item_result.runs_total} runs)")
        failed = [
            score
            for run in item_result.test_results
            for score in run.score_results
            if not is_score_passed(score)
        ]
        for score in failed[:2]:
            print(f"      x {score.name}: {score.reason}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")
    flush_tracing()


def main(argv: list[str] | None = None) -> None:
    # Provider keys come from the repo-root .env or a local one.
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # hush the startup banner
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    parser = argparse.ArgumentParser(prog="calendar-extraction")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract", help="extract an event from every email (or one with --id)")
    p.add_argument("--id")
    p.set_defaults(func=cmd_extract)
    s = sub.add_parser("suite", help="run the Opik test suite over every email")
    s.add_argument("--model", default="gpt-4o-mini")
    s.add_argument("--prompt", choices=sorted(PROMPTS), default="strict")
    s.set_defaults(func=cmd_suite)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
