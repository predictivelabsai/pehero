"""Market / comp tools — PE transaction comps, public trading comps, sector signals."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db import fetch_all, fetch_one


class CompArgs(BaseModel):
    slug_or_id: Optional[str] = Field(default=None, description="Anchor company (optional).")
    sector: Optional[str] = Field(default=None)
    sub_sector: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)
    min_ev: Optional[float] = Field(default=None)
    max_ev: Optional[float] = Field(default=None)
    limit: int = Field(default=8, ge=1, le=25)


def _resolve_cid(slug_or_id: Optional[str]) -> Optional[int]:
    if not slug_or_id:
        return None
    try:
        return int(slug_or_id)
    except (TypeError, ValueError):
        row = fetch_one("SELECT id FROM pehero.companies WHERE slug = %s", (slug_or_id,))
        return row["id"] if row else None


def _find_transaction_comps(**kw) -> str:
    args = CompArgs(**kw)
    sql = ["SELECT target_name, acquirer, sector, sub_sector, country, announce_date, "
           "close_date, enterprise_value, revenue, ebitda, ev_revenue, ev_ebitda, deal_type, source "
           "FROM pehero.transaction_comps WHERE TRUE"]
    params: list = []
    if args.slug_or_id:
        cid = _resolve_cid(args.slug_or_id)
        if cid:
            sql.append("AND company_id = %s"); params.append(cid)
    if args.sector:
        sql.append("AND sector = %s"); params.append(args.sector.lower())
    if args.sub_sector:
        sql.append("AND sub_sector ILIKE %s"); params.append(args.sub_sector)
    if args.country:
        sql.append("AND country ILIKE %s"); params.append(args.country)
    if args.min_ev is not None:
        sql.append("AND enterprise_value >= %s"); params.append(args.min_ev)
    if args.max_ev is not None:
        sql.append("AND enterprise_value <= %s"); params.append(args.max_ev)
    sql.append("ORDER BY announce_date DESC NULLS LAST LIMIT %s"); params.append(args.limit)
    rows = fetch_all(" ".join(sql), tuple(params))
    if not rows:
        return "No transaction comps found."
    rows2 = [
        {
            "target_name": r["target_name"], "acquirer": r["acquirer"],
            "sector": r["sector"], "sub_sector": r["sub_sector"],
            "country": r["country"],
            "announce_date": str(r["announce_date"]) if r["announce_date"] else None,
            "enterprise_value": float(r["enterprise_value"]) if r["enterprise_value"] else None,
            "revenue": float(r["revenue"]) if r["revenue"] else None,
            "ebitda": float(r["ebitda"]) if r["ebitda"] else None,
            "ev_revenue": float(r["ev_revenue"]) if r["ev_revenue"] else None,
            "ev_ebitda": float(r["ev_ebitda"]) if r["ev_ebitda"] else None,
            "deal_type": r["deal_type"], "source": r["source"],
        } for r in rows
    ]
    evs_rev = [r["ev_revenue"] for r in rows2 if r["ev_revenue"]]
    evs_eb = [r["ev_ebitda"] for r in rows2 if r["ev_ebitda"]]
    avg_rev = round(sum(evs_rev) / max(1, len(evs_rev)), 2) if evs_rev else None
    avg_eb = round(sum(evs_eb) / max(1, len(evs_eb)), 2) if evs_eb else None
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": "Transaction comps",
        "subtitle": f"{len(rows2)} deals · avg EV/EBITDA {avg_eb}x · avg EV/Rev {avg_rev}x",
        "columns": ["target_name", "acquirer", "sector", "sub_sector", "announce_date",
                    "enterprise_value", "revenue", "ebitda", "ev_revenue", "ev_ebitda",
                    "deal_type", "source"],
        "rows": rows2,
        "summary": {"avg_ev_ebitda": avg_eb, "avg_ev_revenue": avg_rev},
    })


find_transaction_comps = StructuredTool.from_function(
    func=_find_transaction_comps,
    name="find_transaction_comps",
    description="Return precedent M&A transaction comps for a company (or free-form by sector, sub_sector, country, EV range). Outputs a table with average EV/EBITDA + EV/Revenue.",
    args_schema=CompArgs,
)
# Back-compat alias
find_sales_comps = find_transaction_comps


class TradingCompArgs(BaseModel):
    slug_or_id: Optional[str] = None
    sector: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=25)


def _find_trading_comps(**kw) -> str:
    args = TradingCompArgs(**kw)
    sql = ["SELECT ticker, peer_name, sector, market_cap, ev, revenue_ltm, ebitda_ltm, "
           "ev_revenue, ev_ebitda, rev_growth, ebitda_margin, as_of_date, source "
           "FROM pehero.trading_comps WHERE TRUE"]
    params: list = []
    cid = _resolve_cid(args.slug_or_id)
    if cid:
        sql.append("AND company_id = %s"); params.append(cid)
    if args.sector:
        sql.append("AND sector = %s"); params.append(args.sector.lower())
    sql.append("ORDER BY as_of_date DESC LIMIT %s"); params.append(args.limit)
    rows = fetch_all(" ".join(sql), tuple(params))
    if not rows:
        return "No trading comps found."
    rows2 = [
        {
            "ticker": r["ticker"], "peer_name": r["peer_name"], "sector": r["sector"],
            "market_cap": float(r["market_cap"]) if r["market_cap"] else None,
            "ev": float(r["ev"]) if r["ev"] else None,
            "revenue_ltm": float(r["revenue_ltm"]) if r["revenue_ltm"] else None,
            "ebitda_ltm": float(r["ebitda_ltm"]) if r["ebitda_ltm"] else None,
            "ev_revenue": float(r["ev_revenue"]) if r["ev_revenue"] else None,
            "ev_ebitda": float(r["ev_ebitda"]) if r["ev_ebitda"] else None,
            "rev_growth": float(r["rev_growth"]) if r["rev_growth"] else None,
            "ebitda_margin": float(r["ebitda_margin"]) if r["ebitda_margin"] else None,
            "as_of_date": str(r["as_of_date"]) if r["as_of_date"] else None,
            "source": r["source"],
        } for r in rows
    ]
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": "Public trading comps",
        "columns": ["ticker", "peer_name", "sector", "market_cap", "ev", "revenue_ltm",
                    "ebitda_ltm", "ev_revenue", "ev_ebitda", "rev_growth", "ebitda_margin",
                    "as_of_date", "source"],
        "rows": rows2,
    })


find_trading_comps = StructuredTool.from_function(
    func=_find_trading_comps,
    name="find_trading_comps",
    description="Return public trading comps for a company or by sector — market cap, EV, EV/Revenue, EV/EBITDA, growth, margin.",
    args_schema=TradingCompArgs,
)
# Back-compat alias
find_rent_comps = find_trading_comps


class MarketSignalsArgs(BaseModel):
    sector: str
    sub_sector: Optional[str] = None
    metric: Optional[str] = Field(
        default=None,
        description="ev_ebitda_median | ev_revenue_median | deal_volume | fundraising_close_time | exit_multiples | hold_period",
    )


def _fetch_market_signals(**kw) -> str:
    args = MarketSignalsArgs(**kw)
    sql = ["SELECT sector, sub_sector, metric, value, as_of_date, source "
           "FROM pehero.market_signals WHERE sector = %s"]
    params: list = [args.sector.lower()]
    if args.sub_sector:
        sql.append("AND sub_sector ILIKE %s"); params.append(args.sub_sector)
    if args.metric:
        sql.append("AND metric = %s"); params.append(args.metric)
    sql.append("ORDER BY as_of_date DESC LIMIT 50")
    rows = fetch_all(" ".join(sql), tuple(params))
    if not rows:
        return "No market signals for that filter."
    rows2 = [{"metric": r["metric"], "sub_sector": r["sub_sector"],
              "value": float(r["value"]) if r["value"] is not None else None,
              "as_of_date": str(r["as_of_date"]), "source": r["source"]} for r in rows]
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": f"{args.sector.title()} sector signals",
        "subtitle": args.metric or "all metrics",
        "columns": ["metric", "sub_sector", "value", "as_of_date", "source"],
        "rows": rows2,
    })


fetch_market_signals = StructuredTool.from_function(
    func=_fetch_market_signals,
    name="fetch_market_signals",
    description="Fetch sector-level market signals (EV/EBITDA median, deal volume, fundraising close time, exit multiples, hold period) for a sector + sub_sector.",
    args_schema=MarketSignalsArgs,
)
