"""Command line: `rulesrag ask "..."`."""

import argparse
import sys
from pathlib import Path

import opik
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .evals import run_experiment, summarise
from .graph import build_graph
from .retriever import build_store, retrieve
from .tracing import configure_project, trace_graph

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"


def build_app(k: int = 3):
    store = build_store(OpenAIEmbeddings(model=EMBED_MODEL))
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    return trace_graph(build_graph(lambda q: retrieve(store, q, k), llm))


DEMO_QUESTIONS = [
    "In Emberfall Keep, what does a Flare do?",
    "Does a Reef card ever get destroyed in Tidecaller?",
    "Can I play Saltmarsh Traders with 5 players?",  # the rulebook says 2-4
]


def run_eval(k: int, name: str) -> None:
    print(f"Experiment {name} (k={k})")
    evaluation, means = run_experiment(build_app(k), name=name, k=k)
    print(summarise(means))
    if evaluation.experiment_url:
        print(f"  {evaluation.experiment_url}")


def main(argv: list[str] | None = None) -> int:
    configure_project()
    # Keys come from .env here or in any parent directory.
    for parent in Path(__file__).resolve().parents:
        if (parent / ".env").exists():
            load_dotenv(parent / ".env")
            break

    parser = argparse.ArgumentParser(prog="rulesrag", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="answer one rules question")
    ask.add_argument("question")
    ask.add_argument("-k", type=int, default=3, help="chunks to retrieve")
    ev = sub.add_parser("eval", help="run the dataset experiment")
    ev.add_argument("-k", type=int, default=3, help="chunks to retrieve")
    ev.add_argument("--name", help="experiment name (default: k<k>)")
    sub.add_parser("demo", help="ask a few questions, then compare k=3 against k=1")
    args = parser.parse_args(argv)

    if args.command == "ask":
        result = build_app(args.k).invoke({"question": args.question})
        print(result["answer"])
    elif args.command == "eval":
        run_eval(args.k, args.name or f"k{args.k}")
    elif args.command == "demo":
        app = build_app(3)
        for question in DEMO_QUESTIONS:
            print(f"Q: {question}\nA: {app.invoke({'question': question})['answer']}\n")
        run_eval(3, "k3-baseline")
        run_eval(1, "k1-thin-retrieval")
    # Traces are sent from a background thread; flush so a short-lived CLI
    # process doesn't exit before they are delivered.
    opik.flush_tracker()
    return 0


if __name__ == "__main__":
    sys.exit(main())
