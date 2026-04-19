from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.capital import crm_lookup

SPEC = AGENTS_BY_SLUG["fundraising_crm"]
TOOLS = [crm_lookup]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
