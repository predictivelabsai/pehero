from __future__ import annotations
from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.properties import get_property, search_properties
from tools.diligence import audit_doc_room
from tools.rag import retrieve_documents

SPEC = AGENTS_BY_SLUG["doc_room_auditor"]
TOOLS = [get_property, search_properties, audit_doc_room, retrieve_documents]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
