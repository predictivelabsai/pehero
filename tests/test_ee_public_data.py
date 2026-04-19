"""Sample tests against Estonia's public company-data endpoints.

Originally adapted from a Colab notebook — kept here as a smoke test that
we can actually reach the public surfaces.

Two groups:

* **Public (always run):** EMTA Maasikas REST endpoint at
  maasikas.emta.ee — no auth needed. Returns VAT, turnover, employees.

* **Authenticated (skipped unless creds set):** Äriregister SOAP at
  ariregxmlv6.rik.ee — requires `EE_ARI_USERNAME` + `EE_ARI_PASSWORD` in
  .env. Returns the full company card + annual reports.

Run with:
    pytest -q tests/test_ee_public_data.py

The network tests are short (one call each) and skip themselves cleanly
when offline or when creds are missing, so they're safe in CI.
"""

from __future__ import annotations

import os
import socket

import httpx
import pytest

from tools.registry.ee import (
    EMTA_COMPANIES,
    lookup_ee,
    tax_status_ee,
    fetch_filings_ee,
    _ari_soap_detailandmed,
)

# A stable, well-known Estonian company for demo lookups (Bolt Technology OÜ)
BOLT_REG_CODE = "12417834"


def _online(host: str = "maasikas.emta.ee") -> bool:
    try:
        socket.gethostbyname(host)
        return True
    except Exception:
        return False


needs_online = pytest.mark.skipif(not _online(), reason="offline")
needs_ari_creds = pytest.mark.skipif(
    not (os.getenv("EE_ARI_USERNAME") and os.getenv("EE_ARI_PASSWORD")),
    reason="EE_ARI_USERNAME / EE_ARI_PASSWORD not set",
)


# ── Public EMTA ──────────────────────────────────────────────────────

@needs_online
def test_emta_companies_endpoint_reachable():
    """Bare-HTTP sanity check — the public endpoint responds with JSON."""
    r = httpx.post(
        EMTA_COMPANIES,
        json={"text": BOLT_REG_CODE, "limit": 1, "offset": 0, "language": "en"},
        cookies={"language": "en"},
        timeout=20.0,
    )
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "companies" in data, data


@needs_online
def test_lookup_ee_returns_emta_block():
    """lookup_ee() merges EMTA data into the response."""
    out = lookup_ee(BOLT_REG_CODE)
    assert out["country"] == "EE"
    if out.get("emta"):
        emta = out["emta"]
        assert str(emta["reg_code"]) == BOLT_REG_CODE
        assert emta.get("name") and "Bolt" in emta["name"]
        if emta.get("employees_last_q") is not None:
            assert emta["employees_last_q"] > 0


@needs_online
def test_tax_status_ee_shape():
    out = tax_status_ee(BOLT_REG_CODE)
    assert out["country"] == "EE"
    if not out.get("stub"):
        assert "turnover_ltm_eur" in out
        assert "tax_debt_eur" in out
        assert "employees_last_q" in out


# ── Äriregister SOAP (auth) ──────────────────────────────────────────

@needs_online
@needs_ari_creds
def test_ariregister_soap_company_card():
    """Full company card from Äriregister SOAP — requires RIK credentials."""
    data = _ari_soap_detailandmed(BOLT_REG_CODE)
    assert data is not None, "SOAP parse returned None"
    # Accept either the ettevotjad list or a keha wrapper
    blob = data.get("keha") if isinstance(data, dict) and "keha" in data else data
    companies = (blob.get("ettevotjad") or {}).get("item") if isinstance(blob, dict) else None
    assert companies, f"Unexpected shape: {list(blob.keys()) if isinstance(blob, dict) else type(blob)}"
    first = companies[0] if isinstance(companies, list) else companies
    assert first.get("nimi"), first


@needs_online
@needs_ari_creds
def test_fetch_filings_ee_returns_annual_reports():
    items = fetch_filings_ee(BOLT_REG_CODE)
    assert items, "no filings returned"
    # Either real payload rows or a single stub — guard both
    if not items[0].get("stub"):
        assert items[0].get("year")
        assert items[0].get("report_type") == "A1"


# ── Non-network unit-level checks ────────────────────────────────────

def test_fetch_filings_ee_rejects_non_numeric_reg_code():
    out = fetch_filings_ee("not-a-code")
    assert out[0]["stub"] is True
    assert "digits" in (out[0].get("reason") or "").lower()
