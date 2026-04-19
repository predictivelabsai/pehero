from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import search_properties, get_property
from tools.market import fetch_market_signals

SPEC = AGENTS_BY_SLUG["seller_intent"]
TOOLS = [search_properties, get_property, fetch_market_signals]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
