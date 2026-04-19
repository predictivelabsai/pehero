"""Lithuania — Registrų centras (business registry) + VMI (tax authority).

API docs (subject to change — confirm current endpoints from RC self-service):
  - Registrų centras JAR / JADIS REST API: https://www.registrucentras.lt/atviri_duomenys
    Typical base: https://www.registrucentras.lt/jar/api
    Auth: API key (header `X-RC-API-KEY`), or OAuth2 for higher-volume plans.
  - VMI "i.MAS" tax portal open data + authenticated APIs for debt / VAT payer
    status. Typical base: https://www.vmi.lt/vmi/en/public-services
    Auth: certificate-based (eID via Gosignal / qualified e-signature).

This file is a stub — returns a clearly-marked `stub=True` dict unless
LT_CR_API_KEY / LT_VMI_API_KEY are set. Replace the bodies of `_rc_get` and
`_vmi_get` once credentials land.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from utils.config import settings

log = logging.getLogger(__name__)

RC_BASE = "https://www.registrucentras.lt/jar/api"
VMI_BASE = "https://www.vmi.lt/vmi/api"


def _rc_get(path: str, params: dict | None = None) -> dict | None:
    key = settings().lt_cr_api_key
    if not key:
        return None
    try:
        r = httpx.get(f"{RC_BASE}{path}", params=params or {},
                      headers={"X-RC-API-KEY": key}, timeout=20.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("LT RC call failed %s: %s", path, e)
        return None


def _vmi_get(path: str, params: dict | None = None) -> dict | None:
    key = settings().lt_vmi_api_key
    if not key:
        return None
    try:
        r = httpx.get(f"{VMI_BASE}{path}", params=params or {},
                      headers={"Authorization": f"Bearer {key}"}, timeout=20.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("LT VMI call failed %s: %s", path, e)
        return None


def lookup_lt(name_or_code: str) -> dict[str, Any]:
    data = _rc_get("/companies", params={"q": name_or_code})
    if data:
        return data
    return {
        "stub": True,
        "country": "LT",
        "query": name_or_code,
        "reason": "Set LT_CR_API_KEY and replace stub in tools/registry/lt.py.",
    }


def fetch_filings_lt(reg_code: str) -> list[dict]:
    data = _rc_get(f"/companies/{reg_code}/filings")
    if data is not None:
        return data.get("items") or data
    return [{"stub": True, "country": "LT", "reg_code": reg_code}]


def tax_status_lt(reg_code: str) -> dict[str, Any]:
    data = _vmi_get(f"/tax/{reg_code}")
    if data:
        return data
    return {
        "stub": True, "country": "LT", "reg_code": reg_code,
        "reason": "Set LT_VMI_API_KEY and replace stub in tools/registry/lt.py.",
    }
