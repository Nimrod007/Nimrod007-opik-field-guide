"""The same pipeline as pipeline.py, traced by hand with the low-level Opik client.

No decorators and no integrations: every trace, span, usage block and flush below is an
explicit call, so you can see exactly what lands in Opik and why.
"""

from __future__ import annotations

from datetime import datetime

import opik

import pipeline as steps

PROJECT = "opik-py-redaction-pipeline"


def now() -> datetime:
    return datetime.now().astimezone()


def make_client() -> opik.Opik:
    # The low-level client owns the background batching queue; project_name routes every
    # trace to one project instead of "Default Project". flush() on it is the delivery guarantee.
    return opik.Opik(project_name=PROJECT)


def record(trace, name: str, type_: str, started: datetime, **fields):
    # One create call carrying start_time, end_time and the output together. A span is sent as
    # a single complete row, so there is no later update that could overtake its own creation
    # (calling span.end() right after creation can, see README "Gotchas").
    return trace.span(name=name, type=type_, start_time=started, end_time=now(), **fields)


def process_document_traced(client: opik.Opik, openai_client, doc: dict) -> dict:
    # OPIK_TRACK_DISABLE only switches off @track and the integrations; the low-level client
    # keeps sending whatever you give it. Checking is_tracing_active() ourselves is what makes
    # the env var (and opik.set_tracing_active(False)) work for hand-written traces.
    if not opik.is_tracing_active():
        return steps.process_document(openai_client, doc)

    text = doc["text"]
    started = now()
    # client.trace() opens the root of the tree: this row is what the Traces tab lists. The
    # trace id is kept so the final payload below can overwrite this row with end time and output.
    trace = client.trace(
        name="redact-document",
        start_time=started,
        input={"doc_id": doc["id"], "title": doc["title"], "text": text},
        tags=["redaction"],
        metadata={"model": steps.MODEL},
    )

    # tool span: deterministic regex step, shows its findings as output
    t0 = now()
    rx = steps.regex_prepass(text)
    record(trace, "regex-prepass", "tool", t0, input={"text": text}, output={"findings": rx})

    # llm span: type="llm" plus model, provider and a usage dict is what makes Opik show token
    # counts and compute total_estimated_cost. Without provider or usage the cost column is empty.
    t0 = now()
    response = steps.call_llm(openai_client, text)
    raw = response.choices[0].message.content or ""
    llm = steps.parse_llm_items(raw, text)
    record(
        trace, f"chat {steps.MODEL}", "llm", t0,
        input={"messages": steps.build_messages(text)},
        output={"raw": raw, "kept_findings": llm},
        model=response.model,
        provider="openai",
        usage={
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    )

    t0 = now()
    merged = steps.merge_findings(rx, llm)
    record(trace, "merge", "general", t0,
           input={"regex": len(rx), "llm": len(llm)}, output={"findings": merged})

    t0 = now()
    redacted = steps.redact(text, merged)
    record(trace, "redact", "general", t0, input={"findings": len(merged)}, output={"redacted": redacted})

    # guardrail span: the verify step is a pass/fail check on the output, which is what the
    # guardrail type is for; it appears with its own icon in the span tree.
    t0 = now()
    check = steps.verify(merged, redacted)
    record(trace, "verify", "guardrail", t0, input={"redacted": redacted}, output=check)

    # Re-send the whole trace payload with the same id. The backend overwrites the row, so the
    # trace has input, output and duration even if the early create was still queued.
    client.trace(
        id=trace.id, name="redact-document", start_time=started, end_time=now(),
        input={"doc_id": doc["id"], "title": doc["title"], "text": text},
        output={"redacted": redacted, "verify_ok": check["ok"]},
        tags=["redaction", "verified" if check["ok"] else "leak"],
        metadata={"model": steps.MODEL, "findings": len(merged)},
    )
    score = steps.score_recall(doc.get("pii", []), redacted)

    # Feedback scores attach numbers to the trace: they appear as columns in the Traces tab and
    # can be filtered or sorted (e.g. "pii_recall < 1"). The reason shows in the score tooltip.
    trace.log_feedback_score(
        name="pii_recall", value=score["recall"],
        reason=("all known PII removed" if not score["leaked"]
                else f"still present: {', '.join(score['leaked'])}"),
    )
    trace.log_feedback_score(
        name="verify_passed", value=1.0 if check["ok"] else 0.0,
        reason="rescan found nothing" if check["ok"] else f"leaks: {', '.join(check['leaks'])}",
    )
    return {"redacted": redacted, "findings": merged, "verify": check, "score": score}
