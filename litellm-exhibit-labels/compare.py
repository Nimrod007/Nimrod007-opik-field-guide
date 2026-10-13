"""Rebuild the per-model comparison table from what Opik stored, not from local timers."""

import statistics
import time
from collections import defaultdict

import opik

PROJECT = "litellm-exhibit-labels"


def by_model(spans) -> list[dict]:
    """Group llm spans by model: calls, tokens, cost and latency, as Opik recorded them."""
    groups = defaultdict(list)
    for s in spans:
        if s.type == "llm" and s.model:
            groups[s.model].append(s)
    rows = []
    for model, items in sorted(groups.items()):
        rows.append(
            {
                "model": model,
                "provider": items[0].provider,
                "calls": len(items),
                "tokens": sum((s.usage or {}).get("total_tokens", 0) for s in items),
                # total_estimated_cost is a span field Opik fills from the model's price table;
                # None would mean Opik could not price the model.
                "cost": sum(s.total_estimated_cost or 0.0 for s in items),
                "priced": sum(s.total_estimated_cost is not None for s in items),
                "latency": statistics.mean((s.end_time - s.start_time).total_seconds() for s in items),
            }
        )
    return rows


def format_rows(rows: list[dict]) -> str:
    head = (f"{'Model (as stored in Opik)':<28} {'Provider':<10} {'Calls':>5} {'Tokens':>7} "
            f"{'Cost (USD)':>11} {'Priced':>6} {'Mean latency':>13}")
    lines = [head, "-" * len(head)]
    for r in rows:
        lines.append(f"{r['model']:<28} {r['provider']:<10} {r['calls']:>5} {r['tokens']:>7} "
                     f"${r['cost']:>10.6f} {r['priced']:>3}/{r['calls']:<2} {r['latency']:>12.2f}s")
    if len(rows) == 2 and rows[0]["cost"] and rows[1]["cost"]:
        hi, lo = sorted(rows, key=lambda r: r["cost"], reverse=True)
        lines.append(f"\n{hi['model']} cost {hi['cost'] / lo['cost']:.1f}x as much as {lo['model']} for the same labels.")
    return "\n".join(lines)


def fetch_spans(expected: int, project: str = PROJECT, wait_s: float = 20.0):
    """Query Opik for the project's spans, waiting briefly for ingestion to catch up."""
    client = opik.Opik()
    deadline = time.time() + wait_s
    while True:
        spans = client.search_spans(project_name=project, max_results=1000)
        if len(spans) >= expected or time.time() > deadline:
            return spans
        time.sleep(1)


def main(expected: int = 0) -> None:
    print(format_rows(by_model(fetch_spans(expected))))


if __name__ == "__main__":
    main()
