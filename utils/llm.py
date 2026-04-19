"""LLM factory — xAI Grok via OpenAI-compatible endpoint.

All agents should call ``build_llm()`` (default reasoning model) or
``build_agent_llm()`` (premium model with reliable tool-calling) instead of
constructing ChatOpenAI directly.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from utils.config import settings


def build_llm(model: str | None = None, temperature: float = 0.0, **kw) -> ChatOpenAI:
    s = settings()
    return ChatOpenAI(
        model=model or s.xai_model,
        api_key=s.xai_api_key,
        base_url=s.xai_base_url,
        temperature=temperature,
        timeout=300,
        **kw,
    )


def build_agent_llm(temperature: float = 0.0, **kw) -> ChatOpenAI:
    """LLM for LangGraph ReAct agents — uses the premium tool-calling model."""
    return build_llm(model=settings().xai_agent_model, temperature=temperature, **kw)


@lru_cache(maxsize=1)
def default_llm() -> ChatOpenAI:
    return build_llm()
