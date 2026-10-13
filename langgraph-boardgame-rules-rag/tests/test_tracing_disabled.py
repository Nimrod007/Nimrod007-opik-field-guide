"""With tracking disabled the tracing wiring must not get in the way."""

import opik
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from rulesrag.graph import build_graph
from rulesrag.retriever import build_store, retrieve
from rulesrag.tracing import PROJECT_NAME, configure_project, trace_graph


def test_traced_graph_still_answers_with_tracking_disabled(monkeypatch):
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    configure_project()
    store = build_store(DeterministicFakeEmbedding(size=32))
    llm = GenericFakeChatModel(messages=iter([AIMessage(content="ok")]))
    app = trace_graph(build_graph(lambda q: retrieve(store, q, 2), llm))
    assert app.invoke({"question": "anything"})["answer"] == "ok"
    opik.flush_tracker()


def test_project_name_matches_folder():
    assert PROJECT_NAME == "langgraph-boardgame-rules-rag"
