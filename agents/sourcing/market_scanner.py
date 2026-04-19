from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.properties import search_properties
from tools.market import fetch_market_signals, find_sales_comps
from tools.rag import retrieve_documents

SPEC = AGENTS_BY_SLUG["market_scanner"]
TOOLS = [search_properties, fetch_market_signals, find_sales_comps, retrieve_documents, web_search]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
