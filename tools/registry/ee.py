"""Estonia — Äriregister (business registry, via RIK) + EMTA (Tax & Customs).

Estonia has the most mature open-data / API story of the three:

  - Äriregister / e-Business Register: https://ariregister.rik.ee/
    X-Road-based API (xtee) — the easiest path is via `https://ariregister.rik.ee/eng/api`.
    Auth: username + password for the "Teabesüsteem" (info-system) service,
    typically provisioned via RIK contract (paid, per-query or subscription).
    Some company-card endpoints are freely available without auth.

  - EMTA (Maksu- ja Tolliamet) — tax debt, VAT-payer, employment registry:
    https://emta.ee/en/business-client/registers-and-inquiries
    Auth: eID / Mobile-ID for authenticated lookups; some aggregate lookups
    (e.g. tax-debt by reg code) are available via the `maksuvelg` open service.

The user will be providing EE keys / credentials — plug them into
EE_ARI_API_KEY (Äriregister) and EE_EMTA_API_KEY (EMTA) in .env.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from utils.config import settings

log = logging.getLogger(__name__)

ARI_BASE = "https://ariregister.rik.ee/api"
EMTA_BASE = "https://emta.ee/api"


def _ari_get(path: str, params: dict | None = None) -> dict | None:
    key = settings().ee_ari_api_key
    if not key:
        return None
    try:
        r = httpx.get(f"{ARI_BASE}{path}", params=params or {},
                      headers={"Authorization": f"Bearer {key}"}, timeout=20.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("EE ARI call failed %s: %s", path, e)
        return None


def _emta_get(path: str, params: dict | None = None) -> dict | None:
    key = settings().ee_emta_api_key
    if not key:
        return None
    try:
        r = httpx.get(f"{EMTA_BASE}{path}", params=params or {},
                      headers={"Authorization": f"Bearer {key}"}, timeout=20.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("EE EMTA call failed %s: %s", path, e)
        return None


def lookup_ee(name_or_code: str) -> dict[str, Any]:
    data = _ari_get("/companies", params={"q": name_or_code})
    if data:
        return data
    return {
        "stub": True, "country": "EE", "query": name_or_code,
        "reason": "Set EE_ARI_API_KEY and replace stub in tools/registry/ee.py.",
    }


def fetch_filings_ee(reg_code: str) -> list[dict]:
    data = _ari_get(f"/companies/{reg_code}/annual-reports")
    if data is not None:
        return data.get("items") or data
    return [{"stub": True, "country": "EE", "reg_code": reg_code}]


def tax_status_ee(reg_code: str) -> dict[str, Any]:
    data = _emta_get(f"/maksuvelg/{reg_code}")
    if data:
        return data
    return {
        "stub": True, "country": "EE", "reg_code": reg_code,
        "reason": "Set EE_EMTA_API_KEY and replace stub in tools/registry/ee.py.",
    }
