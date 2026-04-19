"""Monthly financial statements per company — deterministic growth trajectory.

Kept under the legacy filename `t12s.py` for import compatibility. Returns
24 months of monthly P&L data for each company, suitable for LTM + trailing
normalization.
"""

from __future__ import annotations

import math
import random
from datetime import date
from dateutil.relativedelta import relativedelta


OPEX_SPLIT_BY_SECTOR = {
    "software": {"sales": 0.35, "marketing": 0.20, "rnd": 0.28, "ga": 0.12, "other": 0.05},
    "healthcare": {"sales": 0.18, "marketing": 0.08, "rnd": 0.04, "ga": 0.20, "other": 0.50},  # bulk of opex is labor/clinical
    "industrials": {"sales": 0.14, "marketing": 0.06, "rnd": 0.04, "ga": 0.10, "other": 0.66},
    "consumer": {"sales": 0.15, "marketing": 0.22, "rnd": 0.04, "ga": 0.09, "other": 0.50},
    "business_services": {"sales": 0.20, "marketing": 0.10, "rnd": 0.02, "ga": 0.15, "other": 0.53},
    "financial_services": {"sales": 0.22, "marketing": 0.08, "rnd": 0.02, "ga": 0.28, "other": 0.40},
}

COGS_RATIO_BY_SECTOR = {
    "software": 0.22,
    "healthcare": 0.55,
    "industrials": 0.62,
    "consumer": 0.48,
    "business_services": 0.40,
    "financial_services": 0.35,
}


def _seasonal(month: int, sector: str) -> float:
    if sector == "consumer":
        return 1.0 + 0.10 * math.sin((month - 10) / 12 * 2 * math.pi)  # Q4 spike
    if sector == "software":
        return 1.0 + 0.04 * math.sin((month - 11) / 12 * 2 * math.pi)  # year-end deal rush
    if sector == "healthcare":
        return 1.0 + 0.03 * math.sin((month - 1) / 12 * 2 * math.pi)
    return 1.0


def generate_for_property(company: dict, end_month: date, rng: random.Random) -> list[dict]:
    """Return 24 months of monthly financials. (Name kept for back-compat.)"""
    return generate_for_company(company, end_month, rng, months=24)


def generate_for_company(company: dict, end_month: date, rng: random.Random,
                          *, months: int = 24) -> list[dict]:
    sector = company["sector"]
    annual_rev = float(company["revenue_ltm"])
    annual_ebitda = float(company["ebitda_ltm"])
    growth = float(company["growth_rate"]) / 100
    base_margin = annual_ebitda / max(1, annual_rev)
    cogs_ratio = COGS_RATIO_BY_SECTOR[sector]
    opex_split = OPEX_SPLIT_BY_SECTOR[sector]

    base_monthly = annual_rev / 12 / (1 + growth / 2)  # mid-period for LTM
    rows: list[dict] = []

    for i in range(months - 1, -1, -1):
        m = end_month - relativedelta(months=i)
        # monthly revenue grows on trend; months further from end have smaller trend
        trend_factor = (1 + growth) ** ((months - 1 - i) / 12)
        seasonal = _seasonal(m.month, sector)
        noise = rng.uniform(0.93, 1.07)
        revenue = base_monthly * trend_factor * seasonal * noise
        cogs = revenue * cogs_ratio * rng.uniform(0.96, 1.04)
        gp = revenue - cogs

        opex_total = revenue * (1 - base_margin - cogs_ratio) * rng.uniform(0.94, 1.07)
        opex = {k: round(opex_total * v, 2) for k, v in opex_split.items()}

        ebitda = gp - sum(opex.values())

        # Add back adjustments (one-time items, owner comp)
        adjustments = {}
        if rng.random() < 0.25:
            adjustments["owner_comp"] = round(revenue * rng.uniform(0.005, 0.015), 2)
        if rng.random() < 0.12:
            adjustments["one_time_legal"] = round(revenue * rng.uniform(0.002, 0.008), 2)
        if rng.random() < 0.08:
            adjustments["discontinued_product"] = round(revenue * rng.uniform(0.005, 0.015), 2)
        adj_total = sum(adjustments.values())
        adj_ebitda = ebitda + adj_total

        # Optional SaaS metrics
        arr = None
        gross_retention = None
        net_retention = None
        if sector == "software":
            arr = round(revenue * 12 * 0.92, 2)
            gross_retention = round(rng.uniform(88.0, 95.0), 2)
            net_retention = round(gross_retention + rng.uniform(6.0, 18.0), 2)

        rows.append({
            "month": m.replace(day=1).isoformat(),
            "revenue": round(revenue, 2),
            "cogs": round(cogs, 2),
            "gross_profit": round(gp, 2),
            "opex": opex,
            "ebitda": round(ebitda, 2),
            "adjustments": adjustments,
            "adj_ebitda": round(adj_ebitda, 2),
            "arr": arr,
            "gross_retention": gross_retention,
            "net_retention": net_retention,
        })
    return rows
