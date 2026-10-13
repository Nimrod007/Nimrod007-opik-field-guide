"""Print tokens and dollar cost per agent for the latest kickoff trace in Opik.

Run after main.py:  uv run cost_report.py
"""

from collections import defaultdict
from typing import Any

import opik

PROJECT = "crewai-theater-season-planner"
AGENT_ROLES = {"Programming Dramaturg", "Budget Manager", "Rehearsal Scheduler"}


def cost_by_agent(spans: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Roll llm-span usage and cost up to the agent span that owns each call.

    Cost and token usage live only on llm spans, several levels below the
    agent span, so walk the parent chain until an agent role is found.
    """
    by_id = {s["id"]: s for s in spans}
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}
    )
    for span in spans:
        if span["type"] != "llm":
            continue
        node = span
        while node and node["name"] not in AGENT_ROLES:
            node = by_id.get(node["parent_span_id"])
        agent = node["name"] if node else "(unattributed)"
        usage = span.get("usage") or {}
        totals[agent]["calls"] += 1
        totals[agent]["prompt_tokens"] += usage.get("prompt_tokens", 0)
        totals[agent]["completion_tokens"] += usage.get("completion_tokens", 0)
        totals[agent]["cost_usd"] += span.get("total_estimated_cost") or 0.0
    return dict(totals)


def latest_kickoff_spans(client: opik.Opik) -> tuple[Any, list[dict[str, Any]]]:
    # One trace per crew.kickoff(): the newest one is the run we just did.
    # wait_for_at_least polls until the trace is readable (ingestion is asynchronous).
    traces = client.search_traces(project_name=PROJECT, max_results=1, wait_for_at_least=1, wait_for_timeout=60)
    if not traces:
        raise SystemExit(f"No traces in project {PROJECT!r}; run main.py first.")
    trace = traces[0]
    spans = client.search_spans(project_name=PROJECT, trace_id=trace.id, max_results=1000)
    rows = [
        {
            "id": s.id,
            "parent_span_id": s.parent_span_id,
            "name": s.name,
            "type": s.type,
            "usage": s.usage,
            "total_estimated_cost": s.total_estimated_cost,
        }
        for s in spans
    ]
    return trace, rows


if __name__ == "__main__":
    client = opik.Opik()
    trace, rows = latest_kickoff_spans(client)
    print(f"trace {trace.id} ({len(rows)} spans), trace cost ${trace.total_estimated_cost or 0:.6f}\n")
    print(f"{'agent':24} {'calls':>5} {'prompt':>8} {'compl.':>8} {'cost USD':>10}")
    for agent, t in sorted(cost_by_agent(rows).items(), key=lambda kv: -kv[1]["cost_usd"]):
        print(f"{agent:24} {t['calls']:>5} {t['prompt_tokens']:>8} {t['completion_tokens']:>8} {t['cost_usd']:>10.6f}")
