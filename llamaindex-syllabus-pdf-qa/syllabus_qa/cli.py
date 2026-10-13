"""Command line: `syllabus-qa pdfs | ask | suite | all`."""

import argparse

from . import config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="syllabus-qa", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("pdfs", help="regenerate the syllabus PDFs in data/syllabi")
    ask_p = sub.add_parser("ask", help="answer questions (the demo questions if none given)")
    ask_p.add_argument("question", nargs="*")
    sub.add_parser("suite", help="run the policy test suite")
    sub.add_parser("all", help="demo questions, then the suite")
    args = parser.parse_args(argv)

    config.load_env()
    # Imported after load_env so the Opik project name is set before any Opik client exists.
    import opik

    from .index import build_index, configure_models
    from .pdfs import write_pdfs
    from .qa import ask, enable_tracing, make_engine
    from .suite import DEMO_QUESTIONS, run_suite
    from .suite.run import print_result

    if args.command == "pdfs":
        for path in write_pdfs(config.PDF_DIR):
            print(path)
        return 0

    # Install the Opik handler before the models are created: they pick up the active callback manager.
    enable_tracing()
    configure_models()
    engine = make_engine(build_index(config.PDF_DIR))
    try:
        if args.command in ("ask", "all"):
            for question in (getattr(args, "question", None) or DEMO_QUESTIONS):
                answer = ask(engine, question)
                print(f"Q: {question}\nA: {answer.text}\n   (from {', '.join(answer.files)})\n")
        if args.command in ("suite", "all"):
            print_result(run_suite(engine))
    finally:
        # Traces are sent in the background; flush so none are lost when the process exits.
        opik.flush_tracker()
    return 0
