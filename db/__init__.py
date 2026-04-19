"""Database connection helpers.

We keep this deliberately thin — plain psycopg connection pool + a SQLAlchemy
engine for places where parameter binding + pandas io is more ergonomic.
Schemas are always qualified (`pehero.*`, `pehero_rag.*`) in SQL; we
never rely on `search_path`.
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache

import psycopg
from psycopg_pool import ConnectionPool
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from utils.config import settings


@lru_cache(maxsize=1)
def pool() -> ConnectionPool:
    p = ConnectionPool(conninfo=settings().db_url, min_size=1, max_size=8, open=False)
    p.open()
    return p


@contextmanager
def connect():
    with pool().connection() as conn:
        yield conn


@lru_cache(maxsize=1)
def engine() -> Engine:
    return create_engine(settings().db_url, pool_pre_ping=True, pool_size=4, max_overflow=4)


def fetch_all(sql: str, params: tuple | dict | None = None) -> list[dict]:
    with connect() as conn, conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(sql, params or ())
        return list(cur.fetchall())


def fetch_one(sql: str, params: tuple | dict | None = None) -> dict | None:
    with connect() as conn, conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql: str, params: tuple | dict | None = None) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        conn.commit()
