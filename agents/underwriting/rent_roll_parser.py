from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.rentroll import summarize_rent_roll, lease_expiry_waterfall, walt_years

SPEC = AGENTS_BY_SLUG["rent_roll_parser"]
TOOLS = [get_property, search_properties, summarize_rent_roll, lease_expiry_waterfall, walt_years]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
