"""Offline tests: the agent runs on a stub model, so no provider key and no Opik server."""

import datetime as dt

from pydantic_ai.models.test import TestModel

from calendar_extraction.agent import build_agent, extract_event
from calendar_extraction.grounding import grounding_issues
from calendar_extraction.schema import Email, load_emails, render_email
from calendar_extraction.suite import GLOBAL_ASSERTIONS, suite_items

EMAIL = Email(
    id="t1",
    sent=dt.date(2026, 10, 12),
    text="Sync Thursday 2pm in Room Fennel with Ines and Tobias. Link: https://meet.example.org/x",
)


def test_corpus_loads_with_assertions():
    emails = load_emails()
    assert len(emails) == 6
    assert all(e.assertions for e in emails)


def test_render_email_carries_the_sent_weekday():
    assert "2026-10-12 (Monday)" in render_email(EMAIL)


def test_suite_items_keep_answers_out_of_data():
    items = suite_items(load_emails())
    assert all(set(i["data"]) == {"email_id", "sent", "text"} for i in items)  # no "id" key
    assert len(GLOBAL_ASSERTIONS) >= 3


def test_grounding_flags_invented_values():
    event = {
        "location": "Boardroom Nine",
        "meeting_url": "https://zoom.example/abc",
        "attendees": ["Ines", "Quentin"],
        "date": None,
        "start_time": "14:00:00",
    }
    issues = grounding_issues(EMAIL, event)
    assert len(issues) == 4


def test_grounding_accepts_supported_values():
    event = {
        "location": "Room Fennel",
        "meeting_url": "https://meet.example.org/x",
        "attendees": ["Ines", "Tobias"],
        "date": "2026-10-15",
        "start_time": "14:00:00",
    }
    assert grounding_issues(EMAIL, event) == []


def test_traced_extract_event_works_with_a_stub_model():
    # extract_event is decorated with @opik.track; with OPIK_TRACK_DISABLE=true it behaves
    # as a plain function, so the stub model's output comes straight back.
    agent = build_agent("test")
    stub = TestModel(custom_output_args={"title": "Sync", "date": "2026-10-15", "attendees": ["Ines"]})
    with agent.override(model=stub):
        event = extract_event(agent, EMAIL)
    assert event["title"] == "Sync"
    assert event["date"] == "2026-10-15"
    assert event["end_time"] is None
