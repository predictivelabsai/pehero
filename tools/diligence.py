"""Due diligence tools — abstract contracts, audit VDR, check legal/ESG/operations."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db import connect, fetch_all, fetch_one
from rag.retriever import retrieve


def _resolve_cid(slug_or_id):
    try:
        return int(slug_or_id)
    except (TypeError, ValueError):
        row = fetch_one("SELECT id FROM pehero.companies WHERE slug = %s", (slug_or_id,))
        return row["id"] if row else None


class AbstractContractArgs(BaseModel):
    slug_or_id: Optional[str] = Field(default=None, description="Company slug or id.")
    counterparty: Optional[str] = Field(default=None, description="Counterparty filter.")
    contract_type: Optional[str] = Field(
        default=None,
        description="customer_msa | supplier | employment | license | lease | loan | other",
    )


def _abstract_contract(**kw) -> str:
    args = AbstractContractArgs(**kw)
    sql = ["SELECT c.*, co.name AS company_name FROM pehero.contracts c "
           "JOIN pehero.companies co ON co.id = c.company_id WHERE c.status = 'active'"]
    params: list = []
    if args.slug_or_id:
        try:
            cid = int(args.slug_or_id)
            sql.append("AND c.company_id = %s"); params.append(cid)
        except (TypeError, ValueError):
            sql.append("AND co.slug = %s"); params.append(args.slug_or_id)
    if args.counterparty:
        sql.append("AND c.counterparty ILIKE %s"); params.append(f"%{args.counterparty}%")
    if args.contract_type:
        sql.append("AND c.contract_type = %s"); params.append(args.contract_type)
    sql.append("ORDER BY c.annual_value DESC NULLS LAST LIMIT 15")
    rows = fetch_all(" ".join(sql), tuple(params))
    if not rows:
        return "No matching contracts."
    abstracts = [
        {
            "company": r["company_name"],
            "counterparty": r["counterparty"],
            "contract_type": r["contract_type"],
            "start_date": str(r["start_date"]) if r["start_date"] else None,
            "end_date": str(r["end_date"]) if r["end_date"] else None,
            "annual_value": float(r["annual_value"]) if r["annual_value"] else None,
            "auto_renew": r["auto_renew"],
            "change_of_control_trigger": r["change_of_control_trigger"],
            "termination_notice_days": r["termination_notice_days"],
            "exclusivity": r["exclusivity"],
        }
        for r in rows
    ]
    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": "Contract abstracts",
        "columns": ["company", "counterparty", "contract_type", "start_date", "end_date",
                    "annual_value", "auto_renew", "change_of_control_trigger",
                    "termination_notice_days", "exclusivity"],
        "rows": abstracts,
        "summary": {"count": len(abstracts)},
    }, default=str)


abstract_contracts = StructuredTool.from_function(
    func=_abstract_contract,
    name="abstract_contracts",
    description="Abstract active material contracts into structured records — counterparty, term, CoC trigger, termination notice, exclusivity, annual value.",
    args_schema=AbstractContractArgs,
)
# Back-compat alias
abstract_leases = abstract_contracts


class VdrArgs(BaseModel):
    slug_or_id: str = Field(description="Company VDR to audit.")


DD_CHECKLIST = [
    ("msa", "Top customer MSAs abstracted and reconciled to revenue concentration"),
    ("legal", "Corporate records, minute book, and litigation searches"),
    ("qoe", "Quality-of-earnings (QoE) report with EBITDA bridge"),
    ("tax", "Tax diligence — recent returns, state nexus, R&D credits"),
    ("esg", "ESG disclosures / policies / emissions data"),
    ("tech_ddq", "Tech & security DDQ, pen-test summary"),
    ("industry", "Independent industry / commercial report"),
    ("cim", "Confidential Information Memorandum from sell-side"),
    ("contracts", "Material contracts (customers, suppliers, key employees) in VDR"),
    ("financials", "Monthly financials tied out to QoE"),
    ("cap_table", "Clean fully-diluted cap table with liquidation prefs"),
]


def _audit_vdr(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."

    co = fetch_one("SELECT name FROM pehero.companies WHERE id = %s", (cid,))
    rag_docs = fetch_all(
        "SELECT doc_type, count(*) AS n FROM pehero_rag.documents "
        "WHERE company_id = %s GROUP BY doc_type",
        (cid,),
    )
    rag_counts = {r["doc_type"]: r["n"] for r in rag_docs}
    contracts = fetch_one(
        "SELECT count(*) as n FROM pehero.contracts WHERE company_id = %s AND status='active'",
        (cid,),
    )
    fin = fetch_one("SELECT count(*) as n FROM pehero.financials WHERE company_id = %s", (cid,))
    cap = fetch_one("SELECT count(*) as n FROM pehero.cap_tables WHERE company_id = %s", (cid,))

    findings = []
    for doc_type, label in DD_CHECKLIST:
        if doc_type == "contracts":
            present = (contracts["n"] or 0) > 0
        elif doc_type == "financials":
            present = (fin["n"] or 0) > 0
        elif doc_type == "cap_table":
            present = (cap["n"] or 0) > 0
        else:
            present = (rag_counts.get(doc_type, 0) > 0)
        findings.append({
            "item": label,
            "doc_type": doc_type,
            "status": "Present" if present else "Missing",
            "severity": "info" if present else "high",
        })

    return "__ARTIFACT__" + json.dumps({
        "kind": "table",
        "title": f"VDR audit — {co['name']}",
        "subtitle": f"{sum(1 for f in findings if f['status']=='Present')}/{len(findings)} items present",
        "columns": ["item", "status", "severity"],
        "rows": findings,
    })


audit_vdr = StructuredTool.from_function(
    func=_audit_vdr,
    name="audit_vdr",
    description="Audit a company's virtual data room against a PE DD checklist; flags missing items.",
    args_schema=VdrArgs,
)
# Back-compat alias
audit_doc_room = audit_vdr


class RagDocArgs(BaseModel):
    slug_or_id: str
    query: str = Field(default="")


def _check_legal(slug_or_id: str, query: str = "") -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    chunks = retrieve(query or "open litigation regulatory licensure consents change of control",
                      k=5, doc_types=["legal"], company_id=cid)
    if not chunks:
        return "No legal DD indexed."
    items = [{"title": c.title, "doc_type": c.doc_type, "score": round(c.score, 3),
              "snippet": c.text[:600]} for c in chunks]
    return "__ARTIFACT__" + json.dumps({
        "kind": "citations", "title": "Legal & regulatory check", "items": items,
    })


check_legal = StructuredTool.from_function(
    func=_check_legal,
    name="check_legal",
    description="Extract material legal/regulatory items (open litigation, licensure gaps, required consents) from the RAG corpus for a company.",
    args_schema=RagDocArgs,
)
check_title = check_legal  # back-compat


def _check_esg(slug_or_id: str, query: str = "") -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    chunks = retrieve(query or "environmental emissions worker safety governance diversity",
                      k=5, doc_types=["esg"], company_id=cid)
    if not chunks:
        return "No ESG documents indexed."
    items = [{"title": c.title, "doc_type": c.doc_type, "score": round(c.score, 3),
              "snippet": c.text[:600]} for c in chunks]
    return "__ARTIFACT__" + json.dumps({
        "kind": "citations", "title": "ESG findings", "items": items,
    })


check_esg = StructuredTool.from_function(
    func=_check_esg,
    name="check_esg",
    description="Pull ESG report findings for a company — environmental liabilities, social, governance.",
    args_schema=RagDocArgs,
)
check_zoning = check_esg  # back-compat
flag_environmental = check_esg  # back-compat


def _ops_findings(slug_or_id: str, query: str = "") -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    chunks = retrieve(query or "working capital systems gaps pricing unit economics organization",
                      k=5, doc_types=["qoe", "tech_ddq", "industry"], company_id=cid)
    if not chunks:
        return "No operational DD indexed."
    items = [{"title": c.title, "doc_type": c.doc_type, "score": round(c.score, 3),
              "snippet": c.text[:600]} for c in chunks]
    return "__ARTIFACT__" + json.dumps({
        "kind": "citations", "title": "Operational DD findings", "items": items,
    })


ops_findings = StructuredTool.from_function(
    func=_ops_findings,
    name="ops_findings",
    description="Pull operational DD findings for a company — working capital, systems, pricing, unit economics.",
    args_schema=RagDocArgs,
)
pcr_findings = ops_findings  # back-compat


def _record_dd_finding(company_id: int, agent_slug: str, category: str,
                       severity: str, summary: str, detail: Optional[str] = None,
                       source_doc: Optional[str] = None) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pehero.dd_findings "
            "(company_id, agent_slug, category, severity, summary, detail, source_doc) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (company_id, agent_slug, category, severity, summary, detail, source_doc),
        )
        conn.commit()


class FindingArgs(BaseModel):
    slug_or_id: str
    category: str = Field(description="legal | tax | commercial | financial | operational | esg | it | hr")
    severity: str = Field(description="info | low | medium | high | critical")
    summary: str
    detail: Optional[str] = None
    source_doc: Optional[str] = None


def _record_finding(**kw) -> str:
    args = FindingArgs(**kw)
    cid = _resolve_cid(args.slug_or_id)
    if not cid:
        return "Company not found."
    _record_dd_finding(cid, "diligence", args.category, args.severity, args.summary,
                       args.detail, args.source_doc)
    return "Recorded."


record_finding = StructuredTool.from_function(
    func=_record_finding,
    name="record_finding",
    description="Record a DD finding against a company for downstream tracking.",
    args_schema=FindingArgs,
)


class ListFindingsArgs(BaseModel):
    slug_or_id: str


def _list_findings(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    rows = fetch_all(
        "SELECT agent_slug, category, severity, summary FROM pehero.dd_findings "
        "WHERE company_id = %s ORDER BY "
        "CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 "
        "WHEN 'low' THEN 3 ELSE 4 END, created_at DESC",
        (cid,),
    )
    return json.dumps([dict(r) for r in rows], default=str)


list_findings = StructuredTool.from_function(
    func=_list_findings,
    name="list_findings",
    description="List all DD findings recorded for a company, severity-sorted.",
    args_schema=ListFindingsArgs,
)


class ListDocsArgs(BaseModel):
    slug_or_id: str


def _list_documents(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    rows = fetch_all(
        "SELECT doc_type, title, created_at FROM pehero_rag.documents "
        "WHERE company_id = %s ORDER BY doc_type, title",
        (cid,),
    )
    return json.dumps([{"doc_type": r["doc_type"], "title": r["title"],
                        "created_at": str(r["created_at"])} for r in rows])


list_documents = StructuredTool.from_function(
    func=_list_documents,
    name="list_documents",
    description="List VDR documents indexed for a company.",
    args_schema=ListDocsArgs,
)


class ListContractsArgs(BaseModel):
    slug_or_id: str


def _list_contracts(slug_or_id: str) -> str:
    cid = _resolve_cid(slug_or_id)
    if not cid:
        return "Company not found."
    rows = fetch_all(
        "SELECT counterparty, contract_type, start_date, end_date, annual_value, "
        "auto_renew, change_of_control_trigger, exclusivity, status "
        "FROM pehero.contracts WHERE company_id = %s ORDER BY annual_value DESC NULLS LAST LIMIT 50",
        (cid,),
    )
    return json.dumps([dict(r) for r in rows], default=str)


list_contracts = StructuredTool.from_function(
    func=_list_contracts,
    name="list_contracts",
    description="List top contracts (by annual value) for a company — customer MSAs, suppliers, employment, etc.",
    args_schema=ListContractsArgs,
)
