"""Apply schema.sql + rag_schema.sql idempotently.

Usage:
    python -m db.migrate          # apply both
    python -m db.migrate --drop   # DANGER: drops pehero schemas first
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from db import connect
from utils.config import settings

log = logging.getLogger(__name__)

SCHEMA_FILES = [
    Path(__file__).with_name("schema.sql"),
    Path(__file__).with_name("rag_schema.sql"),
]


def _apply(sql: str) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def _render(path: Path) -> str:
    text = path.read_text()
    return text.replace("{{EMBEDDING_DIM}}", str(settings().embedding_dim))


def migrate(drop: bool = False) -> None:
    if drop:
        print("dropping pehero + pehero_rag schemas…")
        _apply("DROP SCHEMA IF EXISTS pehero_rag CASCADE; DROP SCHEMA IF EXISTS pehero CASCADE;")

    for f in SCHEMA_FILES:
        print(f"applying {f.name} (embedding_dim={settings().embedding_dim})")
        _apply(_render(f))

    # Incremental column additions (idempotent).
    _apply("""
        ALTER TABLE pehero.chat_sessions
            ADD COLUMN IF NOT EXISTS share_token TEXT UNIQUE;
    """)

    print("migration complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", action="store_true", help="drop pehero schemas first")
    args = ap.parse_args()
    migrate(drop=args.drop)
