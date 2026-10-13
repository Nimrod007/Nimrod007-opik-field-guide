import opik

from season_data import (
    format_budget, format_plays, load_inputs, production_cost, read_rows, spendable_budget,
)


def test_production_cost_adds_royalty_and_set():
    assert production_cost({"royalty_usd": "1800", "set_cost_usd": "2600"}) == 4400


def test_spendable_budget_excludes_fixed_costs_and_reserve():
    assert spendable_budget(read_rows("budget.csv")) == 37_500


def test_formatters_mention_every_row():
    plays = read_rows("play_candidates.csv")
    text = format_plays(plays)
    assert all(p["title"] in text for p in plays)
    assert "Spendable on productions: $37,500" in format_budget(read_rows("budget.csv"))


def test_load_inputs_has_all_template_keys():
    assert set(load_inputs()) == {"plays", "budget", "calendar"}


@opik.track
def traced_total() -> int:
    return spendable_budget(read_rows("budget.csv"))


def test_traced_function_runs_with_tracking_disabled():
    # @opik.track is a no-op wrapper when OPIK_TRACK_DISABLE=true.
    assert traced_total() == 37_500
