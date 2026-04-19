"""Company-lookup tools shared by many agents.

Historically named `properties` (from the CRE origins); now queries
pehero.companies (portfolio companies / deal targets).
"""

from __future__ import annotations

import json
from typing import Annotated, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db import fetch_all, fetch_one


class SearchCompaniesArgs(BaseModel):
    query: Optional[str] = Field(default=None, description="Free-text partial match on name or description.")
    hq_city: Optional[str] = Field(default=None)
    hq_state: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)
    sector: Optional[str] = Field(default=None, description="software | healthcare | industrials | consumer | business_services | financial_services")
    deal_stage: Optional[str] = Field(default=None)
    ownership: Optional[str] = Field(default=None)
    limit: int = Field(default=10, ge=1, le=50)


def _search_companies(**kw) -> str:
    args = SearchCompaniesArgs(**kw)
    sql = ["SELECT id, slug, name, hq_city, hq_state, country, sector, sub_sector, "
           "employees, revenue_ltm, ebitda_ltm, growth_rate, ownership, deal_stage, "
           "enterprise_value, ask_multiple, seller_intent "
           "FROM pehero.companies WHERE TRUE"]
    params: list = []
    if args.query:
        sql.append("AND (name ILIKE %s OR description ILIKE %s)")
        q = f"%{args.query}%"
        params.extend([q, q])
    if args.hq_city:
        sql.append("AND hq_city ILIKE %s"); params.append(args.hq_city)
    if args.hq_state:
        sql.append("AND hq_state = %s"); params.append(args.hq_state.upper())
    if args.country:
        sql.append("AND country ILIKE %s"); params.append(args.country)
    if args.sector:
        sql.append("AND sector = %s"); params.append(args.sector.lower())
    if args.deal_stage:
        sql.append("AND deal_stage = %s"); params.append(args.deal_stage.lower())
    if args.ownership:
        sql.append("AND ownership = %s"); params.append(args.ownership.lower())
    sql.append("ORDER BY id LIMIT %s"); params.append(args.limit)
    rows = fetch_all(" ".join(sql), tuple(params))

    if not rows:
        return "No matching companies."

    return json.dumps({
        "count": len(rows),
        "companies": [
            {
                "id": r["id"],
                "slug": r["slug"],
                "name": r["name"],
                "hq": f"{r['hq_city']}, {r['hq_state']}, {r['country']}",
                "sector": r["sector"],
                "sub_sector": r["sub_sector"],
                "employees": r["employees"],
                "revenue_ltm": float(r["revenue_ltm"]) if r["revenue_ltm"] is not None else None,
                "ebitda_ltm": float(r["ebitda_ltm"]) if r["ebitda_ltm"] is not None else None,
                "growth_rate": float(r["growth_rate"]) if r["growth_rate"] is not None else None,
                "ownership": r["ownership"],
                "deal_stage": r["deal_stage"],
                "enterprise_value": float(r["enterprise_value"]) if r["enterprise_value"] is not None else None,
                "ask_multiple": float(r["ask_multiple"]) if r["ask_multiple"] is not None else None,
                "seller_intent": r["seller_intent"],
            } for r in rows
        ],
    }, default=str)


search_companies = StructuredTool.from_function(
    func=_search_companies,
    name="search_companies",
    description="Search the PEHero company catalog (pipeline + portfolio). Filter by hq_city, hq_state, country, sector, deal_stage, ownership, or a free-text query.",
    args_schema=SearchCompaniesArgs,
)


class GetCompanyArgs(BaseModel):
    slug_or_id: str = Field(description="Company slug (preferred) or numeric id.")


def _get_company(slug_or_id: str) -> str:
    try:
        cid = int(slug_or_id)
        row = fetch_one("SELECT * FROM pehero.companies WHERE id = %s", (cid,))
    except (TypeError, ValueError):
        row = fetch_one("SELECT * FROM pehero.companies WHERE slug = %s", (slug_or_id,))
    if not row:
        return "Not found."
    return json.dumps(row, default=str)


get_company = StructuredTool.from_function(
    func=_get_company,
    name="get_company",
    description="Fetch full details for one company by slug or numeric id.",
    args_schema=GetCompanyArgs,
)


# Backward-compatible aliases used by agent modules / tests that haven't been
# renamed yet. Prefer the `_companies` forms in new code.
search_properties = search_companies
get_property = get_company
