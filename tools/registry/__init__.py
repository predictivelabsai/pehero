"""Baltic business-registry + tax-authority integration.

Three country modules, one uniform surface:
    lookup_company(name_or_id, country) → {legal_name, reg_code, address, directors, …}
    fetch_filings(reg_code, country)    → [{year, report_type, url, highlights}]
    tax_status(reg_code, country)       → {debt_eur, vat_payer, …}

See docs/registry_integration.md for setup.
"""

from __future__ import annotations

from tools.registry.lt import lookup_lt, fetch_filings_lt, tax_status_lt
from tools.registry.lv import lookup_lv, fetch_filings_lv, tax_status_lv
from tools.registry.ee import lookup_ee, fetch_filings_ee, tax_status_ee

__all__ = [
    "lookup_lt", "fetch_filings_lt", "tax_status_lt",
    "lookup_lv", "fetch_filings_lv", "tax_status_lv",
    "lookup_ee", "fetch_filings_ee", "tax_status_ee",
]
