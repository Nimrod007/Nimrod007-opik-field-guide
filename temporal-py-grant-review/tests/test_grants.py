import json
from pathlib import Path

import pytest

from grants import average, check_budget, check_eligibility, decide, parse_scores

APPS = json.loads((Path(__file__).parent.parent / "data" / "applications.json").read_text())


def test_eligibility_rules():
    app = dict(APPS[0])
    assert check_eligibility(app)["eligible"]
    bad = {**app, "county": "Elsewhere", "requested_amount": 20_000, "organization_type": "company"}
    assert len(check_eligibility(bad)["reasons"]) == 3


def test_budget_sums_and_soft_costs():
    assert check_budget(APPS[0], 40_000)["ok"]
    flagged = check_budget(APPS[1], 40_000)
    assert not flagged["ok"]
    assert any("soft costs" in i for i in flagged["issues"])
    assert any("line items total" in i for i in flagged["issues"])


def test_parse_scores_clamps_and_requires_keys():
    s = parse_scores('{"community_need": 9, "feasibility": 0, "inclusion": 3.6, "sustainability": 4}')
    assert s == {"community_need": 5, "feasibility": 1, "inclusion": 4, "sustainability": 4}
    with pytest.raises(KeyError):
        parse_scores('{"community_need": 3}')


def test_decide_paths():
    ok = {"eligible": True, "reasons": []}
    good = {"community_need": 5, "feasibility": 4, "inclusion": 4, "sustainability": 4}
    assert average(good) == 4.25
    assert decide(ok, good, {"ok": True}) == "approve"
    assert decide(ok, good, {"ok": False}) == "revise"
    assert decide({"eligible": False, "reasons": ["x"]}, None, None) == "decline"
