"""Loads the offline season data and turns it into plain text for the crew."""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def read_rows(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(newline="") as f:
        return list(csv.DictReader(f))


def production_cost(play: dict[str, str]) -> int:
    """Royalties plus set cost: the hard cash a play needs before rehearsals."""
    return int(play["royalty_usd"]) + int(play["set_cost_usd"])


def spendable_budget(lines: list[dict[str, str]]) -> int:
    """Income minus fixed costs, marketing and the untouchable reserve."""
    income = sum(
        int(r["amount_usd"])
        for r in lines
        if r["line"].split()[0] in {"Ticket", "Subscriptions", "Grants", "Donations"}
    )
    outgoing = sum(
        int(r["amount_usd"])
        for r in lines
        if r["line"].startswith(("Fixed", "Marketing", "Contingency"))
    )
    return income - outgoing


def format_plays(plays: list[dict[str, str]]) -> str:
    return "\n".join(
        f"- {p['title']} ({p['genre']}, cast {p['cast_size']}, "
        f"production cost ${production_cost(p):,}, {p['rehearsal_weeks']} rehearsal weeks): {p['notes']}"
        for p in plays
    )


def format_budget(lines: list[dict[str, str]]) -> str:
    rows = "\n".join(f"- {r['line']}: ${int(r['amount_usd']):,} ({r['note']})" for r in lines)
    return f"{rows}\nSpendable on productions: ${spendable_budget(lines):,}"


def format_calendar(slots: list[dict[str, str]]) -> str:
    return "\n".join(f"- {s['slot']}: {s['start']} to {s['end']} ({s['constraint']})" for s in slots)


def load_inputs() -> dict[str, str]:
    return {
        "plays": format_plays(read_rows("play_candidates.csv")),
        "budget": format_budget(read_rows("budget.csv")),
        "calendar": format_calendar(read_rows("venue_calendar.csv")),
    }
