from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import compare
import labels
from labels import Call


def test_artifacts_are_complete():
    arts = labels.load_artifacts()
    assert len(arts) == 6
    assert all({"id", "name", "kind", "period", "found", "facts"} <= a.keys() for a in arts)


def test_prompt_contains_facts_and_limit():
    art = labels.load_artifacts()[0]
    prompt = labels.build_prompt(art, word_limit=40)
    assert "at most 40 words" in prompt
    assert all(f in prompt for f in art["facts"])


def test_summarize_and_table():
    calls = [
        Call("a", "A-1", 1.0, 0.001, 100, 50),
        Call("a", "A-2", 3.0, 0.003, 200, 60),
        Call("b", "A-1", 2.0, 0.0001, 90, 40),
    ]
    rows = labels.summarize(calls)
    assert rows[0]["tokens"] == 300 and rows[0]["latency"] == 2.0 and rows[0]["words"] == 55
    table = labels.format_table(rows)
    assert "a" in table and "b" in table and "$  0.004000" in table


def span(model, cost, secs, tokens=100):
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return SimpleNamespace(type="llm", model=model, provider="p", total_estimated_cost=cost,
                           usage={"total_tokens": tokens}, start_time=t, end_time=t + timedelta(seconds=secs))


def test_by_model_groups_opik_spans_and_flags_unpriced():
    rows = compare.by_model([span("m1", 0.002, 1), span("m1", 0.004, 3), span("m2", None, 2)])
    m1, m2 = rows
    assert m1["calls"] == 2 and m1["cost"] == 0.006 and m1["latency"] == 2.0
    assert m2["priced"] == 0  # a null cost shows up as 0 priced spans
    assert "0/1" in compare.format_rows(rows)


def test_traced_function_runs_with_tracking_disabled(monkeypatch):
    # Importing main registers the OpikLogger callback; with tracking disabled and the
    # completion stubbed, the traced call path still runs offline.
    import main

    fake = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="# Title\nA short label."))],
        usage=SimpleNamespace(total_tokens=42),
        _hidden_params={"response_cost": 0.5},
    )
    monkeypatch.setattr(main.litellm, "completion", lambda **kw: fake)
    call = main.write_label("gpt-4o-mini", labels.load_artifacts()[0])
    assert call.tokens == 42 and call.cost_usd == 0.5 and call.words == 5
