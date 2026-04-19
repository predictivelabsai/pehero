"""24 months of sector-level market signals for PE."""

from __future__ import annotations

import math
import random
from datetime import date
from dateutil.relativedelta import relativedelta

METRICS = ["ev_ebitda_median", "ev_revenue_median", "deal_volume", "fundraising_close_time",
           "exit_multiples", "hold_period"]


def _baseline(sector: str) -> dict[str, float]:
    # baseline sector multiples (at start of window)
    ev_ebitda = {
        "software": 14.0, "healthcare": 12.0, "industrials": 9.5,
        "consumer": 10.5, "business_services": 10.0, "financial_services": 11.5,
    }[sector]
    ev_rev = {
        "software": 4.8, "healthcare": 1.6, "industrials": 1.1,
        "consumer": 1.3, "business_services": 1.5, "financial_services": 2.2,
    }[sector]
    deal_volume = {  # deals per month in that sector
        "software": 55, "healthcare": 42, "industrials": 38,
        "consumer": 28, "business_services": 48, "financial_services": 22,
    }[sector]
    return {
        "ev_ebitda_median": ev_ebitda,
        "ev_revenue_median": ev_rev,
        "deal_volume": deal_volume,
        "fundraising_close_time": 14.0,    # months to close a new fund
        "exit_multiples": ev_ebitda - 1.0,
        "hold_period": 5.2,                 # average held-asset hold period in years
    }


def generate(companies: list[dict], months: int = 24, seed: int = 42) -> list[dict]:
    rng = random.Random(seed + 7)
    rows: list[dict] = []
    seen: set[tuple] = set()

    sectors = {c["sector"] for c in companies}
    sub_sectors_by_sector: dict[str, set[str]] = {}
    for c in companies:
        sub_sectors_by_sector.setdefault(c["sector"], set()).add(c["sub_sector"])

    today = date.today().replace(day=1)

    for sector in sectors:
        base = _baseline(sector)
        for sub in sub_sectors_by_sector.get(sector, {""}):
            for metric in METRICS:
                for i in range(months, 0, -1):
                    m = today - relativedelta(months=i)
                    t = i / months
                    seasonal = 0.05 * math.sin(i / 6 * math.pi)
                    trend = {
                        "ev_ebitda_median": -1.5 * (1 - t),     # multiples compressed recently
                        "ev_revenue_median": -0.4 * (1 - t),
                        "deal_volume": -10 * (1 - t),           # deal volume softened
                        "fundraising_close_time": 6 * (1 - t),  # fundraising taking longer
                        "exit_multiples": -1.0 * (1 - t),
                        "hold_period": 0.8 * (1 - t),           # holds extended
                    }[metric]
                    value = base[metric] * (1 + seasonal) + trend + rng.uniform(-0.2, 0.2)
                    key = (sector, sub, metric, m)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({
                        "sector": sector,
                        "sub_sector": sub,
                        "metric": metric,
                        "value": round(value, 3),
                        "as_of_date": m.isoformat(),
                        "source": rng.choice(["PitchBook", "Preqin", "Bain Private Equity Report",
                                              "Cambridge Associates", "Burgiss"]),
                    })
    return rows
