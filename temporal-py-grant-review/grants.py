"""Pure grant-review logic: eligibility rules, rubric parsing, budget check, decision.

No Opik, Temporal or network code lives here, so the Temporal workflow sandbox can
import it and the unit tests can exercise it offline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

SERVICE_AREA = "Harbor County"
MAX_REQUEST = 15_000
ALLOWED_TYPES = {"nonprofit", "resident_group", "school"}
RUBRIC = ("community_need", "feasibility", "inclusion", "sustainability")
APPROVE_AT = 3.5


@dataclass
class ReviewInput:
    """Workflow input. `trace_headers` carries Opik's distributed-tracing ids."""

    application: dict
    trace_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ActivityInput:
    """Activity input: the same trace headers ride along with every activity call."""

    application: dict
    trace_headers: dict[str, str] = field(default_factory=dict)
    context: dict = field(default_factory=dict)


def check_eligibility(app: dict) -> dict:
    reasons = []
    if app["county"] != SERVICE_AREA:
        reasons.append(f"outside the service area ({app['county']})")
    if app["organization_type"] not in ALLOWED_TYPES:
        reasons.append(f"organization type '{app['organization_type']}' is not funded")
    if app["requested_amount"] > MAX_REQUEST:
        reasons.append(f"request exceeds the ${MAX_REQUEST:,} cap")
    return {"eligible": not reasons, "reasons": reasons}


def check_budget(app: dict, matching_balance: float) -> dict:
    """Line items must add up to the request; soft costs are flagged above 20%."""
    total = sum(i["amount"] for i in app["budget"])
    soft = sum(
        i["amount"]
        for i in app["budget"]
        if any(w in i["item"].lower() for w in ("marketing", "party", "stipend", "snacks"))
    )
    issues = []
    if total != app["requested_amount"]:
        issues.append(f"line items total ${total:,} but ${app['requested_amount']:,} requested")
    if total and soft / total > 0.20:
        issues.append(f"soft costs are {soft / total:.0%} of the budget (limit 20%)")
    if app["requested_amount"] > matching_balance:
        issues.append("request exceeds the remaining fund balance")
    return {"ok": not issues, "issues": issues, "total": total, "soft_share": round(soft / total, 2) if total else 0}


def parse_scores(raw: str) -> dict[str, int]:
    """Parse the model's JSON rubric; clamp every criterion to 1-5."""
    data = json.loads(raw)
    scores = {}
    for key in RUBRIC:
        value = int(round(float(data[key])))
        scores[key] = max(1, min(5, value))
    return scores


def average(scores: dict[str, int]) -> float:
    return round(sum(scores.values()) / len(scores), 2)


def decide(eligibility: dict, scores: dict[str, int] | None, budget: dict | None) -> str:
    if not eligibility["eligible"]:
        return "decline"
    assert scores is not None and budget is not None
    if average(scores) >= APPROVE_AT and budget["ok"]:
        return "approve"
    if average(scores) >= 2.5:
        return "revise"
    return "decline"
