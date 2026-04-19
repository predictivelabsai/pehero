from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import search_properties, get_property
from tools.market import find_sales_comps, fetch_market_signals
from tools.financials import normalize_t12

SPEC = AGENTS_BY_SLUG["deal_triage"]
TOOLS = [search_properties, get_property, find_sales_comps, fetch_market_signals, normalize_t12]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
