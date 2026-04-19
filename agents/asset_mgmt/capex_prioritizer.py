from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.asset import capex_ranking
from tools.diligence import pcr_findings

SPEC = AGENTS_BY_SLUG["capex_prioritizer"]
TOOLS = [get_property, search_properties, capex_ranking, pcr_findings]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
