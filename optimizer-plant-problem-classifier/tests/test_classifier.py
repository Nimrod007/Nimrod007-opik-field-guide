import os

os.environ["OPIK_TRACK_DISABLE"] = "true"  # before opik is imported: no network, no Opik needed

import pytest  # noqa: E402

from plant_classifier import LABELS, SEED_SYSTEM, classify, label_accuracy, load_problems  # noqa: E402


def test_dataset_is_balanced_and_valid():
    problems = load_problems()
    assert len(problems) == 24
    assert {p["label"] for p in problems} == set(LABELS)
    assert all(sum(p["label"] == l for p in problems) == 4 for l in LABELS)


@pytest.mark.parametrize("answer", ["overwatering", "Overwatering.", ' "overwatering" ', "**overwatering**"])
def test_metric_accepts_clean_answers(answer):
    assert label_accuracy("overwatering", answer) == 1.0


@pytest.mark.parametrize("answer", ["It looks like overwatering", "too much water", "light", ""])
def test_metric_rejects_chatty_or_wrong_answers(answer):
    assert label_accuracy("overwatering", answer) == 0.0


class _FakeClient:
    """Stands in for the OpenAI client; records the messages it was given."""

    def __init__(self, reply):
        self.reply, self.calls = reply, []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        msg = type("M", (), {"content": self.reply})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})


def test_traced_classify_works_with_tracking_disabled():
    client = _FakeClient("light")
    assert classify(client, SEED_SYSTEM, "leggy basil on a dark sill") == "light"
    assert client.calls[0]["messages"][0] == {"role": "system", "content": SEED_SYSTEM}
