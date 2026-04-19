"""Full 3-pane chat page layout."""

from __future__ import annotations

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Div, Span,
)

from landing.components import SITE_NAME, TAILWIND_CONFIG
from chat.components import left_pane, center_pane, right_pane, signin_overlay


def chat_page(*, user_email: str | None, sessions: list, current_sid: str = "",
              messages: list, current_agent_slug: str | None = None):
    head = Head(
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="description", content="PEHero — agentic AI for private equity deal teams"),
        Title(f"App · {SITE_NAME}"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
        ),
        Script(src="https://cdn.tailwindcss.com"),
        Script(NotStr(TAILWIND_CONFIG)),
        Link(rel="stylesheet", href="/static/site.css"),
        Link(rel="stylesheet", href="/static/app.css"),
    )
    body = Body(
        signin_overlay(),
        Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
        left_pane(user_email=user_email, sessions=sessions, current_sid=current_sid),
        center_pane(messages=messages, current_agent_slug=current_agent_slug),
        right_pane(),
        Script(src="/static/chat.js"),
        cls="bg-bg text-ink font-sans antialiased app pane-closed",
    )
    return Html(head, body, lang="en")
