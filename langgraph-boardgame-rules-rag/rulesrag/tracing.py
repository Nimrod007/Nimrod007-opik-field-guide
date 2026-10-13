"""Opik wiring: one project, one tracer, one wrapped graph."""

import os

PROJECT_NAME = "langgraph-boardgame-rules-rag"


def configure_project() -> None:
    # Must run before anything creates an Opik client: it decides which
    # project every trace lands in (Opik's default project otherwise).
    os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)


def trace_graph(compiled_graph):
    from opik.integrations.langchain import OpikTracer, track_langgraph

    # track_langgraph attaches the OpikTracer to the compiled graph, so every
    # .invoke() becomes one trace with a span per node and a nested llm span for
    # the chat model. Passing graph= stores its structure in the trace metadata
    # (_opik_graph_definition) so the UI can draw the retrieve -> generate graph.
    tracer = OpikTracer(project_name=PROJECT_NAME, graph=compiled_graph.get_graph(xray=True))
    return track_langgraph(compiled_graph, tracer)
