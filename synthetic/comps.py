"""Transaction + trading comps per company."""

from __future__ import annotations

import random
from datetime import date, timedelta


PE_ACQUIRERS = [
    "Thoma Bravo", "Vista Equity Partners", "Hellman & Friedman", "KKR", "Apollo Global",
    "Bain Capital", "Carlyle Group", "Apax", "Clearlake", "Francisco Partners",
    "Silver Lake", "Warburg Pincus", "CVC Capital", "Permira", "Genstar",
    "Audax Private Equity", "Summit Partners", "TA Associates",
    "Frontier Growth Partners", "Granite Ridge Partners", "Ridgeline Capital",
]
STRATEGIC_ACQUIRERS = [
    "Oracle", "Salesforce", "Microsoft", "IBM", "ServiceNow", "Adobe",
    "Siemens", "Emerson", "Honeywell", "Parker Hannifin", "Roper Technologies",
    "UnitedHealth", "HCA Healthcare", "CVS Health", "Stryker", "Medtronic",
    "Clorox", "Procter & Gamble", "Nestle", "Pepsico",
]

TARGETS_BY_SECTOR = {
    "software": ["AppWorks", "DataPrism", "Clarion AI", "Dataflow Labs", "NovaSoft",
                 "Acuity Analytics", "Stellar SaaS", "Crestwave", "Vantedge", "Beacon AI"],
    "healthcare": ["ClearPath Health", "Hampton Medical", "Northfield Care", "Pine Valley Clinics",
                   "Summit Specialty", "Meadowbrook Health"],
    "industrials": ["Apex Industrial", "Sterling Manufacturing", "Foundry Works", "Ironpeak Industries",
                    "Granite Services", "Hudson Precision"],
    "consumer": ["Riverbend Brands", "Harbor Kitchen", "Fieldhouse Goods", "Wildroot Co"],
    "business_services": ["Apex Services Group", "Stride Solutions", "Corbin Partners", "Gateway Group"],
    "financial_services": ["Ridgeline Capital Partners", "Anchor Wealth", "Keystone Financial"],
}


def _sector_multiple(sector: str, rng: random.Random) -> float:
    base = {
        "software": 13.0,
        "healthcare": 11.0,
        "industrials": 9.0,
        "consumer": 10.0,
        "business_services": 10.0,
        "financial_services": 11.0,
    }[sector]
    return round(base + rng.uniform(-2.5, 3.5), 2)


def generate_sales_comps(company: dict, rng: random.Random, count: int = 6) -> list[dict]:
    """M&A transaction comps for the company's sector. Stored in pehero.transaction_comps."""
    return generate_transaction_comps(company, rng, count)


def generate_transaction_comps(company: dict, rng: random.Random, count: int = 6) -> list[dict]:
    sector = company["sector"]
    sub = company["sub_sector"]
    target_names = TARGETS_BY_SECTOR.get(sector, ["Acme Co"])
    rows = []
    for _ in range(count):
        delta_days = rng.randint(30, 900)
        announce_date = date.today() - timedelta(days=delta_days)
        close_date = announce_date + timedelta(days=rng.randint(30, 180))
        target_rev = rng.uniform(20_000_000, 320_000_000)
        target_margin = rng.uniform(10, 30)
        target_ebitda = target_rev * target_margin / 100
        ev_ebitda = _sector_multiple(sector, rng)
        ev = target_ebitda * ev_ebitda
        ev_rev = ev / target_rev
        deal_type = rng.choice(["pe_buyout", "pe_buyout", "pe_buyout", "strategic", "growth"])
        acquirer = rng.choice(PE_ACQUIRERS if deal_type != "strategic" else STRATEGIC_ACQUIRERS)

        rows.append({
            "target_name": rng.choice(target_names) + " " + rng.choice(["Holdings", "Inc", "LLC", "Group", "Co"]),
            "acquirer": acquirer,
            "sector": sector,
            "sub_sector": sub,
            "country": company["country"],
            "announce_date": announce_date.isoformat(),
            "close_date": close_date.isoformat(),
            "enterprise_value": round(ev, 2),
            "revenue": round(target_rev, 2),
            "ebitda": round(target_ebitda, 2),
            "ev_revenue": round(ev_rev, 2),
            "ev_ebitda": round(ev_ebitda, 2),
            "deal_type": deal_type,
            "source": rng.choice(["PitchBook", "MergerMarket", "Capital IQ", "Press Release"]),
        })
    return rows


# Back-compat wrapper used by synthetic/generate._insert_comps
def generate_rent_comps(company: dict, rng: random.Random, count: int = 6) -> list[dict]:
    """Trading comps (public peers) for the company's sector. Stored in pehero.trading_comps."""
    return generate_trading_comps(company, rng, count)


def generate_trading_comps(company: dict, rng: random.Random, count: int = 6) -> list[dict]:
    sector = company["sector"]
    tickers = {
        "software": ["CRM", "NOW", "DDOG", "SNOW", "TEAM", "HUBS", "WDAY", "VEEV"],
        "healthcare": ["UNH", "HCA", "ELV", "VEEV", "TDOC", "HUM"],
        "industrials": ["ROP", "AME", "DOV", "EMR", "ITW", "PNR"],
        "consumer": ["PG", "CLX", "KHC", "GIS"],
        "business_services": ["ACN", "CTAS", "WM", "RSG"],
        "financial_services": ["MMC", "AJG", "BRO", "WTW"],
    }[sector]

    rows = []
    for _ in range(count):
        ticker = rng.choice(tickers)
        market_cap = rng.uniform(1_500_000_000, 80_000_000_000)
        ev = market_cap * rng.uniform(0.95, 1.25)
        rev_ltm = market_cap / rng.uniform(3, 12)
        ebitda_margin = rng.uniform(15, 35)
        ebitda_ltm = rev_ltm * ebitda_margin / 100
        ev_rev = ev / rev_ltm
        ev_ebitda = ev / ebitda_ltm
        rev_growth = rng.uniform(4, 24)
        rows.append({
            "comp_name": f"Trading comp — {ticker}",
            "ticker": ticker,
            "peer_name": ticker,
            "sector": sector,
            "market_cap": round(market_cap, 2),
            "ev": round(ev, 2),
            "revenue_ltm": round(rev_ltm, 2),
            "ebitda_ltm": round(ebitda_ltm, 2),
            "ev_revenue": round(ev_rev, 2),
            "ev_ebitda": round(ev_ebitda, 2),
            "rev_growth": round(rev_growth, 2),
            "ebitda_margin": round(ebitda_margin, 2),
            "as_of_date": date.today().isoformat(),
            # Legacy fields kept empty for old callers
            "unit_type": ticker,
            "sqft": None,
            "rent": None,
            "rent_per_sqft": None,
            "effective_date": date.today().isoformat(),
            "source": rng.choice(["Capital IQ", "FactSet", "Bloomberg"]),
        })
    return rows
