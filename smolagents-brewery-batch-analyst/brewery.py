"""Helpers for the brewery batch log: loading, ABV maths, and the agent briefing."""
from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).parent / "data" / "batches.csv"


def abv(original_gravity: float, final_gravity: float) -> float:
    """Standard homebrew estimate: (OG - FG) * 131.25, in percent."""
    return round((original_gravity - final_gravity) * 131.25, 2)


def load_batches(path: Path = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["brew_date"])
    df["attenuation"] = (df.original_gravity - df.final_gravity) / (df.original_gravity - 1)
    return df


BRIEFING = f"""\
You are the data analyst for Tidewater Ferments, a craft brewery.
The fermentation batch log for 2025 is the CSV at: {CSV_PATH}

Columns: batch_id, brew_date (YYYY-MM-DD), beer_style, yeast_strain, fermenter,
original_gravity, final_gravity (specific gravity, e.g. 1.052), ferment_temp_c,
days_fermented, volume_liters, outcome (passed | stuck | off-flavor | dumped).
Attenuation = (original_gravity - final_gravity) / (original_gravity - 1).

Load it with pandas and answer with concrete numbers from the data.
Give your final answer as one or two plain sentences, not a raw Python object.
"""

QUESTIONS = [
    "Which yeast strain has the lowest average attenuation, and what share "
    "of its batches ended with outcome 'stuck'?",
    "Which fermenter has the most 'off-flavor' batches, and from what date "
    "did they start? Compare its average ferment_temp_c before and after that date.",
    "What is the average ABV per beer style, using ABV = (original_gravity - "
    "final_gravity) * 131.25? List the styles from strongest to weakest.",
]
