from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_url: str = Field(default="", alias="DB_URL")
    xai_api_key: str = Field(default="", alias="XAI_API_KEY")
    xai_base_url: str = Field(default="https://api.x.ai/v1", alias="XAI_BASE_URL")
    xai_model: str = Field(default="grok-4-fast-reasoning", alias="XAI_MODEL")
    xai_agent_model: str = Field(default="grok-4", alias="XAI_AGENT_MODEL")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=384, alias="EMBEDDING_DIM")

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_secret: str = Field(default="change-me", alias="APP_SECRET")
    port: int = Field(default=5058, alias="PORT")


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
