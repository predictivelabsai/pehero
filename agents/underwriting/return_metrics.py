from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.financials import build_pro_forma, compute_returns, size_debt

SPEC = AGENTS_BY_SLUG["return_metrics"]
TOOLS = [get_property, search_properties, build_pro_forma, compute_returns, size_debt]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
