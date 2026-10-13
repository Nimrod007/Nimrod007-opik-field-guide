"""Calls a traced activity helper with tracking disabled and a stubbed Temporal context."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import activities

APP = json.loads((Path(__file__).parent.parent / "data" / "applications.json").read_text())[0]


def fake_info(attempt):
    return SimpleNamespace(attempt=attempt, workflow_id="wf", activity_type="check_budget")


async def test_traced_budget_fails_then_succeeds(monkeypatch):
    # @opik.track must not get in the way: the raw exception still reaches the caller
    # (so Temporal would retry) and the result is unchanged on the second attempt.
    monkeypatch.setattr(activities.activity, "info", lambda: fake_info(1))
    with pytest.raises(ConnectionError):
        await activities._budget(APP)
    monkeypatch.setattr(activities.activity, "info", lambda: fake_info(2))
    assert (await activities._budget(APP))["ok"] is True


async def test_score_uses_stubbed_model(monkeypatch):
    monkeypatch.setattr(activities.activity, "info", lambda: fake_info(1))

    async def create(**kwargs):
        content = '{"community_need": 4, "feasibility": 4, "inclusion": 3, "sustainability": 5}'
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    stub = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(activities, "llm", lambda: stub)
    assert (await activities._score(APP))["sustainability"] == 5
