from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.properties import search_properties, get_property
from tools.market import find_sales_comps, find_rent_comps

SPEC = AGENTS_BY_SLUG["comp_finder"]
TOOLS = [search_properties, get_property, find_sales_comps, find_rent_comps, web_search]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
