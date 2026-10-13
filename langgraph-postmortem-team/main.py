"""Run the post-mortem team on the fictional Marlin checkout outage, traced in Opik."""

import os
import pathlib

PROJECT_NAME = "langgraph-postmortem-team"
# Set before opik is imported so every trace lands in this project.
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)

import dotenv

# Provider key lives in a local .env, or in the repo-root .env one level up.
dotenv.load_dotenv(pathlib.Path(__file__).parent / ".env")
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

import opik
from opik.integrations.langchain import OpikTracer, track_langgraph

from postmortem.team import build_graph

INCIDENT = (
    "On 2026-03-14 the Marlin checkout service returned HTTP 503 to a large share of customers "
    "for about 47 minutes. Write the post-mortem."
)


def main() -> None:
    # OpikTracer is a LangChain callback; graph=... attaches the graph structure so the
    # trace gets an agent-graph view with the planner loop drawn in.
    app = build_graph().compile()
    tracer = OpikTracer(project_name=PROJECT_NAME, graph=app.get_graph(xray=True))
    # track_langgraph wraps the compiled graph: every invoke() becomes one trace with a span
    # per node pass and each LLM call nested inside, without passing callbacks by hand.
    app = track_langgraph(app, tracer)

    result = app.invoke({"incident": INCIDENT, "round": 0, "findings": []})

    print(f"Investigation rounds: {result['round'] - 1}  Findings: {len(result['findings'])}\n")
    for f in result["findings"]:
        print(f"  round {f['round']} {f['agent']:<17} {f['focus']}")
    print("\n" + result["report"])

    # Flush so the short-lived script doesn't exit before spans are sent.
    tracer.flush()
    opik.flush_tracker()


if __name__ == "__main__":
    main()
