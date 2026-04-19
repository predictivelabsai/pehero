from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.financials import normalize_t12, build_pro_forma, compute_returns
from tools.rentroll import summarize_rent_roll

SPEC = AGENTS_BY_SLUG["pro_forma_builder"]
TOOLS = [get_property, search_properties, summarize_rent_roll, normalize_t12, build_pro_forma, compute_returns]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
