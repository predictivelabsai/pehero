"""Embedding provider — pluggable.

Providers:
  - local  (default): fastembed ONNX runtime, no API key, ~100 MB model.
             Default: BAAI/bge-small-en-v1.5 (384 dim)
  - openai: OpenAI embeddings (requires OPENAI_API_KEY).
             Default: text-embedding-3-small (1536 dim)
  - xai:   reserved for when xAI ships embeddings.

`EMBEDDING_DIM` in the env must match the chosen model. It is baked into the
pgvector column type at migration time, so changing provider/dim requires
rerunning `python -m db.migrate --drop`.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from utils.config import settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _local_model():
    from fastembed import TextEmbedding

    s = settings()
    log.info("loading local embedding model %s (first run downloads ~100MB)", s.embedding_model)
    return TextEmbedding(model_name=s.embedding_model)


@lru_cache(maxsize=1)
def _openai_client():
    from openai import OpenAI

    s = settings()
    if not s.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY required for embedding_provider=openai")
    return OpenAI(api_key=s.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    s = settings()
    provider = s.embedding_provider.lower()

    if provider == "local":
        model = _local_model()
        return [list(map(float, v)) for v in model.embed(texts)]

    if provider == "openai":
        resp = _openai_client().embeddings.create(model=s.embedding_model, input=texts)
        return [d.embedding for d in resp.data]

    raise RuntimeError(f"unknown EMBEDDING_PROVIDER={provider}")


def embed_one(text: str) -> list[float]:
    return embed_texts([text])[0]
