"""Temporal activities. Each one re-attaches to the client's Opik trace."""

import json
import os

import opik
from openai import AsyncOpenAI
from opik import opik_context
from opik.integrations.openai import track_openai
from temporalio import activity

import config
from grants import RUBRIC, ActivityInput, check_budget, check_eligibility, parse_scores

# track_openai wraps the client: every completion becomes an llm span with model,
# token usage and cost, nested under whichever tracked span is current.
_client = None


def llm() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = track_openai(AsyncOpenAI(), project_name=config.PROJECT)
    return _client


def _tag_attempt() -> None:
    # Writes the Temporal attempt number onto the current Opik span, so retries are
    # distinguishable in the trace tree; the worker's pid shows these spans came from another process.
    info = activity.info()
    opik_context.update_current_span(
        metadata={"temporal_attempt": info.attempt, "workflow_id": info.workflow_id, "activity": info.activity_type, "pid": os.getpid()}
    )


# Activities are thin: they hand the trace headers to a tracked helper. Passing
# opik_distributed_trace_headers to a @opik.track function makes its span a child of
# the span that created the headers in the client process, instead of a new trace.
@activity.defn
async def check_eligibility_activity(inp: ActivityInput) -> dict:
    return await _eligibility(inp.application, opik_distributed_trace_headers=inp.trace_headers or None)


@activity.defn
async def score_rubric_activity(inp: ActivityInput) -> dict:
    return await _score(inp.application, opik_distributed_trace_headers=inp.trace_headers or None)


@activity.defn
async def check_budget_activity(inp: ActivityInput) -> dict:
    return await _budget(inp.application, opik_distributed_trace_headers=inp.trace_headers or None)


@activity.defn
async def write_letter_activity(inp: ActivityInput) -> str:
    return await _letter(inp.application, inp.context, opik_distributed_trace_headers=inp.trace_headers or None)


# type="tool": a deterministic rules check shows up as a tool span.
@opik.track(name="activity:check_eligibility", type="tool")
async def _eligibility(app: dict) -> dict:
    _tag_attempt()
    return check_eligibility(app)


@opik.track(name="activity:score_rubric", type="general")
async def _score(app: dict) -> dict:
    _tag_attempt()
    response = await llm().chat.completions.create(
        model=config.MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You review community grant applications. Score each criterion from 1 (weak) to 5 "
                f"(excellent): {', '.join(RUBRIC)}. Reply with a JSON object using exactly those keys.",
            },
            {"role": "user", "content": f"{app['title']}\n\n{app['summary']}\n\nRequested: ${app['requested_amount']:,}"},
        ],
    )
    return parse_scores(response.choices[0].message.content)


@opik.track(name="activity:check_budget", type="tool")
async def _budget(app: dict) -> dict:
    _tag_attempt()
    # The first attempt fails on purpose, like a flaky finance service. The raised
    # error is recorded by @opik.track as error_info on this attempt's span; the
    # retry then produces a second, clean span in the same trace.
    if activity.info().attempt == 1:
        raise ConnectionError("Finance ledger unavailable (503) while reading fund balance")
    return check_budget(app, matching_balance=40_000)


@opik.track(name="activity:write_letter", type="general")
async def _letter(app: dict, ctx: dict) -> str:
    _tag_attempt()
    facts = {k: ctx.get(k) for k in ("decision", "eligibility", "scores", "budget")}
    response = await llm().chat.completions.create(
        model=config.MODEL,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": "Write a warm, plain-language decision letter (under 120 words) from the Harbor "
                "County Community Fund. State the decision and the concrete reasons from the facts. Do not "
                "invent facts or amounts. No placeholders such as [Date] or [Name]; sign it 'The Grants Committee'.",
            },
            {"role": "user", "content": f"Applicant: {app['applicant']}\nProject: {app['title']}\nFacts: {json.dumps(facts)}"},
        ],
    )
    return response.choices[0].message.content.strip()
