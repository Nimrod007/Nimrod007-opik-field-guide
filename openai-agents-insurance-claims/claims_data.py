"""Fictional policies, claims and the pure business rules behind the tools.

Nothing here knows about the Agents SDK or Opik, so it is trivial to unit-test.
"""

from __future__ import annotations

POLICIES: dict[str, dict] = {
    "HP-1001": {
        "holder": "Marta Okonkwo", "status": "active",
        "address": "14 Larch Lane, Dunmere",
        "deductible_usd": 500,
        "limits_usd": {"auto": 25_000, "property": 300_000, "liability": 100_000},
        "exclusions": ["flood", "wear and tear"],
    },
    "HP-1002": {
        "holder": "Teodor Lindqvist", "status": "lapsed",
        "address": "3 Quarry Road, Dunmere",
        "deductible_usd": 1_000,
        "limits_usd": {"auto": 0, "property": 200_000, "liability": 50_000},
        "exclusions": ["flood"],
    },
    "HP-1003": {
        "holder": "Priya Raman", "status": "active",
        "address": "88 Heron Court, Dunmere",
        "deductible_usd": 250,
        "limits_usd": {"auto": 15_000, "property": 450_000, "liability": 250_000},
        "exclusions": ["flood", "mold"],
    },
}

CLAIMS: dict[str, dict] = {
    "CLM-7001": {"policy_id": "HP-1001", "category": "property", "status": "under review",
                 "summary": "Burst pipe in upstairs bathroom", "adjuster": "R. Vance"},
    "CLM-7002": {"policy_id": "HP-1003", "category": "auto", "status": "approved",
                 "summary": "Hail damage to parked car", "adjuster": "S. Idowu"},
}


def lookup_policy(policy_id: str) -> dict:
    policy = POLICIES.get(policy_id.upper())
    if policy is None:
        return {"error": f"no policy with id {policy_id}"}
    return {"policy_id": policy_id.upper(), **policy}


def claim_status(claim_id: str) -> dict:
    claim = CLAIMS.get(claim_id.upper())
    if claim is None:
        return {"error": f"no claim with id {claim_id}"}
    return {"claim_id": claim_id.upper(), **claim}


def estimate_payout(policy_id: str, category: str, damage_usd: float) -> dict:
    """Payout = damage minus deductible, capped at the category limit."""
    policy = POLICIES.get(policy_id.upper())
    if policy is None:
        return {"error": f"no policy with id {policy_id}"}
    if policy["status"] != "active":
        return {"error": f"policy {policy_id} is {policy['status']}; claims cannot be paid"}
    if category not in policy["limits_usd"]:
        return {"error": f"unknown category {category}"}
    limit = policy["limits_usd"][category]
    payout = max(0.0, min(damage_usd - policy["deductible_usd"], limit))
    return {
        "policy_id": policy_id.upper(), "category": category,
        "damage_usd": damage_usd, "deductible_usd": policy["deductible_usd"],
        "limit_usd": limit, "estimated_payout_usd": payout,
    }


def open_claim(policy_id: str, category: str, summary: str) -> dict:
    """Open a claim with a deterministic id (next number after the existing ones)."""
    policy = POLICIES.get(policy_id.upper())
    if policy is None:
        return {"error": f"no policy with id {policy_id}"}
    if policy["status"] != "active":
        return {"error": f"policy {policy_id} is {policy['status']}; cannot open a claim"}
    claim_id = f"CLM-{7001 + len(CLAIMS)}"
    CLAIMS[claim_id] = {"policy_id": policy_id.upper(), "category": category,
                        "status": "received", "summary": summary, "adjuster": "unassigned"}
    return {"claim_id": claim_id, "status": "received"}
