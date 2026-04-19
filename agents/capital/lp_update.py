from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.capital import portfolio_snapshot, crm_lookup
from tools.market import fetch_market_signals

SPEC = AGENTS_BY_SLUG["lp_update"]
TOOLS = [portfolio_snapshot, crm_lookup, fetch_market_signals]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
