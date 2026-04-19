from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.financials import normalize_t12

SPEC = AGENTS_BY_SLUG["t12_normalizer"]
TOOLS = [get_property, search_properties, normalize_t12]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
