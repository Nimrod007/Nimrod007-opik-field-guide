from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

import app as app_module
from catalog import format_books, load_catalog, score, search_catalog


def test_catalog_is_well_formed():
    books = load_catalog()
    assert len(books) >= 10
    assert len({b["id"] for b in books}) == len(books)


def test_search_finds_relevant_book_first():
    assert search_catalog("a cozy small-town winter romance")[0]["title"] == "Snowed In at Wren Hollow"
    assert search_catalog("dragons for kids")[0]["title"] == "Tiny Dragons of Tuesday"


def test_search_returns_nothing_for_unrelated_query():
    assert search_catalog("quantum chromodynamics") == []
    assert format_books([]) == "(no catalog matches)"


def test_format_books_flags_availability():
    text = format_books([b for b in load_catalog() if b["id"] in {"B03", "B01"}])
    assert "checked out, can be reserved" in text and "on the shelf" in text


def test_tags_outweigh_summary_words():
    book = {"title": "x", "author": "y", "genre": "mystery", "tags": ["detective"], "summary": "detective"}
    assert score("detective", book) == 3


def test_chat_endpoint_keeps_history_per_session(monkeypatch):
    # Swap the model for a fake: runs the real history/search/prompt steps, no network.
    fake = FakeListChatModel(responses=["first reply", "second reply"])
    chain = (
        RunnableLambda(app_module.prepare_inputs)
        | app_module.prompt | fake | StrOutputParser()
    )
    monkeypatch.setattr(app_module, "_chain", chain)
    app_module.HISTORY.clear()
    client = TestClient(app_module.app)
    r1 = client.post("/chat", json={"message": "cozy small-town book", "session_id": "s1"})
    r2 = client.post("/chat", json={"message": "and a mystery?", "session_id": "s1"})
    assert (r1.json()["reply"], r2.json()["reply"]) == ("first reply", "second reply")
    assert len(app_module.HISTORY["s1"]) == 4
    assert "s2" not in app_module.HISTORY


def test_traced_lookup_works_with_tracking_disabled():
    # @opik.track wraps lookup_books; with OPIK_TRACK_DISABLE=true it is a plain call.
    assert app_module.lookup_books("dragons")[0]["id"] == "B10"
