"""Cosine similarity retrieval over pehero_rag with metadata filters."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass

from db import connect
from rag.embeddings import embed_one

log = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    doc_type: str
    title: str
    company_id: int | None
    ord: int
    text: str
    score: float  # cosine similarity in [0, 1]
    metadata: dict


def _vec_literal(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def retrieve(
    query: str,
    *,
    k: int = 6,
    doc_types: list[str] | None = None,
    company_id: int | None = None,
    log_query: bool = True,
    user_id: int | None = None,
    session_id: int | None = None,
) -> list[RetrievedChunk]:
    started = time.time()
    vec = embed_one(query)

    sql = [
        """
        SELECT c.id AS chunk_id, c.document_id, c.ord, c.text, c.metadata,
               d.doc_type, d.title, d.company_id,
               1 - (e.embedding <=> %s::vector) AS score
        FROM pehero_rag.chunks c
        JOIN pehero_rag.embeddings e ON e.chunk_id = c.id
        JOIN pehero_rag.documents d ON d.id = c.document_id
        WHERE 1=1
        """
    ]
    params: list = [_vec_literal(vec)]
    if doc_types:
        sql.append("AND d.doc_type = ANY(%s)")
        params.append(doc_types)
    if company_id is not None:
        sql.append("AND d.company_id = %s")
        params.append(company_id)
    sql.append("ORDER BY e.embedding <=> %s::vector ASC LIMIT %s")
    params.extend([_vec_literal(vec), k])

    with connect() as conn, conn.cursor() as cur:
        cur.execute(" ".join(sql), params)
        rows = cur.fetchall()

        out = [
            RetrievedChunk(
                chunk_id=r[0],
                document_id=r[1],
                ord=r[2],
                text=r[3],
                metadata=r[4] or {},
                doc_type=r[5],
                title=r[6],
                company_id=r[7],
                score=float(r[8]),
            )
            for r in rows
        ]

        if log_query:
            cur.execute(
                """
                INSERT INTO pehero_rag.rag_queries (user_id, session_id, query, top_k, filters, latency_ms)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    user_id,
                    session_id,
                    query,
                    k,
                    json.dumps({"doc_types": doc_types, "company_id": company_id}),
                    int((time.time() - started) * 1000),
                ),
            )
            conn.commit()

    return out
