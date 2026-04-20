"""Instructions page — edit + save per-agent system prompts.

/app/instructions              → list all 22 agents
/app/instructions/<slug>       → edit form
POST /app/instructions/<slug>  → persist to prompts/system/<slug>.md
"""

from __future__ import annotations

from pathlib import Path

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Div, Span, H1, H2, H3, H4, P, Ul, Li, A, Button,
    Form, Textarea, Input, Label,
)
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app import rt
from agents.registry import AGENTS, AGENTS_BY_SLUG
from chat.components import left_pane, signin_overlay
from chat.layout import _versioned
from utils.session import get_currency, currency_symbol
from chat.routes import _ensure_user, _list_sessions
from landing.components import TAILWIND_CONFIG, _favicon_links

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "system"
SHARED_DIR = Path(__file__).resolve().parent.parent / "prompts" / "shared"


def _head(title: str) -> Head:
    return Head(
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Title(f"{title} · PEHero"),
        *_favicon_links(),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(rel="stylesheet",
             href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"),
        Script(src="https://cdn.tailwindcss.com"),
        Script(NotStr(TAILWIND_CONFIG)),
        Link(rel="stylesheet", href="/static/site.css"),
        Link(rel="stylesheet", href=_versioned("app.css")),
        Link(rel="stylesheet", href="/static/pipeline.css"),
    )


@rt("/app/instructions")
def instructions_home(sess):
    uid, email = _ensure_user(sess)
    sessions = _list_sessions(uid) if uid else []

    items = []
    for a in AGENTS:
        path = PROMPTS_DIR / f"{a.slug}.md"
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        items.append(A(
            Div(
                Span(a.icon, cls="instr-icon"),
                Div(
                    Div(a.name, cls="instr-name"),
                    Div(a.one_liner, cls="instr-sub"),
                ),
                Span(f"{size}b" if exists else "missing", cls="instr-size"),
                cls="instr-row",
            ),
            href=f"/app/instructions/{a.slug}",
            cls="instr-link",
        ))

    body = Body(
        signin_overlay(),
        Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
        left_pane(user_email=email, sessions=sessions, current_sid="", current_currency=get_currency(sess)),
        Div(
            Div(
                Div(
                    Button("☰", cls="mobile-menu-btn", onclick="toggleLeftPane()"),
                    Span("Instructions", cls="chat-header-title"),
                    Span("·", cls="chat-header-dot"),
                    Span(f"{len(AGENTS)} agent prompts", cls="chat-header-agent"),
                    cls="chat-header-left",
                ),
                Div(
                    A("Back to chat", href="/app", cls="back-to-chat-btn"),
                    cls="chat-header-actions",
                ),
                cls="chat-header",
            ),
            Div(
                P("Edit the system prompts that drive each agent. Saves write to "
                  "prompts/system/<slug>.md and reload on the next conversation.",
                  cls="instr-intro"),
                A("Edit shared PE glossary",
                  href="/app/instructions/__shared__",
                  cls="instr-shared-link"),
                *items,
                cls="instr-list",
            ),
            cls="center-pane",
        ),
        Script(src=_versioned("chat.js")),
        cls="bg-bg text-ink font-sans antialiased app pane-closed pipeline-app",
    )
    return Html(_head("Instructions"), body, lang="en")


@rt("/app/instructions/{slug}")
def instruction_edit(sess, slug: str, saved: bool = False):
    uid, email = _ensure_user(sess)
    sessions = _list_sessions(uid) if uid else []

    if slug == "__shared__":
        path = SHARED_DIR / "pe_context.md"
        title = "Shared PE glossary"
        subtitle = "Prepended to every agent's system prompt"
    else:
        spec = AGENTS_BY_SLUG.get(slug)
        if not spec:
            return Html(_head("Not found"),
                        Body(Div(H1("Agent not found"),
                                 A("Back", href="/app/instructions"),
                                 cls="p-10 text-ink")))
        path = PROMPTS_DIR / f"{slug}.md"
        title = spec.name
        subtitle = spec.one_liner

    content = path.read_text() if path.exists() else ""

    banner = Div("Saved.", cls="save-banner") if saved else None

    body = Body(
        signin_overlay(),
        Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
        left_pane(user_email=email, sessions=sessions, current_sid="", current_currency=get_currency(sess)),
        Div(
            Div(
                Div(
                    Button("☰", cls="mobile-menu-btn", onclick="toggleLeftPane()"),
                    A("← Instructions", href="/app/instructions", cls="back-to-chat-btn"),
                    Span("·", cls="chat-header-dot"),
                    Span(title, cls="chat-header-title"),
                    cls="chat-header-left",
                ),
                cls="chat-header",
            ),
            Div(
                banner,
                P(subtitle, cls="instr-sub-big"),
                P(NotStr(f"<code>{path}</code>"), cls="instr-path"),
                Form(
                    Textarea(content, name="content", rows="28",
                             cls="instr-textarea",
                             spellcheck="false"),
                    Div(
                        Button("Save", type="submit", cls="chat-send instr-save"),
                        A("Cancel", href="/app/instructions", cls="back-to-chat-btn"),
                        cls="instr-actions",
                    ),
                    method="post",
                    action=f"/app/instructions/{slug}",
                    cls="instr-form",
                ),
                cls="instr-edit",
            ),
            cls="center-pane",
        ),
        Script(src=_versioned("chat.js")),
        cls="bg-bg text-ink font-sans antialiased app pane-closed pipeline-app",
    )
    return Html(_head(f"Edit — {title}"), body, lang="en")


@rt("/app/instructions/{slug}", methods=["POST"])
async def instruction_save(request: Request, slug: str):
    form = await request.form()
    content = form.get("content") or ""

    if slug == "__shared__":
        path = SHARED_DIR / "pe_context.md"
    else:
        if slug not in AGENTS_BY_SLUG:
            return RedirectResponse(url="/app/instructions", status_code=302)
        path = PROMPTS_DIR / f"{slug}.md"

    path.write_text(content)

    # Clear agent cache so next invocation re-loads the prompt
    try:
        from agents.base import cached_agent
        cached_agent.cache_clear()
    except Exception:
        pass

    return RedirectResponse(url=f"/app/instructions/{slug}?saved=1", status_code=302)
