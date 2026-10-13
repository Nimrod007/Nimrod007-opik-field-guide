"""Offline tests: no provider keys, no Opik server needed."""

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from rulesrag.corpus import load_chunks, split_rulebook
from rulesrag.evals import load_questions, summarise
from rulesrag.graph import build_graph, format_context
from rulesrag.retriever import build_store, retrieve

SAMPLE = "# Mini Game\n\nIntro.\n\n## Setup\nDeal 5 cards.\n\n## Winning\nFirst to 10 wins.\n"


def test_split_rulebook_makes_one_chunk_per_section():
    chunks = split_rulebook(SAMPLE)
    assert [(c.game, c.section) for c in chunks] == [("Mini Game", "Setup"), ("Mini Game", "Winning")]
    assert chunks[1].content == "Mini Game / Winning\nFirst to 10 wins."


def test_bundled_rulebooks_cover_three_games():
    chunks = load_chunks()
    assert {c.game for c in chunks} == {"Saltmarsh Traders", "Emberfall Keep", "Tidecaller"}
    assert all(c.text for c in chunks)


def test_retrieve_returns_k_chunks():
    store = build_store(DeterministicFakeEmbedding(size=32))
    assert len(retrieve(store, "how many reefs?", k=2)) == 2
    assert len(retrieve(store, "how many reefs?", k=1)) == 1


def test_graph_passes_retrieved_context_to_the_model():
    seen = {}

    class Recorder(GenericFakeChatModel):
        def _generate(self, messages, *args, **kwargs):
            seen["system"] = messages[0].content
            return super()._generate(messages, *args, **kwargs)

    llm = Recorder(messages=iter([AIMessage(content="3 reefs")]))
    app = build_graph(lambda q: ["Tidecaller / Reef cards\nMax 3."], llm)
    result = app.invoke({"question": "How many reefs?"})
    assert result["answer"] == "3 reefs"
    assert result["context"] == ["Tidecaller / Reef cards\nMax 3."]
    assert "Max 3." in seen["system"]


def test_format_context_separates_chunks():
    assert format_context(["a", "b"]) == "a\n\n---\n\nb"


def test_question_set_is_well_formed_and_has_an_unanswerable_item():
    items = load_questions()
    assert len(items) >= 10
    assert any("do not cover" in i["expected_output"] for i in items)


def test_summarise_formats_means():
    assert summarise({"hallucination_metric": 0.083, "context_precision_metric": 0.9}) == (
        "  context_precision_metric: 0.90\n  hallucination_metric: 0.08"
    )
