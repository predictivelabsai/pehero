from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.diligence import pcr_findings, record_finding
from tools.rag import retrieve_documents

SPEC = AGENTS_BY_SLUG["physical_condition"]
TOOLS = [get_property, search_properties, pcr_findings, record_finding, retrieve_documents]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
