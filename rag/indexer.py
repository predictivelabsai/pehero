"""Chunk + embed + upsert into pehero_rag."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from db import connect
from rag.embeddings import embed_texts

log = logging.getLogger(__name__)

# Simple target chunk size. Splits on paragraph boundaries first; falls back
# to sentence splits if a paragraph is too long.
TARGET_CHARS = 1800
OVERLAP_CHARS = 150


@dataclass
class DocIn:
    title: str
    doc_type: str
    text: str
    company_id: int | None = None
    source_path: str | None = None
    metadata: dict | None = None


def chunk_text(text: str, target: int = TARGET_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    """Greedy paragraph-first chunker with character overlap."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > target:
            for s in re.split(r"(?<=[.!?])\s+", p):
                if len(buf) + len(s) + 1 > target:
                    if buf:
                        chunks.append(buf.strip())
                    buf = (buf[-overlap:] if overlap and buf else "") + " " + s
                else:
                    buf = (buf + " " + s).strip()
            continue
        if len(buf) + len(p) + 2 > target:
            if buf:
                chunks.append(buf.strip())
            buf = (buf[-overlap:] if overlap and buf else "") + "\n\n" + p
        else:
            buf = (buf + "\n\n" + p).strip() if buf else p
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def _vec_literal(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def upsert_document(doc: DocIn, *, replace: bool = False) -> int:
    """Insert document + chunks + embeddings. Returns document_id.

    If replace=True and a document with the same (title, source_path) already
    exists, delete it first so re-runs are idempotent.
    """
    meta_json = json.dumps(doc.metadata or {})

    with connect() as conn, conn.cursor() as cur:
        if replace:
            cur.execute(
                "DELETE FROM pehero_rag.documents WHERE title = %s AND source_path IS NOT DISTINCT FROM %s",
                (doc.title, doc.source_path),
            )

        cur.execute(
            """
            INSERT INTO pehero_rag.documents (company_id, doc_type, title, source_path, metadata)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            RETURNING id
            """,
            (doc.company_id, doc.doc_type, doc.title, doc.source_path, meta_json),
        )
        doc_id = cur.fetchone()[0]

        chunks = chunk_text(doc.text)
        if not chunks:
            conn.commit()
            return doc_id

        vectors = embed_texts(chunks)
        assert len(vectors) == len(chunks)

        for i, (text, vec) in enumerate(zip(chunks, vectors)):
            cur.execute(
                """
                INSERT INTO pehero_rag.chunks (document_id, ord, text, token_count)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (doc_id, i, text, len(text) // 4),
            )
            chunk_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO pehero_rag.embeddings (chunk_id, embedding) VALUES (%s, %s::vector)",
                (chunk_id, _vec_literal(vec)),
            )

        conn.commit()
    return doc_id


def upsert_documents(docs: list[DocIn], *, replace: bool = False) -> list[int]:
    ids: list[int] = []
    for d in docs:
        ids.append(upsert_document(d, replace=replace))
    return ids


def build_ann_index(lists: int = 100) -> None:
    """Create the ivfflat cosine index. Call after the table is populated
    with enough rows — ivfflat clusters are assigned at index-build time.

    Rule of thumb: lists ≈ rows / 1000 for moderate tables, sqrt(rows) for large.
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM pehero_rag.embeddings")
        n = cur.fetchone()[0]
        if n < 100:
            log.info("only %d embeddings — skipping ivfflat index (not worth it)", n)
            return
        adjusted = max(10, min(lists, n // 50))
        log.info("building ivfflat cosine index over %d rows (lists=%d)", n, adjusted)
        cur.execute("DROP INDEX IF EXISTS pehero_rag.embeddings_cosine_idx")
        cur.execute(
            f"CREATE INDEX embeddings_cosine_idx ON pehero_rag.embeddings "
            f"USING ivfflat (embedding vector_cosine_ops) WITH (lists = {adjusted})"
        )
        conn.commit()
