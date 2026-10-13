"""Offline tests: no provider keys, no Opik (run with OPIK_TRACK_DISABLE=true)."""

import claims_data as data


def setup_function():
    # open_claim mutates the in-memory claim table; restore it between tests.
    for key in [k for k in data.CLAIMS if k not in ("CLM-7001", "CLM-7002")]:
        del data.CLAIMS[key]


def test_lookup_is_case_insensitive_and_reports_unknown():
    assert data.lookup_policy("hp-1001")["holder"] == "Marta Okonkwo"
    assert "error" in data.lookup_policy("HP-9999")


def test_payout_subtracts_deductible_and_caps_at_limit():
    assert data.estimate_payout("HP-1001", "auto", 3_200)["estimated_payout_usd"] == 2_700
    assert data.estimate_payout("HP-1001", "auto", 90_000)["estimated_payout_usd"] == 25_000
    assert data.estimate_payout("HP-1001", "auto", 100)["estimated_payout_usd"] == 0


def test_lapsed_policy_cannot_be_paid_or_claimed():
    assert "lapsed" in data.estimate_payout("HP-1002", "property", 5_000)["error"]
    assert "lapsed" in data.open_claim("HP-1002", "property", "fire")["error"]


def test_open_claim_assigns_next_id_and_is_queryable():
    opened = data.open_claim("HP-1003", "liability", "icy steps")
    assert opened["claim_id"] == "CLM-7003"
    assert data.claim_status("CLM-7003")["status"] == "received"
