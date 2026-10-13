"""Regenerates data/batches.csv, the fictional Tidewater Ferments batch log.

Deterministic (seeded). Two problems are planted for the agent to find:
  * yeast strain "Kestrel-12" stalls: final gravity stays high, batches get "stuck";
  * fermenter FV-4 ran hot (24-27 C) from 2025-07-01, and those batches came out "off-flavor".
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(4242)

STYLES = {  # style: (OG range, typical yeast strains)
    "Pale Ale": ((1.050, 1.058), ["Harbor-US05", "Kestrel-12"]),
    "Saison": ((1.056, 1.066), ["Marlow-Saison", "Kestrel-12"]),
    "Stout": ((1.062, 1.076), ["Harbor-US05", "Cove-English"]),
    "Hefeweizen": ((1.046, 1.054), ["Marlow-Wheat"]),
    "Lager": ((1.044, 1.052), ["Cove-Lager34"]),
}
FERMENTERS = ["FV-1", "FV-2", "FV-3", "FV-4"]

rows = []
start = date(2025, 1, 6)
for i in range(120):
    d = start + timedelta(days=i * 2 + random.randint(0, 1))
    style = random.choice(list(STYLES))
    (lo, hi), yeasts = STYLES[style]
    yeast = random.choice(yeasts)
    fv = random.choice(FERMENTERS)
    og = round(random.uniform(lo, hi), 3)
    temp = round(random.gauss(18.5 if style != "Lager" else 11.5, 0.7), 1)
    attenuation = random.uniform(0.74, 0.80)
    outcome = "passed"
    if yeast == "Kestrel-12":
        attenuation = random.uniform(0.40, 0.52)  # stalled ferment
        outcome = "stuck"
    if fv == "FV-4" and d >= date(2025, 7, 1):
        temp = round(random.uniform(24.0, 27.0), 1)
        outcome = "off-flavor"
    if outcome == "passed" and random.random() < 0.04:
        outcome = "dumped"  # background noise: contamination
    fg = round(1 + (og - 1) * (1 - attenuation), 3)
    rows.append({
        "batch_id": f"TF-{i + 1:03d}", "brew_date": d.isoformat(), "beer_style": style,
        "yeast_strain": yeast, "fermenter": fv, "original_gravity": f"{og:.3f}",
        "final_gravity": f"{fg:.3f}", "ferment_temp_c": temp,
        "days_fermented": random.randint(9, 16), "volume_liters": random.choice([400, 400, 800]),
        "outcome": outcome,
    })

out = Path(__file__).parent / "data" / "batches.csv"
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"wrote {len(rows)} batches to {out}")
