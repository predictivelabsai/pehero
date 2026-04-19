"""Unified Baltic registry / tax-authority tools for agents.

Wraps the country modules in `tools.registry` behind a single StructuredTool
surface so any agent can call them uniformly.
"""

from __future__ import annotations

import json
from typing import Literal, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from tools.registry import (
    lookup_lt, fetch_filings_lt, tax_status_lt,
    lookup_lv, fetch_filings_lv, tax_status_lv,
    lookup_ee, fetch_filings_ee, tax_status_ee,
)

Country = Literal["LT", "LV", "EE"]


class BalticLookupArgs(BaseModel):
    country: Country = Field(description="LT | LV | EE")
    name_or_code: str = Field(description="Company legal name or registration code.")


def _baltic_lookup(**kw) -> str:
    args = BalticLookupArgs(**kw)
    fn = {"LT": lookup_lt, "LV": lookup_lv, "EE": lookup_ee}[args.country]
    return json.dumps(fn(args.name_or_code), default=str)


baltic_lookup = StructuredTool.from_function(
    func=_baltic_lookup,
    name="baltic_lookup",
    description=("Look up a company in a Baltic business registry (Lithuania "
                 "Registrų centras, Latvia Uzņēmumu reģistrs, or Estonia Äriregister)."),
    args_schema=BalticLookupArgs,
)


class BalticFilingsArgs(BaseModel):
    country: Country
    reg_code: str


def _baltic_filings(**kw) -> str:
    args = BalticFilingsArgs(**kw)
    fn = {"LT": fetch_filings_lt, "LV": fetch_filings_lv, "EE": fetch_filings_ee}[args.country]
    return json.dumps(fn(args.reg_code), default=str)


baltic_filings = StructuredTool.from_function(
    func=_baltic_filings,
    name="baltic_filings",
    description="Fetch annual reports / filings for a company registered in LT, LV, or EE.",
    args_schema=BalticFilingsArgs,
)


class BalticTaxArgs(BaseModel):
    country: Country
    reg_code: str


def _baltic_tax(**kw) -> str:
    args = BalticTaxArgs(**kw)
    fn = {"LT": tax_status_lt, "LV": tax_status_lv, "EE": tax_status_ee}[args.country]
    return json.dumps(fn(args.reg_code), default=str)


baltic_tax_status = StructuredTool.from_function(
    func=_baltic_tax,
    name="baltic_tax_status",
    description="Fetch current tax-debt / VAT-payer status for a company registered in LT, LV, or EE.",
    args_schema=BalticTaxArgs,
)
