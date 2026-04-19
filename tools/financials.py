"""Financial modeling tools: LTM normalize, LBO model, debt sizing, returns."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db import connect, fetch_all, fetch_one


class CompanyArgs(BaseModel):
    slug_or_id: str = Field(description="Company slug or numeric id.")


def _resolve_cid(slug_or_id: str) -> Optional[int]:
    try:
        return int(slug_or_id)
    except (TypeError, ValueError):
        row = fetch_one("SELECT id FROM pehero.companies WHERE slug = %s", (slug_or_id,))
        return row["id"] if row else None


def _normalize_ltm(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    co = fetch_one("SELECT name, sector, sub_sector FROM pehero.companies WHERE id = %s", (cid,))
    rows = fetch_all(
        "SELECT month, revenue, cogs, gross_profit, opex, ebitda, adjustments, adj_ebitda, "
        "arr, gross_retention, net_retention "
        "FROM pehero.financials WHERE company_id = %s ORDER BY month ASC",
        (cid,),
    )
    if not rows:
        return "No financial rows."

    rev = sum(float(r["revenue"] or 0) for r in rows)
    cogs = sum(float(r["cogs"] or 0) for r in rows)
    gp = sum(float(r["gross_profit"] or 0) for r in rows)
    ebitda = sum(float(r["ebitda"] or 0) for r in rows)
    adj_ebitda = sum(float(r["adj_ebitda"] or 0) for r in rows)

    opex_total: dict[str, float] = {}
    for r in rows:
        for k, v in (r["opex"] or {}).items():
            opex_total[k] = opex_total.get(k, 0) + float(v or 0)

    # add-back detail (sum of adjustments by type, in the last 12 months)
    adj_total: dict[str, float] = {}
    for r in rows[-12:]:
        for k, v in (r["adjustments"] or {}).items():
            adj_total[k] = adj_total.get(k, 0) + float(v or 0)

    # LTM = last 12 rows
    ltm = rows[-12:] if len(rows) >= 12 else rows
    ltm_rev = sum(float(r["revenue"] or 0) for r in ltm)
    ltm_ebitda = sum(float(r["ebitda"] or 0) for r in ltm)
    ltm_adj_ebitda = sum(float(r["adj_ebitda"] or 0) for r in ltm)

    # prior 12 for growth
    prior12 = rows[-24:-12] if len(rows) >= 24 else []
    prior_rev = sum(float(r["revenue"] or 0) for r in prior12)
    rev_growth = ((ltm_rev / prior_rev) - 1.0) * 100 if prior_rev else None

    summary = {
        "company": co["name"],
        "sector": co["sector"],
        "period": f"{rows[0]['month']} to {rows[-1]['month']}",
        "months": len(rows),
        "ltm_revenue": round(ltm_rev, 2),
        "ltm_growth_pct": round(rev_growth, 2) if rev_growth is not None else None,
        "ltm_gross_margin_pct": round(100 * (ltm_rev - (sum(float(r['cogs'] or 0) for r in ltm))) / max(1, ltm_rev), 2),
        "ltm_ebitda": round(ltm_ebitda, 2),
        "ltm_adj_ebitda": round(ltm_adj_ebitda, 2),
        "ltm_ebitda_margin_pct": round(100 * ltm_ebitda / max(1, ltm_rev), 2),
        "ltm_adj_ebitda_margin_pct": round(100 * ltm_adj_ebitda / max(1, ltm_rev), 2),
        "opex_by_category": {k: round(v, 2) for k, v in opex_total.items()},
        "adjustments_ltm": {k: round(v, 2) for k, v in adj_total.items()},
        "add_back_total_ltm": round(ltm_adj_ebitda - ltm_ebitda, 2),
    }

    chart_rows = [
        {
            "month": str(r["month"])[:7],
            "revenue": float(r["revenue"] or 0),
            "ebitda": float(r["ebitda"] or 0),
            "adj_ebitda": float(r["adj_ebitda"] or 0),
        }
        for r in rows
    ]
    artifact = {
        "kind": "table",
        "title": f"LTM financials — {co['name']}",
        "subtitle": f"{summary['period']} · {summary['ltm_adj_ebitda_margin_pct']}% adj. EBITDA margin",
        "columns": ["month", "revenue", "ebitda", "adj_ebitda"],
        "rows": chart_rows,
        "summary": summary,
    }
    return "__ARTIFACT__" + json.dumps(artifact)


normalize_ltm = StructuredTool.from_function(
    func=_normalize_ltm,
    name="normalize_ltm",
    description="Normalize a company's historical financials into LTM (trailing twelve months) adj. EBITDA with add-back detail and growth stats. Emits a monthly artifact.",
    args_schema=CompanyArgs,
)

# Back-compat alias so agents still using `normalize_t12` continue to work.
normalize_t12 = normalize_ltm


class LBOArgs(BaseModel):
    slug_or_id: str = Field(description="Company slug or id.")
    hold_years: int = Field(default=5, ge=1, le=10)
    entry_multiple: float = Field(default=10.0, description="EV / LTM adj EBITDA at entry")
    revenue_growth_pct: float = Field(default=8.0, description="Annual revenue growth %")
    margin_expansion_bps: float = Field(default=200.0, description="Cumulative bps of EBITDA margin expansion over hold")
    capex_pct_revenue: float = Field(default=3.0)
    wc_days: float = Field(default=0.0, description="Incremental working capital days invested per revenue $")
    exit_multiple: float = Field(default=10.0)
    tax_rate_pct: float = Field(default=25.0)
    sponsor_equity_pct: float = Field(default=45.0, description="Sponsor equity % of EV (rest is debt + seller notes)")
    interest_rate_pct: float = Field(default=9.0)


def _build_lbo_model(**kw) -> str:
    args = LBOArgs(**kw)
    cid = _resolve_cid(args.slug_or_id)
    if not cid:
        return "Company not found."
    co = fetch_one("SELECT * FROM pehero.companies WHERE id = %s", (cid,))

    ltm_rows = fetch_all(
        "SELECT revenue, adj_ebitda FROM pehero.financials "
        "WHERE company_id = %s ORDER BY month DESC LIMIT 12",
        (cid,),
    )
    ltm_rev = sum(float(r["revenue"] or 0) for r in ltm_rows)
    ltm_adj_ebitda = sum(float(r["adj_ebitda"] or 0) for r in ltm_rows)
    if ltm_adj_ebitda <= 0:
        ltm_adj_ebitda = float(co["ebitda_ltm"] or 0)
        ltm_rev = float(co["revenue_ltm"] or 0)
    if ltm_adj_ebitda <= 0 or ltm_rev <= 0:
        return "Insufficient financial data to build LBO."

    entry_ev = ltm_adj_ebitda * args.entry_multiple
    entry_equity = entry_ev * args.sponsor_equity_pct / 100
    entry_debt = entry_ev - entry_equity

    projections = []
    rev = ltm_rev
    starting_margin = ltm_adj_ebitda / ltm_rev
    debt = entry_debt
    for y in range(1, args.hold_years + 1):
        rev = rev * (1 + args.revenue_growth_pct / 100)
        margin = starting_margin + (args.margin_expansion_bps / 10000) * (y / args.hold_years)
        ebitda = rev * margin
        capex = rev * args.capex_pct_revenue / 100
        interest = debt * args.interest_rate_pct / 100
        taxes = max(0.0, (ebitda - interest) * args.tax_rate_pct / 100)
        fcf = ebitda - capex - interest - taxes
        debt_paydown = max(0.0, fcf * 0.90)   # 90% sweep
        debt = max(0.0, debt - debt_paydown)
        projections.append({
            "year": y,
            "revenue": round(rev, 2),
            "ebitda": round(ebitda, 2),
            "ebitda_margin_pct": round(margin * 100, 2),
            "capex": round(capex, 2),
            "interest": round(interest, 2),
            "taxes": round(taxes, 2),
            "fcf": round(fcf, 2),
            "debt_paydown": round(debt_paydown, 2),
            "net_debt_end": round(debt, 2),
        })

    exit_ebitda = projections[-1]["ebitda"]
    exit_ev = exit_ebitda * args.exit_multiple
    exit_debt = projections[-1]["net_debt_end"]
    exit_equity = exit_ev - exit_debt
    moic = exit_equity / entry_equity if entry_equity else 0
    # equity cashflows: -entry at t0, exit at year N, no interim dividends
    irr = _irr([-entry_equity] + [0] * (args.hold_years - 1) + [exit_equity])

    assumptions = args.model_dump()
    returns = {
        "entry_ev": round(entry_ev, 2),
        "entry_debt": round(entry_debt, 2),
        "entry_equity": round(entry_equity, 2),
        "exit_ev": round(exit_ev, 2),
        "exit_debt": round(exit_debt, 2),
        "exit_equity": round(exit_equity, 2),
        "moic": round(moic, 2),
        "levered_irr_pct": round(irr * 100, 2) if irr is not None else None,
    }

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pehero.lbo_models (company_id, name, assumptions, projections, returns) "
            "VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb) RETURNING id",
            (cid, f"{co['name']} — base case", json.dumps(assumptions),
             json.dumps(projections), json.dumps(returns)),
        )
        conn.commit()

    artifact = {
        "kind": "table",
        "title": f"LBO model — {co['name']}",
        "subtitle": f"{args.hold_years}yr · entry {args.entry_multiple}x → exit {args.exit_multiple}x · MOIC {returns['moic']}x, IRR {returns['levered_irr_pct']}%",
        "columns": ["year", "revenue", "ebitda", "ebitda_margin_pct", "capex", "interest", "fcf", "debt_paydown", "net_debt_end"],
        "rows": projections,
        "summary": {"assumptions": assumptions, "returns": returns},
    }
    return "__ARTIFACT__" + json.dumps(artifact)


def _irr(cash_flows: list[float]) -> Optional[float]:
    def npv(r):
        return sum(cf / ((1 + r) ** i) for i, cf in enumerate(cash_flows))
    low, high = -0.95, 10.0
    if npv(low) * npv(high) > 0:
        return None
    for _ in range(80):
        mid = (low + high) / 2
        v = npv(mid)
        if abs(v) < 1:
            return mid
        if npv(low) * v < 0:
            high = mid
        else:
            low = mid
    return mid


build_lbo_model = StructuredTool.from_function(
    func=_build_lbo_model,
    name="build_lbo_model",
    description="Build a 5-year LBO model for a company — entry / exit multiple, revenue growth, margin expansion, capex, interest, debt paydown. Persists to pehero.lbo_models and returns the schedule + returns.",
    args_schema=LBOArgs,
)
# Back-compat alias
build_pro_forma = build_lbo_model


class DebtArgs(BaseModel):
    slug_or_id: str
    entry_ev: Optional[float] = Field(default=None, description="Enterprise value; if None, priced off current LTM and ask_multiple")
    total_leverage: float = Field(default=5.5, description="Target total debt / EBITDA turns")
    revolver_size: float = Field(default=15_000_000.0, description="Revolver commitment in USD")
    mezz_turns: float = Field(default=0.0, description="Turns of mezzanine / second-lien to add above senior")
    senior_rate_pct: float = Field(default=8.5)
    mezz_rate_pct: float = Field(default=12.0)
    target_fccr: float = Field(default=1.35)


def _size_debt_stack(**kw) -> str:
    args = DebtArgs(**kw)
    cid = _resolve_cid(args.slug_or_id)
    if not cid:
        return "Company not found."
    co = fetch_one("SELECT name, ebitda_ltm, ask_multiple FROM pehero.companies WHERE id = %s", (cid,))
    ebitda = float(co["ebitda_ltm"] or 0)
    if ebitda <= 0:
        return "No EBITDA available."
    entry_ev = args.entry_ev or (ebitda * float(co["ask_multiple"] or 10))

    senior_turns = max(0.0, args.total_leverage - args.mezz_turns)
    senior_amt = ebitda * senior_turns
    mezz_amt = ebitda * args.mezz_turns
    total_debt = senior_amt + mezz_amt

    senior_interest = senior_amt * args.senior_rate_pct / 100
    mezz_interest = mezz_amt * args.mezz_rate_pct / 100
    total_interest = senior_interest + mezz_interest
    dscr = ebitda / total_interest if total_interest else None
    fccr = ebitda / total_interest if total_interest else None

    tranches = [
        {"name": "Senior / Unitranche", "lender": "Direct lender", "type": "unitranche",
         "amount": round(senior_amt, 2), "rate_pct": args.senior_rate_pct,
         "amort_years": 7, "term_years": 7, "io_years": 1,
         "covenants": "springing leverage"},
    ]
    if mezz_amt > 0:
        tranches.append({
            "name": "Mezzanine", "lender": "Mezz fund", "type": "mezz",
            "amount": round(mezz_amt, 2), "rate_pct": args.mezz_rate_pct,
            "amort_years": 0, "term_years": 8, "io_years": 8,
            "covenants": "incurrence",
        })
    tranches.append({
        "name": "Revolver", "lender": "Bank", "type": "revolver",
        "amount": round(args.revolver_size, 2), "rate_pct": 7.5,
        "amort_years": 0, "term_years": 5, "io_years": 5,
        "covenants": "springing leverage",
    })

    result = {
        "company": co["name"],
        "entry_ev": round(entry_ev, 2),
        "ltm_ebitda": round(ebitda, 2),
        "total_debt": round(total_debt, 2),
        "total_leverage_x": round(total_debt / ebitda, 2),
        "senior_turns_x": round(senior_turns, 2),
        "mezz_turns_x": round(args.mezz_turns, 2),
        "interest_total": round(total_interest, 2),
        "dscr": round(dscr, 2) if dscr else None,
        "fccr": round(fccr, 2) if fccr else None,
        "tranches": tranches,
    }

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pehero.debt_stacks (company_id, name, tranches, total_debt, total_leverage, dscr) "
            "VALUES (%s, %s, %s::jsonb, %s, %s, %s)",
            (cid, f"{co['name']} — base debt stack", json.dumps(tranches),
             total_debt, total_debt / ebitda if ebitda else 0, dscr),
        )
        conn.commit()

    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": f"Debt stack — {co['name']}",
        "subtitle": f"{result['total_leverage_x']}x total · DSCR {result['dscr']}x",
        "columns": ["name", "lender", "amount", "rate_pct", "amort_years", "term_years", "io_years", "covenants"],
        "rows": tranches,
        "summary": result,
    })


size_debt_stack = StructuredTool.from_function(
    func=_size_debt_stack,
    name="size_debt_stack",
    description="Size an LBO capital structure (senior / unitranche + mezz + revolver) given target leverage turns and coverage ratios. Persists to pehero.debt_stacks.",
    args_schema=DebtArgs,
)
# Back-compat alias
size_debt = size_debt_stack


class ReturnsArgs(BaseModel):
    slug_or_id: str
    lbo_model_id: Optional[int] = Field(default=None, description="Specific LBO model id; if None uses most recent.")


def _compute_returns(**kw) -> str:
    args = ReturnsArgs(**kw)
    cid = _resolve_cid(args.slug_or_id)
    if not cid:
        return "Company not found."
    if args.lbo_model_id:
        pf = fetch_one("SELECT * FROM pehero.lbo_models WHERE id = %s AND company_id = %s",
                       (args.lbo_model_id, cid))
    else:
        pf = fetch_one(
            "SELECT * FROM pehero.lbo_models WHERE company_id = %s ORDER BY id DESC LIMIT 1",
            (cid,),
        )
    if not pf:
        return "No LBO model for this company — call build_lbo_model first."

    returns = pf["returns"] or {}
    projections = pf["projections"] or []
    entry_equity = returns.get("entry_equity") or 0
    exit_equity = returns.get("exit_equity") or 0

    # MOIC bridge
    ltm_rows = fetch_all(
        "SELECT adj_ebitda FROM pehero.financials WHERE company_id = %s "
        "ORDER BY month DESC LIMIT 12",
        (cid,),
    )
    ltm_ebitda = sum(float(r["adj_ebitda"] or 0) for r in ltm_rows)
    assumptions = pf["assumptions"] or {}
    entry_mult = float(assumptions.get("entry_multiple") or 10)
    exit_mult = float(assumptions.get("exit_multiple") or entry_mult)
    exit_ebitda = float(projections[-1]["ebitda"]) if projections else 0

    multiple_arb = exit_ebitda * (exit_mult - entry_mult)
    ebitda_growth = (exit_ebitda - ltm_ebitda) * entry_mult
    debt_paydown = sum(p.get("debt_paydown", 0) for p in projections)

    bridge = {
        "ebitda_growth_contribution": round(ebitda_growth, 2),
        "multiple_arbitrage_contribution": round(multiple_arb, 2),
        "debt_paydown_contribution": round(debt_paydown, 2),
    }

    return json.dumps({"returns": returns, "value_creation_bridge": bridge,
                       "entry_equity": entry_equity, "exit_equity": exit_equity}, default=str)


compute_returns = StructuredTool.from_function(
    func=_compute_returns,
    name="compute_returns",
    description="Return IRR/MOIC + value-creation bridge (EBITDA growth vs. multiple arb vs. debt paydown) for the most recent LBO model of a company.",
    args_schema=ReturnsArgs,
)


def _get_lbo_model(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    pf = fetch_one(
        "SELECT * FROM pehero.lbo_models WHERE company_id = %s ORDER BY id DESC LIMIT 1",
        (cid,),
    )
    if not pf:
        return "No LBO model."
    return json.dumps(pf, default=str)


get_lbo_model = StructuredTool.from_function(
    func=_get_lbo_model,
    name="get_lbo_model",
    description="Return the most recent LBO model for a company (assumptions + projections + returns).",
    args_schema=CompanyArgs,
)
