from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.asset import tenant_churn

SPEC = AGENTS_BY_SLUG["tenant_churn"]
TOOLS = [get_property, search_properties, tenant_churn]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
