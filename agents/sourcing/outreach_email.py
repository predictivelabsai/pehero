from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.properties import search_properties, get_property
from tools.market import fetch_market_signals
from tools.rag import retrieve_documents

SPEC = AGENTS_BY_SLUG["outreach_email"]
TOOLS = [search_properties, get_property, fetch_market_signals, retrieve_documents, web_search]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
