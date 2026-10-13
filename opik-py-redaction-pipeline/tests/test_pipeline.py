import json
from types import SimpleNamespace

import opik
import pipeline as p
from traced_pipeline import make_client, process_document_traced

DOC = {
    "id": "t1",
    "title": "Test note",
    "text": "Mail Ana Brandt at ana@example.org or call (555) 010-4477.",
    "pii": ["Ana Brandt", "ana@example.org", "(555) 010-4477"],
}


class FakeOpenAI:
    """Stands in for the OpenAI client: returns a canned JSON detection."""

    def __init__(self, items):
        body = json.dumps({"items": items})
        msg = SimpleNamespace(content=body)
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        self.response = SimpleNamespace(choices=[SimpleNamespace(message=msg)], model="gpt-4o-mini", usage=usage)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: self.response))


def test_regex_prepass_finds_well_formed_identifiers():
    labels = {f["label"] for f in p.regex_prepass(DOC["text"])}
    assert labels == {"EMAIL", "PHONE"}


def test_parse_llm_items_drops_hallucinated_spans_and_bad_json():
    raw = json.dumps({"items": [{"text": "Ana Brandt", "label": "name"}, {"text": "Nobody Here", "label": "NAME"}]})
    assert [i["text"] for i in p.parse_llm_items(raw, DOC["text"])] == ["Ana Brandt"]
    assert p.parse_llm_items("not json", DOC["text"]) == []


def test_merge_collapses_duplicates_and_contained_strings():
    a = [{"text": "Ana Brandt", "label": "NAME", "source": "llm"}]
    b = [{"text": "Ana", "label": "NAME", "source": "llm"}, {"text": "Ana Brandt", "label": "NAME", "source": "regex"}]
    merged = p.merge_findings(b, a)
    assert [f["text"] for f in merged] == ["Ana Brandt"]


def test_redact_and_verify_and_recall():
    findings = [{"text": "Ana Brandt", "label": "NAME"}] + p.regex_prepass(DOC["text"])
    out = p.redact(DOC["text"], findings)
    assert out == "Mail [NAME] at [EMAIL] or call [PHONE]."
    assert p.verify(findings, out)["ok"]
    assert not p.verify(findings, DOC["text"])["ok"]
    assert p.score_recall(DOC["pii"], out)["recall"] == 1.0


def test_recall_reports_what_leaked():
    s = p.score_recall(["a b", "c d"], "a b stays, c d gone? no")
    assert s["recall"] == 0.0 and s["leaked"] == ["a b", "c d"]


def test_traced_pipeline_runs_with_tracking_disabled(monkeypatch):
    # With tracking disabled the traced function skips every trace/span call, so it is still
    # unit-testable with a stubbed model client and no Opik server.
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    assert not opik.is_tracing_active()
    result = process_document_traced(make_client(), FakeOpenAI([{"text": "Ana Brandt", "label": "NAME"}]), DOC)
    assert result["redacted"] == "Mail [NAME] at [EMAIL] or call [PHONE]."
    assert result["score"]["recall"] == 1.0 and result["verify"]["ok"]
