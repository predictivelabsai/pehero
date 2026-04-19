"""Chat-UI building blocks."""

from __future__ import annotations

from fasthtml.common import (
    Div, Span, Button, A, P, H1, H2, H3, H4, Ul, Li, NotStr,
    Form, Textarea, Input, Hr, Article,
)

from agents.registry import AGENTS, AGENTS_BY_CATEGORY, CATEGORIES, AGENTS_BY_SLUG


def message_bubble(role: str, content: str, agent_slug: str | None = None):
    """Render a single persisted message."""
    header = None
    if role == "assistant" and agent_slug:
        agent = AGENTS_BY_SLUG.get(agent_slug)
        label = agent.name if agent else agent_slug
        header = Div(
            Span(agent.icon if agent else "◆", cls="msg-agent-icon"),
            Span(label, cls="msg-agent-label"),
            cls="msg-agent",
        )
    return Div(
        header,
        Div(NotStr(_render_content(content)), cls="msg-bubble"),
        cls=f"msg msg-{role}",
    )


def _render_content(content: str) -> str:
    """Trivial markdown-ish renderer (bold, italic, newlines). Kept dependency-free."""
    import html
    safe = html.escape(content)
    # code fences → <pre>
    import re
    safe = re.sub(r"```(.*?)```", lambda m: f"<pre>{m.group(1)}</pre>", safe, flags=re.DOTALL)
    # **bold**
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    # simple bullets
    safe = re.sub(r"(?m)^- (.*)$", r"<li>\1</li>", safe)
    safe = re.sub(r"(<li>.*?</li>\n?)+", r"<ul>\g<0></ul>", safe, flags=re.DOTALL)
    # newlines
    safe = safe.replace("\n", "<br>")
    return safe


def welcome_hero():
    """Empty-state hero with category chips + example prompts."""
    prompts = [
        ("triage: vertical SaaS, €8M EBITDA, 20% growth, €85M ask", "deal_triage"),
        ("lbo: 5-year model for Northwind Systems at 12x entry, 12% growth", "pro_forma_builder"),
        ("abstract: change-of-control across my top-10 customer MSAs", "lease_abstractor"),
        ("memo: draft the IC memo for Meridian Healthcare", "investor_memo"),
        ("price: where is pricing most below market across portcos?", "rent_optimization"),
        ("comps: software precedent M&A 2022-2024 under €500M EV", "comp_finder"),
    ]
    return Div(
        Div(
            Span("◆", cls="hero-mark"),
            H1("PEHero", cls="welcome-title"),
            P("Your Private Equity AI Agent Squad. Type a prompt — the router picks the right specialist.",
              cls="welcome-sub"),
            cls="welcome-head",
        ),
        Div(
            *[Button(
                Span(AGENTS_BY_SLUG[slug].icon if slug in AGENTS_BY_SLUG else "◆", cls="sugg-icon"),
                Span(text, cls="sugg-text"),
                cls="suggestion-chip",
                onclick=f"fillChat({text!r})",
            ) for text, slug in prompts],
            cls="suggestions",
        ),
        id="welcome-hero",
        cls="welcome-hero",
    )


def agent_browser():
    """Left-pane browser of all 22 agents, grouped by category."""
    groups = []
    for cat in CATEGORIES:
        agents = AGENTS_BY_CATEGORY.get(cat["key"], [])
        buttons = [
            Button(
                Span(a.icon, cls="aitem-icon"),
                Span(a.name, cls="aitem-name"),
                Span(a.prefix, cls="aitem-prefix"),
                cls="agent-item",
                onclick=f"fillChat({a.prefix + ' '!r})",
                title=a.one_liner,
            )
            for a in agents
        ]
        groups.append(Div(
            Button(
                Span(cat["icon"], cls="cat-icon"),
                Span(cat["name"], cls="cat-name"),
                Span(f"{len(agents)}", cls="cat-count"),
                Span("▸", cls="cat-arrow"),
                cls="cat-toggle",
                onclick=f"toggleGroup('cat-{cat['key']}')",
                id=f"btn-cat-{cat['key']}",
            ),
            Div(*buttons, cls="agent-list", id=f"cat-{cat['key']}"),
            cls="agent-group",
        ))
    return Div(*groups, cls="agent-browser")


def sessions_list(sessions: list[dict], current_sid: str = ""):
    """Renders the left-pane session history."""
    if not sessions:
        return Div(P("No sessions yet — send a message to start.", cls="sessions-empty"))
    items = []
    for s in sessions:
        is_active = str(s["id"]) == str(current_sid)
        title = s.get("title") or "Untitled session"
        items.append(Button(
            Span(cls=f"chat-dot{' active' if is_active else ''}"),
            Span(title[:48] + ("…" if len(title) > 48 else ""), cls="chat-session-title"),
            cls=f"chat-history-item{' active' if is_active else ''}",
            onclick=f"window.location.href='/app?sid={s['id']}'",
        ))
    return Div(*items, cls="session-list")


def _config_section(current_currency: str = "EUR"):
    """Configuration: currency selector (EUR default) + anything else down the line."""
    from utils.session import CURRENCIES, SYMBOLS
    pills = []
    for c in CURRENCIES:
        active = c == current_currency
        pills.append(Button(
            Span(SYMBOLS[c], cls="cfg-sym"),
            Span(c, cls="cfg-code"),
            cls=f"cfg-chip{' active' if active else ''}",
            onclick=f"setCurrency({c!r})",
        ))
    return Div(
        Div(Span("Currency", cls="cfg-label"),
            Span("affects agents + displays", cls="cfg-help"),
            cls="cfg-row"),
        Div(*pills, cls="cfg-pills"),
        cls="config-section",
    )


def _bottom_nav(current_path: str = ""):
    items = [
        ("Pipeline",     "/app/pipeline",     "◆"),
        ("Instructions", "/app/instructions", "✎"),
        ("Analytics",    "/app/analytics",    "∑"),
    ]
    links = []
    for label, href, icon in items:
        active = current_path.startswith(href)
        links.append(A(
            Span(icon, cls="bottom-nav-icon"),
            Span(label, cls="bottom-nav-label"),
            href=href,
            cls=f"bottom-nav-link{' active' if active else ''}",
        ))
    return Div(*links, cls="bottom-nav")


def left_pane(*, user_email: str | None, sessions: list[dict], current_sid: str = "",
              current_path: str = "", current_currency: str = "EUR"):
    """The full left pane composition."""
    signin_block = (
        Div(
            Span("◇", cls="user-mark"),
            Span(user_email, cls="user-email"),
            Button("Sign out", cls="sign-out-btn", onclick="signOut()"),
            cls="signed-in-bar",
        )
        if user_email else
        Button(Span("◇", cls="user-mark"), Span("Sign in", cls="sign-in-text"),
               cls="sign-in-btn", onclick="showSignIn()")
    )

    return Div(
        Div(
            A(Span("◆", cls="brand-mark"), Span("PEHero"),
              href="/", cls="brand-link"),
            Span("Beta", cls="brand-badge"),
            cls="left-header",
        ),
        Div(
            Div(
                Button("+ New chat", cls="new-chat-btn", onclick="newChat()"),
                Div(Span("Sessions", cls="section-label")),
                sessions_list(sessions, current_sid),
                cls="sessions-section",
            ),
            Hr(cls="left-hr"),
            Div(
                Div(Span("Agents", cls="section-label")),
                agent_browser(),
                cls="agents-section",
            ),
            Hr(cls="left-hr"),
            Div(
                Div(Span("Workspace", cls="section-label")),
                _bottom_nav(current_path),
                cls="workspace-section",
            ),
            Hr(cls="left-hr"),
            Div(
                Div(Span("Configuration", cls="section-label")),
                _config_section(current_currency=current_currency),
                cls="config-wrap",
            ),
            cls="left-body",
        ),
        Div(signin_block, cls="left-footer"),
        cls="left-pane", id="left-pane",
    )


def sample_cards(current_agent_slug: str | None = None):
    """Gemini-style contextual sample-question cards below the chat input.

    Renders the current agent's example_prompts (or a curated 6-pack when no
    agent is bound yet). Client-side, `updateSampleCards(slug)` refreshes the
    list whenever the user types a prefix or the router picks a new agent.
    """
    if current_agent_slug and current_agent_slug in AGENTS_BY_SLUG:
        agent = AGENTS_BY_SLUG[current_agent_slug]
        prompts = list(agent.example_prompts[:6])
        label = f"Try with {agent.name}"
    else:
        prompts = [
            "triage: vertical SaaS, €8M EBITDA, 20% growth, €85M ask",
            "lbo: 5-year model for Northwind at 12x entry, 12% growth",
            "comps: software precedent M&A 2022-2024 under €500M EV",
            "memo: draft the IC memo for Meridian Healthcare",
            "vdr: audit the data room for Meridian Healthcare",
            "crm: top 10 LPs to reach out to for Fund V",
        ]
        label = "Try a prompt"

    chips = [
        Button(
            Span(p, cls="sample-card-text"),
            cls="sample-card",
            onclick=f"fillChat({p!r}); sendMessage(null);",
            title=p,
        )
        for p in prompts
    ]
    return Div(
        Div(
            Span(label, cls="sample-cards-label"),
            id="sample-cards-label",
        ),
        Div(*chips, id="sample-cards-row", cls="sample-cards-row"),
        id="sample-cards",
        cls="sample-cards",
    )


def center_pane(*, messages: list[dict], current_agent_slug: str | None = None):
    has_messages = bool(messages)
    bubbles = [message_bubble(m["role"], m["content"], m.get("agent_slug")) for m in messages]

    input_placeholder = "Ask anything — or type a prefix like `triage:`, `memo:`, `pf:`"

    # Embed all agents' example_prompts as JSON for the client so we can
    # refresh sample cards without a round-trip whenever the router picks a
    # different slug.
    import json
    prompts_lookup = {a.slug: list(a.example_prompts[:6]) for a in AGENTS}
    names_lookup = {a.slug: a.name for a in AGENTS}

    return Div(
        Div(
            Div(
                Button("☰", cls="mobile-menu-btn", onclick="toggleLeftPane()"),
                Span("PEHero", cls="chat-header-title"),
                Span("·", cls="chat-header-dot"),
                Span(
                    AGENTS_BY_SLUG[current_agent_slug].name if current_agent_slug and current_agent_slug in AGENTS_BY_SLUG else "Auto-routed",
                    cls="chat-header-agent",
                    id="current-agent-label",
                ),
                cls="chat-header-left",
            ),
            Div(
                Button("Artifact", id="artifact-btn", cls="artifact-toggle-btn",
                       onclick="toggleArtifactPane()"),
                cls="chat-header-actions",
            ),
            cls="chat-header",
        ),
        Div(*bubbles, id="messages", cls="messages"),
        welcome_hero() if not has_messages else Div(id="welcome-hero", style="display:none"),
        Form(
            Textarea(
                id="chat-input", name="msg",
                cls="chat-textarea",
                placeholder=input_placeholder,
                rows="2",
                onkeydown="handleKey(event)",
                oninput="autoResize(this); onInputChange(this)",
            ),
            Button("Send", type="submit", cls="chat-send", id="send-btn"),
            id="chat-form",
            cls="chat-form",
            onsubmit="sendMessage(event)",
        ),
        sample_cards(current_agent_slug),
        # JSON blob the client reads to re-render sample cards per-agent
        NotStr(f'<script id="agent-prompts-data" type="application/json">{json.dumps(prompts_lookup)}</script>'),
        NotStr(f'<script id="agent-names-data" type="application/json">{json.dumps(names_lookup)}</script>'),
        cls="center-pane",
    )


def right_pane():
    """Artifact pane — starts empty; filled by SSE artifact_show events."""
    return Div(
        Div(
            Div(H3("Artifact", cls="right-title"),
                Span("", id="artifact-subtitle", cls="right-subtitle"),
                cls="right-header-left"),
            Button("✕", cls="right-close", onclick="toggleArtifactPane()"),
            cls="right-header",
        ),
        Div(
            Div(
                Div("◈", cls="artifact-empty-icon"),
                P("Artifacts appear here as agents produce them — company briefs, LBO models, comps tables, IC memo previews, RAG citations.",
                  cls="artifact-empty-text"),
                id="artifact-empty",
                cls="artifact-empty",
            ),
            Div(id="artifact-body", cls="artifact-body", style="display:none"),
            cls="right-body",
        ),
        id="right-pane", cls="right-pane",
    )


def signin_overlay():
    return Div(
        Div(
            H3("Sign in to PEHero"),
            P("Email only — we'll send a confirmation later.", cls="signin-sub"),
            Input(type="email", id="signin-email", placeholder="you@firm.com",
                  onkeydown="if(event.key==='Enter')doSignIn()"),
            Button("Continue →", onclick="doSignIn()"),
            cls="signin-box",
        ),
        cls="signin-overlay", id="signin-overlay",
        onclick="if(event.target===this)this.classList.remove('visible')",
    )
