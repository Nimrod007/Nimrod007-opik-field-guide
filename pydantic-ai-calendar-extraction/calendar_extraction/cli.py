"""Command line: `calendar-extraction extract|suite`."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .agent import build_agent, extract_event
from .schema import load_emails
from .tracing import flush_tracing, setup_tracing


def cmd_extract(args: argparse.Namespace) -> None:
    setup_tracing()
    agent = build_agent()
    for email in load_emails():
        if args.id and email.id != args.id:
            continue
        print(f"[{email.id}] {email.text[:60]!r}...")
        print(json.dumps(extract_event(agent, email), indent=2), "\n")
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
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
