"""Cap-table tools: parse/summarize/waterfall.

Historically named `rentroll` (from the CRE origins); now reads
pehero.cap_tables (equity ownership snapshots).
"""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db import fetch_one


class CompanySlugArgs(BaseModel):
    slug_or_id: str = Field(description="Company slug or numeric id.")


def _load_cap_table(slug_or_id: str):
    try:
        cid = int(slug_or_id)
        row = fetch_one(
            "SELECT c.id, c.name, c.sector, ct.as_of_date, ct.holders, ct.total_shares, ct.post_money "
            "FROM pehero.companies c "
            "JOIN pehero.cap_tables ct ON ct.company_id = c.id "
            "WHERE c.id = %s ORDER BY ct.as_of_date DESC LIMIT 1",
            (cid,),
        )
    except (TypeError, ValueError):
        row = fetch_one(
            "SELECT c.id, c.name, c.sector, ct.as_of_date, ct.holders, ct.total_shares, ct.post_money "
            "FROM pehero.companies c "
            "JOIN pehero.cap_tables ct ON ct.company_id = c.id "
            "WHERE c.slug = %s ORDER BY ct.as_of_date DESC LIMIT 1",
            (slug_or_id,),
        )
    return row


def _summarize_cap_table(slug_or_id: str) -> str:
    row = _load_cap_table(slug_or_id)
    if not row:
        return "No cap table for that company."
    holders = row["holders"] or []
    total_shares = row["total_shares"] or sum(h.get("shares", 0) for h in holders) or 1

    # top holders
    ranked = sorted(holders, key=lambda h: h.get("fd_pct") or 0, reverse=True)[:10]

    total_liq_pref = sum(h.get("liquidation_pref") or 0 for h in holders)
    total_capital_in = sum(h.get("capital_in") or 0 for h in holders)
    options_overhang = sum(h.get("shares", 0) for h in holders if (h.get("class") or "").lower() in {"options", "warrant"}) / total_shares * 100

    summary = {
        "company": row["name"],
        "as_of": str(row["as_of_date"]),
        "total_holders": len(holders),
        "total_shares": total_shares,
        "post_money": float(row["post_money"]) if row["post_money"] else None,
        "capital_invested_total": total_capital_in,
        "total_liquidation_preference": total_liq_pref,
        "options_warrants_overhang_pct": round(options_overhang, 1),
    }
    artifact = {
        "kind": "table",
        "title": f"Cap table — {row['name']}",
        "subtitle": f"As of {row['as_of_date']} · {len(holders)} holders",
        "columns": ["holder", "class", "shares", "fd_pct", "capital_in", "liquidation_pref", "last_round"],
        "rows": ranked,
    }
    return "__ARTIFACT__" + json.dumps({"summary": summary, **artifact}, default=str)


summarize_cap_table = StructuredTool.from_function(
    func=_summarize_cap_table,
    name="summarize_cap_table",
    description="Load the most recent cap table for a company and return ownership, liquidation prefs, "
                "and a top-10 holders table. Emits a right-pane artifact with the cap table.",
    args_schema=CompanySlugArgs,
)


def _waterfall(slug_or_id: str) -> str:
    """Liquidation waterfall at a given exit value."""
    row = _load_cap_table(slug_or_id)
    if not row:
        return "No cap table for that company."
    holders = row["holders"] or []
    # simple single-priority liquidation preference waterfall
    # (synthetic data uses 1x non-participating preferred by default)
    sorted_holders = sorted(holders, key=lambda h: h.get("last_round") or "", reverse=True)
    running = []
    for h in sorted_holders:
        running.append({
            "holder": h.get("holder"),
            "class": h.get("class"),
            "liquidation_pref": h.get("liquidation_pref") or 0,
            "fd_pct": h.get("fd_pct"),
        })
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": f"Liquidation waterfall — {row['name']}",
        "subtitle": "Priority by last_round (newest first)",
        "columns": ["holder", "class", "liquidation_pref", "fd_pct"],
        "rows": running,
    }, default=str)


waterfall = StructuredTool.from_function(
    func=_waterfall,
    name="waterfall",
    description="Liquidation waterfall (priority-ordered) for a company's cap table.",
    args_schema=CompanySlugArgs,
)


def _get_cap_table(slug_or_id: str) -> str:
    row = _load_cap_table(slug_or_id)
    if not row:
        return "No cap table for that company."
    return json.dumps({
        "company": row["name"],
        "as_of": str(row["as_of_date"]),
        "total_shares": row["total_shares"],
        "post_money": float(row["post_money"]) if row["post_money"] else None,
        "holders": row["holders"],
    }, default=str)


get_cap_table = StructuredTool.from_function(
    func=_get_cap_table,
    name="get_cap_table",
    description="Raw cap table dump for a company (JSON).",
    args_schema=CompanySlugArgs,
)


# Back-compat aliases
summarize_rent_roll = summarize_cap_table
lease_expiry_waterfall = waterfall
walt_years = waterfall  # repurposed — no rent-roll weighted term in PE; returns waterfall
