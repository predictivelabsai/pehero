"""Portfolio operations tools: pricing, EBITDA variance, value-creation ranking, customer churn."""

from __future__ import annotations

import json
from datetime import date
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db import fetch_all, fetch_one


def _resolve_cid(slug_or_id):
    try:
        return int(slug_or_id)
    except (TypeError, ValueError):
        row = fetch_one("SELECT id FROM pehero.companies WHERE slug = %s", (slug_or_id,))
        return row["id"] if row else None


class CompanyArgs(BaseModel):
    slug_or_id: str


def _pricing_opt(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    co = fetch_one("SELECT name, sector FROM pehero.companies WHERE id = %s", (cid,))
    contracts = fetch_all(
        "SELECT counterparty, contract_type, annual_value, start_date, end_date "
        "FROM pehero.contracts WHERE company_id = %s AND status = 'active' "
        "AND contract_type = 'customer_msa' ORDER BY annual_value DESC LIMIT 50",
        (cid,),
    )
    if not contracts:
        return "No customer contracts."

    # Pricing benchmark: assume market median is 8% above in-place for the demo
    avg_av = sum(float(c["annual_value"] or 0) for c in contracts) / max(1, len(contracts))
    recs = []
    for c in contracts:
        av = float(c["annual_value"] or 0)
        if av <= 0:
            continue
        segment = "enterprise" if av > avg_av * 2 else "mid_market" if av > avg_av * 0.5 else "smb"
        rec_pct = {"enterprise": 4.0, "mid_market": 8.0, "smb": 12.0}[segment]
        lift = av * rec_pct / 100
        recs.append({
            "counterparty": c["counterparty"],
            "segment": segment,
            "in_place_arr": round(av, 2),
            "rec_increase_pct": rec_pct,
            "rec_arr_lift": round(lift, 2),
            "renewal_date": str(c["end_date"]) if c["end_date"] else None,
        })
    recs.sort(key=lambda r: r["rec_arr_lift"], reverse=True)
    total_lift = sum(r["rec_arr_lift"] for r in recs)
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": f"Pricing optimization — {co['name']}",
        "subtitle": f"{len(recs)} customers · total estimated ARR lift ${total_lift:,.0f}",
        "columns": ["counterparty", "segment", "in_place_arr", "rec_increase_pct",
                    "rec_arr_lift", "renewal_date"],
        "rows": recs[:25],
    }, default=str)


pricing_opt_recs = StructuredTool.from_function(
    func=_pricing_opt,
    name="pricing_opt_recs",
    description="Rank customer contracts by pricing opportunity using segment benchmarks; estimate ARR lift at renewal.",
    args_schema=CompanyArgs,
)
# Back-compat alias
rent_optimization_recs = pricing_opt_recs


def _ebitda_variance(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    rows = fetch_all(
        "SELECT month, ebitda, adj_ebitda, opex FROM pehero.financials "
        "WHERE company_id = %s ORDER BY month ASC",
        (cid,),
    )
    if len(rows) < 2:
        return "Not enough financial history."
    total = len(rows)
    split = max(1, total - 3)  # baseline = first n-3, recent = last 3
    cats = set().union(*[set((r["opex"] or {}).keys()) for r in rows])
    variance = []
    for c in cats:
        base = sum(float((r["opex"] or {}).get(c, 0)) for r in rows[:split]) / split
        recent = sum(float((r["opex"] or {}).get(c, 0)) for r in rows[split:]) / max(1, total - split)
        delta = recent - base
        pct = 100 * delta / base if base else 0
        variance.append({
            "category": c,
            "baseline_avg": round(base, 2),
            "recent_avg": round(recent, 2),
            "abs_delta": round(delta, 2),
            "pct_delta": round(pct, 1),
        })
    # Add EBITDA line
    base_eb = sum(float(r["ebitda"] or 0) for r in rows[:split]) / split
    recent_eb = sum(float(r["ebitda"] or 0) for r in rows[split:]) / max(1, total - split)
    variance.insert(0, {
        "category": "EBITDA (reported)",
        "baseline_avg": round(base_eb, 2),
        "recent_avg": round(recent_eb, 2),
        "abs_delta": round(recent_eb - base_eb, 2),
        "pct_delta": round(100 * (recent_eb - base_eb) / base_eb, 1) if base_eb else 0,
    })
    variance.sort(key=lambda v: abs(v["pct_delta"]), reverse=True)
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": "EBITDA + opex variance (last 3 mo vs. prior)",
        "columns": ["category", "baseline_avg", "recent_avg", "abs_delta", "pct_delta"],
        "rows": variance,
    })


fetch_ebitda_variance = StructuredTool.from_function(
    func=_ebitda_variance,
    name="fetch_ebitda_variance",
    description="Compute recent vs baseline EBITDA + opex variance from a company's monthly financials; ranks categories by variance magnitude.",
    args_schema=CompanyArgs,
)
# Back-compat alias
opex_variance = fetch_ebitda_variance


def _value_creation_ranking(slug_or_id: str) -> str:
    """Rank synthetic value-creation initiatives by expected EBITDA impact."""
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    co = fetch_one(
        "SELECT name, sector, revenue_ltm, ebitda_ltm FROM pehero.companies WHERE id = %s",
        (cid,),
    )
    rev = float(co["revenue_ltm"] or 0)
    ebitda = float(co["ebitda_ltm"] or 0)

    catalog = [
        {"initiative": "Pricing — segmented price increases at renewal",
         "capital_usd": round(0.005 * rev, 0),
         "ebitda_lift_usd": round(0.04 * rev, 0),
         "timing_months": 6, "urgency": "high",
         "risk": "Customer pushback at top enterprise accounts."},
        {"initiative": "Sales productivity — CRM rollout + rep benchmarks",
         "capital_usd": 650_000,
         "ebitda_lift_usd": round(0.02 * rev, 0),
         "timing_months": 9, "urgency": "medium",
         "risk": "Execution risk; 12-month ramp to full impact."},
        {"initiative": "Procurement — top-20 supplier renegotiation",
         "capital_usd": 180_000,
         "ebitda_lift_usd": round(0.015 * rev, 0),
         "timing_months": 4, "urgency": "medium",
         "risk": "Supplier relationships; single-source exposure."},
        {"initiative": "Tuck-in M&A — one programmatic add-on per year",
         "capital_usd": round(2.5 * ebitda, 0),
         "ebitda_lift_usd": round(0.3 * ebitda, 0),
         "timing_months": 12, "urgency": "low",
         "risk": "Integration risk; cultural fit; multiple paid."},
        {"initiative": "Digital / ERP upgrade — margin recapture",
         "capital_usd": 1_800_000,
         "ebitda_lift_usd": round(0.02 * rev, 0),
         "timing_months": 18, "urgency": "low",
         "risk": "Large implementation; delayed payback."},
    ]
    for c in catalog:
        cap = c["capital_usd"] or 1
        c["roi_pct"] = round(100 * c["ebitda_lift_usd"] / cap, 1)
    catalog.sort(key=lambda c: c["roi_pct"], reverse=True)
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": f"Value-creation ranking — {co['name']}",
        "columns": ["initiative", "capital_usd", "ebitda_lift_usd", "roi_pct",
                    "timing_months", "urgency"],
        "rows": catalog,
    })


value_creation_ranking = StructuredTool.from_function(
    func=_value_creation_ranking,
    name="value_creation_ranking",
    description="Rank pending value-creation initiatives for a portfolio company by expected ROI (EBITDA lift / capital).",
    args_schema=CompanyArgs,
)
# Back-compat alias
capex_ranking = value_creation_ranking
list_initiatives = value_creation_ranking


def _customer_churn(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    co = fetch_one("SELECT name FROM pehero.companies WHERE id = %s", (cid,))
    contracts = fetch_all(
        "SELECT counterparty, contract_type, annual_value, start_date, end_date, "
        "auto_renew, exclusivity "
        "FROM pehero.contracts WHERE company_id = %s AND status='active' "
        "AND contract_type = 'customer_msa' "
        "ORDER BY end_date ASC NULLS LAST LIMIT 60",
        (cid,),
    )
    today = date.today()
    rows = []
    for c in contracts:
        if not c["end_date"]:
            continue
        end_d = c["end_date"]
        days_to = (end_d - today).days
        tenure_days = (today - (c["start_date"] or end_d)).days
        score = 0.0
        if days_to < 90: score += 0.5
        elif days_to < 270: score += 0.3
        if tenure_days < 365: score += 0.2
        if not c["auto_renew"]: score += 0.15
        if not c["exclusivity"]: score += 0.1
        av = float(c["annual_value"] or 0)
        if av < 50_000: score += 0.1
        score = min(0.95, round(score, 2))
        rows.append({
            "counterparty": c["counterparty"],
            "annual_value": av,
            "end_date": str(end_d),
            "days_to_expiry": days_to,
            "auto_renew": c["auto_renew"],
            "exclusivity": c["exclusivity"],
            "churn_score": score,
        })
    rows.sort(key=lambda r: -r["churn_score"])
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": f"Customer churn risk — {co['name']}",
        "subtitle": f"{len(rows)} active customers ranked by churn score",
        "columns": ["counterparty", "annual_value", "end_date", "days_to_expiry",
                    "auto_renew", "exclusivity", "churn_score"],
        "rows": rows[:25],
    }, default=str)


customer_churn_scores = StructuredTool.from_function(
    func=_customer_churn,
    name="customer_churn_scores",
    description="Score each active customer contract for churn / renewal risk based on time-to-expiry, tenure, auto-renew, exclusivity, and value tier.",
    args_schema=CompanyArgs,
)
# Back-compat alias
tenant_churn = customer_churn_scores
