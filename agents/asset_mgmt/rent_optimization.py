from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.asset import rent_optimization_recs
from tools.market import find_rent_comps

SPEC = AGENTS_BY_SLUG["rent_optimization"]
TOOLS = [get_property, search_properties, rent_optimization_recs, find_rent_comps]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
