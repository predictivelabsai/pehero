"""Estonia — Äriregister (Business Registry, RIK) + EMTA (Tax & Customs).

Two public-ish endpoints are wired here:

1. **Äriregister SOAP** at https://ariregxmlv6.rik.ee/
   Requires a RIK-issued username + password (`EE_ARI_USERNAME`,
   `EE_ARI_PASSWORD` in .env). Returns full company card with founders,
   directors, share capital.

2. **EMTA Maasikas public API** at https://maasikas.emta.ee/...
   Truly public — returns VAT, turnover, employee count by quarter. No
   credentials needed.

Full setup notes in docs/registry_integration.md.
"""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from utils.config import settings

log = logging.getLogger(__name__)

ARI_SOAP_URL = "https://ariregxmlv6.rik.ee/"
EMTA_COMPANIES = "https://maasikas.emta.ee/mirror-public-api/public/api/v1/companies"
EMTA_PERSONS = "https://maasikas.emta.ee/mirror-public-api/public/api/v1/persons"

SOAP_NS = {
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "prod": "http://arireg.x-road.eu/producer/",
}


def _detailandmed_body(reg_code: str, username: str, password: str, lang: str = "eng") -> str:
    return f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:prod="http://arireg.x-road.eu/producer/">
    <soapenv:Body>
    <prod:detailandmed_v2>
    <prod:keha>
    <prod:ariregister_kasutajanimi>{username}</prod:ariregister_kasutajanimi>
    <prod:ariregister_parool>{password}</prod:ariregister_parool>
    <prod:ariregistri_kood>{reg_code}</prod:ariregistri_kood>
    <prod:yandmed>1</prod:yandmed>
    <prod:iandmed>1</prod:iandmed>
    <prod:kandmed>0</prod:kandmed>
    <prod:dandmed>0</prod:dandmed>
    <prod:maarused>0</prod:maarused>
    <prod:keel>{lang}</prod:keel>
    <prod:ariregister_valjundi_formaat>json</prod:ariregister_valjundi_formaat>
    </prod:keha>
    </prod:detailandmed_v2>
    </soapenv:Body>
    </soapenv:Envelope>"""


def _financials_body(reg_code: str, year: int, report_type: str,
                     username: str, password: str) -> str:
    return f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:prod="http://arireg.x-road.eu/producer/">
    <soapenv:Body>
    <prod:majandusaastaAruanneteKirjed_v1>
    <prod:keha>
    <prod:ariregister_kasutajanimi>{username}</prod:ariregister_kasutajanimi>
    <prod:ariregister_parool>{password}</prod:ariregister_parool>
    <prod:ariregistri_kood>{reg_code}</prod:ariregistri_kood>
    <prod:aruande_liik>{report_type}</prod:aruande_liik>
    <prod:aruandeaasta>{year}</prod:aruandeaasta>
    </prod:keha>
    </prod:majandusaastaAruanneteKirjed_v1>
    </soapenv:Body>
    </soapenv:Envelope>"""


def _parse_soap_json(raw: bytes) -> dict | None:
    """Ariregister wraps a JSON blob inside its SOAP response body. Extract it."""
    try:
        # Response format embeds JSON as text inside <prod:keha>…</prod:keha>
        # If response is already JSON (some endpoints honor valjundi_formaat=json
        # at the HTTP level), try that first.
        txt = raw.decode("utf-8", errors="replace")
        if txt.lstrip().startswith("{"):
            return json.loads(txt)
        # Otherwise parse the SOAP envelope and pull the keha payload.
        root = ET.fromstring(raw)
        for keha in root.iter():
            tag = keha.tag.split("}")[-1]
            if tag == "keha" and keha.text and keha.text.strip().startswith("{"):
                return json.loads(keha.text)
        return None
    except Exception as e:  # noqa: BLE001
        log.warning("EE SOAP parse failed: %s", e)
        return None


def _ari_soap_detailandmed(reg_code: str) -> dict | None:
    cfg = settings()
    user, pwd = cfg.ee_ari_username, cfg.ee_ari_password
    if not user or not pwd:
        return None
    try:
        r = httpx.post(
            ARI_SOAP_URL,
            data=_detailandmed_body(reg_code, user, pwd).encode("utf-8"),
            headers={"content-type": "text/xml; charset=utf-8"},
            timeout=25.0,
        )
        r.raise_for_status()
        return _parse_soap_json(r.content)
    except Exception as e:  # noqa: BLE001
        log.warning("EE Äriregister SOAP call failed (code=%s): %s", reg_code, e)
        return None


def _ari_soap_financials(reg_code: str, year: int, report_type: str = "A1") -> dict | None:
    cfg = settings()
    user, pwd = cfg.ee_ari_username, cfg.ee_ari_password
    if not user or not pwd:
        return None
    try:
        r = httpx.post(
            ARI_SOAP_URL,
            data=_financials_body(reg_code, year, report_type, user, pwd).encode("utf-8"),
            headers={"content-type": "text/xml; charset=utf-8"},
            timeout=25.0,
        )
        r.raise_for_status()
        return _parse_soap_json(r.content)
    except Exception as e:  # noqa: BLE001
        log.warning("EE Äriregister financials call failed (code=%s year=%s): %s",
                    reg_code, year, e)
        return None


def _emta_company(query: str) -> dict | None:
    """Public EMTA lookup — no auth required. Returns the first hit."""
    payload = {
        "text": str(query),
        "limit": 10,
        "offset": 0,
        "language": "en",
    }
    try:
        r = httpx.post(EMTA_COMPANIES,
                       json=payload,
                       cookies={"language": "en"},
                       timeout=20.0)
        r.raise_for_status()
        data = r.json()
        return data
    except Exception as e:  # noqa: BLE001
        log.warning("EE EMTA call failed (%s): %s", query, e)
        return None


# ── Public API ──────────────────────────────────────────────────────

def lookup_ee(name_or_code: str) -> dict[str, Any]:
    """Look up an Estonian company by reg code or name.

    Merges Äriregister detail (if SOAP creds available) with public EMTA
    data (always available).
    """
    out: dict[str, Any] = {"country": "EE", "query": name_or_code}

    # EMTA works without credentials and handles both name + code search.
    emta = _emta_company(name_or_code)
    if emta and emta.get("companies"):
        first = emta["companies"][0]
        out["emta"] = {
            "name": first.get("companyName") or first.get("name"),
            "reg_code": (first.get("companyRegcode") or first.get("registrationNumber")
                         or first.get("regCode")),
            "turnover_ltm_eur": first.get("turnover4QuarterSum"),
            "labour_tax_4q_eur": first.get("labourTax4QuarterSum"),
            "employees_last_q": first.get("employeesCountLastQuarter"),
            "tax_debt_eur": first.get("taxDebtSum"),
            "tax_compliance_rating": first.get("taxComplianceLastRatingPeriod"),
            "prohibition_on_trade": first.get("isProhibitionOnTrade"),
            "representatives": first.get("representativesText"),
            "status": first.get("statusText"),
        }

    # If it looks like a reg code (all digits, 8 chars) and we have Ariregister creds, pull the card.
    reg_code = name_or_code
    if out.get("emta", {}).get("reg_code"):
        reg_code = str(out["emta"]["reg_code"])
    if reg_code.isdigit():
        ari = _ari_soap_detailandmed(reg_code)
        if ari:
            out["ariregister"] = ari

    if not out.get("emta") and not out.get("ariregister"):
        out["stub"] = True
        out["reason"] = ("Public EMTA returned no match; Äriregister SOAP needs "
                         "EE_ARI_USERNAME + EE_ARI_PASSWORD in .env.")
    return out


def fetch_filings_ee(reg_code: str) -> list[dict]:
    """Pull the most recent annual report A1 schedule from Äriregister.

    Requires SOAP credentials — returns a stub otherwise.
    """
    if not reg_code.isdigit():
        return [{"stub": True, "reason": "EE reg_code must be digits.",
                 "country": "EE", "reg_code": reg_code}]
    from datetime import datetime
    items: list[dict] = []
    for year in (datetime.utcnow().year - 1, datetime.utcnow().year - 2):
        data = _ari_soap_financials(reg_code, year, "A1")
        if data:
            items.append({"year": year, "report_type": "A1", "payload": data})
    if not items:
        return [{"stub": True, "country": "EE", "reg_code": reg_code,
                 "reason": "Set EE_ARI_USERNAME + EE_ARI_PASSWORD to pull annual reports."}]
    return items


def tax_status_ee(reg_code: str) -> dict[str, Any]:
    """Pull tax / VAT status via the public EMTA endpoint — no auth."""
    data = _emta_company(reg_code)
    if data and data.get("companies"):
        c = data["companies"][0]
        return {
            "country": "EE",
            "reg_code": c.get("companyRegcode") or reg_code,
            "name": c.get("companyName"),
            "turnover_ltm_eur": c.get("turnover4QuarterSum"),
            "labour_tax_4q_eur": c.get("labourTax4QuarterSum"),
            "employees_last_q": c.get("employeesCountLastQuarter"),
            "tax_debt_eur": c.get("taxDebtSum"),
            "tax_compliance_rating": c.get("taxComplianceLastRatingPeriod"),
            "prohibition_on_trade": c.get("isProhibitionOnTrade"),
            "source": "emta-maasikas",
        }
    return {
        "stub": True, "country": "EE", "reg_code": reg_code,
        "reason": "EMTA returned no match; verify the reg code.",
    }
