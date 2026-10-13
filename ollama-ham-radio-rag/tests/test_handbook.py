"""Offline tests: no Ollama, no Opik, no keys. Run with OPIK_TRACK_DISABLE=true."""

from langchain_core.runnables import RunnableLambda

import main
from handbook import format_context, load_sections, section_label


def test_one_chunk_per_section_with_title():
    chunks = load_sections()
    assert len(chunks) == 16  # 4 chapters x 4 sections
    assert all("\n\n## " in c for c in chunks)
    assert any(c.startswith("Antenna Basics\n\n## Standing wave ratio") for c in chunks)


def test_section_label_and_context_format():
    chunk = "Antenna Basics\n\n## Standing wave ratio\nCheck SWR."
    assert section_label(chunk) == "Antenna Basics > Standing wave ratio"
    assert format_context(["a", "b"]) == "a\n\n---\n\nb"


class FakeStore:
    """Stands in for the vector store: returns canned (document, score) pairs."""

    def similarity_search_with_score(self, question, k):
        doc = type("Doc", (), {"page_content": "Emergency Net Etiquette\n\n## Checking in\nSay your call sign once."})
        return [(doc, 0.81234)][:k]


def test_traced_retrieval_runs_with_tracking_disabled(monkeypatch):
    # The @opik.track'd retriever still works as a plain function when tracking is off.
    prompts = []

    def fake_llm(**_):  # replaces ChatOllama so no server is needed
        return RunnableLambda(lambda p: prompts.append(p.to_string()) or "stub answer")

    monkeypatch.setattr(main, "ChatOllama", fake_llm)
    chain = main.build_chain(FakeStore())
    assert chain.invoke("How do I check in?") == "stub answer"
    assert "Say your call sign once." in prompts[0]
    assert "How do I check in?" in prompts[0]
