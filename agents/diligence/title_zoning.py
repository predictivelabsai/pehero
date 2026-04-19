from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.diligence import check_title, check_zoning, record_finding

SPEC = AGENTS_BY_SLUG["title_zoning"]
TOOLS = [get_property, search_properties, check_title, check_zoning, record_finding]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
