"""Retrieval tool for the pehero_rag corpus."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from rag.retriever import retrieve


class RetrieveArgs(BaseModel):
    query: str = Field(description="Natural-language query to retrieve relevant document chunks for.")
    k: int = Field(default=6, ge=1, le=20)
    doc_types: Optional[list[str]] = Field(
        default=None,
        description="Restrict to specific doc types: cim, msa, qoe, legal, esg, tax, tech_ddq, industry, lp_letter, ic_memo.",
    )
    company_id: Optional[int] = Field(default=None, description="Restrict to a single company's docs.")


def _retrieve(**kw) -> str:
    args = RetrieveArgs(**kw)
    chunks = retrieve(args.query, k=args.k, doc_types=args.doc_types, company_id=args.company_id)
    if not chunks:
        return "No relevant documents found."
    items = [
        {
            "title": c.title,
            "doc_type": c.doc_type,
            "company_id": c.company_id,
            "score": round(c.score, 3),
            "snippet": c.text[:500],
        }
        for c in chunks
    ]
    artifact_payload = {
        "kind": "citations",
        "title": f"Retrieved {len(chunks)} sources",
        "subtitle": args.query[:60],
        "items": items,
    }
    return "__ARTIFACT__" + json.dumps(artifact_payload)


retrieve_documents = StructuredTool.from_function(
    func=_retrieve,
    name="retrieve_documents",
    description="Semantic search across CIMs, QoE reports, MSAs, legal DD, ESG reports, tax memos, tech DDQs, and industry reports indexed in the RAG corpus. Use this when the user asks about document contents.",
    args_schema=RetrieveArgs,
)

# Alias
rag_search = retrieve_documents
