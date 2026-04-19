"""Thin cookie-session helpers shared by chat + auth routes."""

from __future__ import annotations

from typing import Any


def get_user_email(session: dict[str, Any]) -> str | None:
    return session.get("user_email")


def set_user_email(session: dict[str, Any], email: str) -> None:
    session["user_email"] = email.strip().lower()


def clear_user(session: dict[str, Any]) -> None:
    session.pop("user_email", None)
    session.pop("user_id", None)


def get_user_id(session: dict[str, Any]) -> int | None:
    uid = session.get("user_id")
    return int(uid) if uid is not None else None


def set_user_id(session: dict[str, Any], user_id: int) -> None:
    session["user_id"] = int(user_id)
