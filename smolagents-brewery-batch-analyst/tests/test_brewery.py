import pytest

from brewery import BRIEFING, abv, load_batches
from main import ask
from tracing import flush_tracing, setup_tracing


def test_abv_formula():
    assert abv(1.050, 1.010) == 5.25


def test_planted_stalling_yeast():
    df = load_batches()
    means = df.groupby("yeast_strain").attenuation.mean()
    assert means.idxmin() == "Kestrel-12"
    assert means["Kestrel-12"] < 0.55 < means.drop("Kestrel-12").min()


def test_planted_hot_fermenter():
    df = load_batches()
    off = df[df.outcome == "off-flavor"]
    assert set(off.fermenter) == {"FV-4"}
    hot = df[(df.fermenter == "FV-4") & (df.brew_date >= "2025-07-01")]
    assert hot.ferment_temp_c.min() >= 24


def test_tracing_off_returns_no_provider(monkeypatch):
    # With tracking disabled nothing is instrumented and flushing is a harmless no-op.
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    provider = setup_tracing()
    assert provider is None
    flush_tracing(provider)


def test_ask_runs_without_tracing_or_a_model(monkeypatch):
    # ask() is the function the instrumentor turns into a trace; it works untouched offline.
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")

    class StubAgent:
        def run(self, prompt):
            assert prompt.startswith(BRIEFING)
            return 42

    assert ask(StubAgent(), "How many?") == "42"
