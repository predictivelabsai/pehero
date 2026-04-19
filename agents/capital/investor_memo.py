from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.capital import deal_brief
from tools.rag import retrieve_documents
from tools.market import find_sales_comps, fetch_market_signals
from tools.baltic import baltic_lookup, baltic_tax_status

SPEC = AGENTS_BY_SLUG["investor_memo"]
TOOLS = [
    get_property, search_properties, deal_brief, retrieve_documents,
    find_sales_comps, fetch_market_signals,
    baltic_lookup, baltic_tax_status,
]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
