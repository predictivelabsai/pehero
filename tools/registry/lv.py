"""Latvia — Uzņēmumu reģistrs (business registry) + VID (State Revenue Service).

API notes (confirm current endpoints from UR / VID portals):
  - Uzņēmumu reģistrs open data: https://www.ur.gov.lv/lv/atverti-dati/
    Partial data is free + REST. Full filings / changes feed require a
    signed agreement with UR; API key is delivered on approval.
  - VID EDS API (Elektroniskā deklarēšanas sistēma): https://eds.vid.gov.lv
    Auth: certificate-based (eID) or API key for authorized operators.
    Typical use: tax-debt lookup, VAT-payer status.

Stub follows the same pattern as lt.py.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from utils.config import settings

log = logging.getLogger(__name__)

UR_BASE = "https://www.ur.gov.lv/api/v1"
VID_BASE = "https://eds.vid.gov.lv/api"


def _ur_get(path: str, params: dict | None = None) -> dict | None:
    key = settings().lv_ur_api_key
    if not key:
        return None
    try:
        r = httpx.get(f"{UR_BASE}{path}", params=params or {},
                      headers={"X-UR-API-KEY": key}, timeout=20.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("LV UR call failed %s: %s", path, e)
        return None


def _vid_get(path: str, params: dict | None = None) -> dict | None:
    key = settings().lv_vid_api_key
    if not key:
        return None
    try:
        r = httpx.get(f"{VID_BASE}{path}", params=params or {},
                      headers={"Authorization": f"Bearer {key}"}, timeout=20.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("LV VID call failed %s: %s", path, e)
        return None


def lookup_lv(name_or_code: str) -> dict[str, Any]:
    data = _ur_get("/companies", params={"q": name_or_code})
    if data:
        return data
    return {
        "stub": True, "country": "LV", "query": name_or_code,
        "reason": "Set LV_UR_API_KEY and replace stub in tools/registry/lv.py.",
    }


def fetch_filings_lv(reg_code: str) -> list[dict]:
    data = _ur_get(f"/companies/{reg_code}/filings")
    if data is not None:
        return data.get("items") or data
    return [{"stub": True, "country": "LV", "reg_code": reg_code}]


def tax_status_lv(reg_code: str) -> dict[str, Any]:
    data = _vid_get(f"/tax/{reg_code}")
    if data:
        return data
    return {
        "stub": True, "country": "LV", "reg_code": reg_code,
        "reason": "Set LV_VID_API_KEY and replace stub in tools/registry/lv.py.",
    }
