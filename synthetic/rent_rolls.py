"""Synthetic cap table (equity ownership) generator.

Kept under the legacy filename `rent_rolls.py` to preserve the package
import shape. Exposes `generate_for_company` which returns a dict matching
pehero.cap_tables row shape.
"""

from __future__ import annotations

import random
from datetime import date


def _last_round_for(rng: random.Random) -> str:
    yr = rng.randint(2018, 2024)
    mo = rng.randint(1, 12)
    return date(yr, mo, 1).isoformat()


def generate_for_company(company: dict, as_of: date, rng: random.Random) -> dict:
    """Return a dict matching pehero.cap_tables row shape (holders, total_shares, post_money)."""
    total_shares = 10_000_000
    post_money = float(company.get("enterprise_value") or 0) * 1.15

    holders = []
    ownership = company.get("ownership", "founder")

    if ownership == "founder":
        founder_shares = int(total_shares * rng.uniform(0.55, 0.78))
        co_founder_shares = int(total_shares * rng.uniform(0.08, 0.15))
        option_pool = int(total_shares * 0.08)
        growth_inv_shares = total_shares - founder_shares - co_founder_shares - option_pool
        holders = [
            {"holder": "Founder / CEO", "class": "Common", "shares": founder_shares,
             "fd_pct": round(100 * founder_shares / total_shares, 2),
             "capital_in": 500_000, "liquidation_pref": 0,
             "last_round": "2015-01-01"},
            {"holder": "Co-Founder / CTO", "class": "Common", "shares": co_founder_shares,
             "fd_pct": round(100 * co_founder_shares / total_shares, 2),
             "capital_in": 100_000, "liquidation_pref": 0,
             "last_round": "2015-01-01"},
            {"holder": "Option Pool", "class": "Options", "shares": option_pool,
             "fd_pct": round(100 * option_pool / total_shares, 2),
             "capital_in": 0, "liquidation_pref": 0,
             "last_round": "2019-06-01"},
            {"holder": "Frontier Growth Partners", "class": "Preferred A",
             "shares": growth_inv_shares,
             "fd_pct": round(100 * growth_inv_shares / total_shares, 2),
             "capital_in": round(post_money * 0.18, 0),
             "liquidation_pref": round(post_money * 0.18, 0),
             "last_round": _last_round_for(rng)},
        ]
    elif ownership == "vc_backed":
        holders = [
            {"holder": "Founder", "class": "Common", "shares": int(total_shares * 0.20),
             "fd_pct": 20.0, "capital_in": 0, "liquidation_pref": 0,
             "last_round": "2017-03-01"},
            {"holder": "Option Pool", "class": "Options", "shares": int(total_shares * 0.12),
             "fd_pct": 12.0, "capital_in": 0, "liquidation_pref": 0,
             "last_round": "2019-06-01"},
            {"holder": "Series A — Accel", "class": "Preferred A",
             "shares": int(total_shares * 0.22), "fd_pct": 22.0,
             "capital_in": round(post_money * 0.10, 0),
             "liquidation_pref": round(post_money * 0.10, 0),
             "last_round": "2019-11-01"},
            {"holder": "Series B — Insight Venture Partners", "class": "Preferred B",
             "shares": int(total_shares * 0.24), "fd_pct": 24.0,
             "capital_in": round(post_money * 0.18, 0),
             "liquidation_pref": round(post_money * 0.18, 0),
             "last_round": "2021-05-01"},
            {"holder": "Series C — Tiger Global", "class": "Preferred C",
             "shares": int(total_shares * 0.22), "fd_pct": 22.0,
             "capital_in": round(post_money * 0.22, 0),
             "liquidation_pref": round(post_money * 0.22, 0),
             "last_round": _last_round_for(rng)},
        ]
    elif ownership == "pe_backed":
        holders = [
            {"holder": "Mgmt Team (rollover)", "class": "Common",
             "shares": int(total_shares * 0.18), "fd_pct": 18.0,
             "capital_in": 0, "liquidation_pref": 0,
             "last_round": "2022-01-01"},
            {"holder": "Option Pool / MIP", "class": "Options",
             "shares": int(total_shares * 0.07), "fd_pct": 7.0,
             "capital_in": 0, "liquidation_pref": 0,
             "last_round": "2022-01-01"},
            {"holder": "Sponsor — Granite Ridge Partners", "class": "Preferred A",
             "shares": int(total_shares * 0.75), "fd_pct": 75.0,
             "capital_in": round(post_money * 0.45, 0),
             "liquidation_pref": round(post_money * 0.45, 0),
             "last_round": "2022-01-01"},
        ]
    elif ownership == "corporate_carve_out":
        holders = [
            {"holder": "Parent — Industrial Conglomerate Inc.", "class": "Common",
             "shares": total_shares, "fd_pct": 100.0,
             "capital_in": 0, "liquidation_pref": 0,
             "last_round": "1998-01-01"},
        ]
    elif ownership == "family":
        holders = [
            {"holder": "Family Trust (Generation II)", "class": "Common",
             "shares": int(total_shares * 0.60), "fd_pct": 60.0,
             "capital_in": 0, "liquidation_pref": 0,
             "last_round": "1985-01-01"},
            {"holder": "Family Trust (Generation III)", "class": "Common",
             "shares": int(total_shares * 0.30), "fd_pct": 30.0,
             "capital_in": 0, "liquidation_pref": 0,
             "last_round": "1985-01-01"},
            {"holder": "Executive Team (Class B)", "class": "Common",
             "shares": int(total_shares * 0.10), "fd_pct": 10.0,
             "capital_in": 0, "liquidation_pref": 0,
             "last_round": "2015-01-01"},
        ]
    else:
        holders = [
            {"holder": "Public Float", "class": "Common",
             "shares": total_shares, "fd_pct": 100.0,
             "capital_in": 0, "liquidation_pref": 0,
             "last_round": None},
        ]

    return {
        "as_of_date": as_of.isoformat(),
        "holders": holders,
        "total_shares": total_shares,
        "post_money": round(post_money, 2),
    }


# Back-compat signature for the legacy property-based caller
def generate_for_property(company: dict, as_of: date, rng: random.Random) -> list[dict]:
    return generate_for_company(company, as_of, rng)["holders"]
