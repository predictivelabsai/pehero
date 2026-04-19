"""Synthetic LP / investor CRM — 60 PE LP contacts."""

from __future__ import annotations

import random
from datetime import date, timedelta

FIRST_NAMES = ["Priya", "Marcus", "Sarah", "Daniel", "Aisha", "Jon", "Elena", "Hiroshi",
               "Fiona", "Rashid", "Margaux", "Theo", "Olivia", "Kenji", "Ines", "Tomas",
               "Amara", "Levi", "Noor", "Ida", "Caleb", "Yuki", "Lior", "Petra", "Sebastian"]
LAST_NAMES = ["Chen", "Patel", "Rodriguez", "Sanchez", "Müller", "Okafor", "Bergström",
              "Khan", "Kovač", "Hassan", "Nakamura", "Levine", "Ferreira", "Dubois",
              "Kwon", "Alvarez", "Weinstein", "Reinhardt", "Park"]

FIRMS_BY_TYPE = {
    "pension": ["CalPERS", "CalSTRS", "NYSCRF", "OMERS", "OTPP", "CPP Investments",
                "ABP", "New Mexico SIC", "Texas Municipal Retirement System",
                "Ohio Public Employees Retirement", "LACERA"],
    "endowment": ["Yale Investments Office", "Stanford Mgmt Co", "Harvard Management Co",
                  "MIT Investment Management", "Princeton University Investment Co",
                  "Duke Endowment", "Notre Dame Investment Office"],
    "fof": ["HarbourVest Partners", "Adams Street Partners", "Pathway Capital Management",
            "Neuberger Berman Private Markets", "Hamilton Lane", "StepStone Group",
            "Aberdeen Standard Private Equity"],
    "family_office": ["Cascade Family Office", "Brightwater Capital", "Thornfield Wealth",
                      "Grayson Family Trust", "Castle Pines Advisors", "Haverford Group",
                      "Silvercloud Family Office"],
    "sovereign": ["GIC", "Mubadala", "Temasek", "QIA", "ADIA", "KIC", "Wealth Fund of Norway"],
    "insurance": ["MetLife", "Prudential Capital Group", "Allianz Global Investors",
                  "Nippon Life", "AIG Asset Management"],
    "hnw": ["iCapital", "Moonfare", "iOwn Private Wealth", "Connor Clark & Lunn Private Capital"],
}
LP_TYPES = list(FIRMS_BY_TYPE.keys())
STAGES = ["cold", "qualified", "meeting", "dd", "committed", "closed", "passed"]
FOCI = ["buyout", "growth", "special_sits", "multi_strategy"]
GEOS = ["North America", "Europe", "Global", "DACH", "Nordics", "Asia-Pacific"]


def generate(count: int = 60, seed: int = 42) -> list[dict]:
    rng = random.Random(seed + 11)
    rows: list[dict] = []
    for i in range(count):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        lp_type = rng.choice(LP_TYPES)
        firm = rng.choice(FIRMS_BY_TYPE[lp_type])
        stage = rng.choices(STAGES, weights=[8, 5, 4, 4, 3, 2, 3])[0]
        # Commitment size varies by LP type
        type_check = {
            "pension": [25_000_000, 50_000_000, 100_000_000, 250_000_000],
            "endowment": [10_000_000, 25_000_000, 50_000_000, 100_000_000],
            "fof": [25_000_000, 50_000_000, 75_000_000, 150_000_000],
            "family_office": [5_000_000, 10_000_000, 25_000_000, 50_000_000],
            "sovereign": [100_000_000, 250_000_000, 500_000_000],
            "insurance": [50_000_000, 100_000_000, 200_000_000],
            "hnw": [500_000, 1_000_000, 2_500_000, 5_000_000],
        }[lp_type]
        commitment = rng.choice(type_check)
        aum = commitment * rng.randint(20, 200)
        focus = rng.choice(FOCI)
        geo = rng.choice(GEOS)
        last_touch = (date.today() - timedelta(days=rng.randint(3, 180))).isoformat()
        notes_pool = [
            f"Focuses on {focus.replace('_', ' ')} in {geo}. Prefers funds $500M-$2B.",
            f"Introduced by {rng.choice(['placement agent', 'warm intro', 'Selects', 'co-invest LP'])}. Looking for North America buyout exposure.",
            "Reups most recent vintage; high priority for next close.",
            f"Closed last fund with us at {rng.randint(14, 22)}% net IRR; repeat LP.",
            "Requests ESG reporting + DEI metrics as part of DDQ.",
            f"Allocates quarterly; next IC is {rng.choice(['March','July','November'])}.",
            "Seeking co-invest alongside fund commitment; 2x commitment in co-invest rights.",
        ]
        rows.append({
            "name": f"{first} {last}",
            "firm": firm,
            "lp_type": lp_type,
            "email": f"{first.lower()}.{last.lower().replace(' ', '')}@{firm.split()[0].lower()}.com",
            "commitment_size": commitment,
            "stage": stage,
            "focus": focus,
            "geography": geo,
            "aum": aum,
            "last_touch": last_touch,
            "notes": rng.choice(notes_pool),
        })
    return rows
