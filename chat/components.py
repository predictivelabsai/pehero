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
    """Server-side markdown → HTML for persisted messages."""
    import html as _html
    import re

    safe = _html.escape(content)
    # code fences → <pre>
    safe = re.sub(r"```(.*?)```", lambda m: f"<pre>{m.group(1)}</pre>", safe, flags=re.DOTALL)
    # **bold**
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)

    lines = safe.split("\n")
    out = []
    in_list = False
    in_table = False
    is_header = True
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            if re.fullmatch(r"\|[\s\-:|]+\|", stripped):
                continue
            if not in_table:
                out.append('<table>')
                in_table = True
                is_header = True
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            tag = "th" if is_header else "td"
            out.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
            is_header = False
        else:
            if in_table:
                out.append("</table>")
                in_table = False
            if stripped.startswith("- "):
                if not in_list:
                    out.append("<ul>")
                    in_list = True
                out.append(f"<li>{stripped[2:]}</li>")
            else:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                if stripped.startswith("### "):
                    out.append(f"<h4>{stripped[4:]}</h4>")
                elif stripped.startswith("## "):
                    out.append(f"<h3>{stripped[3:]}</h3>")
                elif stripped.startswith("# "):
                    out.append(f"<h2>{stripped[2:]}</h2>")
                else:
                    out.append(line if line.strip() else "<br>")
    if in_list:
        out.append("</ul>")
    if in_table:
        out.append("</table>")
    return "\n".join(out)


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
    """Configuration: currency selector (EUR default) + Integrations submenu."""
    from utils.session import CURRENCIES, SYMBOLS
    from utils.config import settings

    pills = []
    for c in CURRENCIES:
        active = c == current_currency
        pills.append(Button(
            Span(SYMBOLS[c], cls="cfg-sym"),
            Span(c, cls="cfg-code"),
            cls=f"cfg-chip{' active' if active else ''}",
            onclick=f"setCurrency({c!r})",
        ))

    s = settings()
    integrations = [
        ("EE", "Estonia", "Äriregister", bool(s.ee_ari_api_key), "public endpoint"),
        ("EE", "Estonia", "EMTA (tax)",  bool(s.ee_emta_api_key), None),
        ("LT", "Lithuania", "Registrų centras", bool(s.lt_cr_api_key), "public atviri duomenys"),
        ("LT", "Lithuania", "VMI (tax)",  bool(s.lt_vmi_api_key), None),
        ("LV", "Latvia",   "UR",         bool(s.lv_ur_api_key), None),
        ("LV", "Latvia",   "VID (tax)",  bool(s.lv_vid_api_key), None),
        ("",   "Web",      "Tavily",     bool(s.tavily_api_key), "default"),
        ("",   "Web",      "EXA",        bool(s.exa_api_key), "fallback"),
    ]
    integration_rows = []
    for flag, country, name, connected, note in integrations:
        status_cls = "ok" if connected else (" fallback" if note else " off")
        dot = Span(cls=f"integration-dot {'ok' if connected else ''}")
        label_text = f"{flag} {name}" if flag else name
        note_el = Span(note, cls="integration-note") if note else Span("", cls="integration-note")
        integration_rows.append(Div(
            dot,
            Span(label_text, cls="integration-name"),
            note_el,
            Span("connected" if connected else "off",
                 cls=f"integration-status{' ok' if connected else ''}"),
            cls="integration-row",
        ))

    return Div(
        # Currency block
        Div(Span("Currency", cls="cfg-label"),
            Span("affects agents + displays", cls="cfg-help"),
            cls="cfg-row"),
        Div(*pills, cls="cfg-pills"),
        # Integrations submenu
        Button(
            Span("▸", cls="cfg-arrow"),
            Span("Integrations", cls="cfg-label"),
            Span(f"{sum(1 for i in integrations if i[3])}/{len(integrations)}",
                 cls="cfg-count"),
            cls="cfg-integrations-toggle",
            onclick="toggleGroup('integrations-list')",
            id="btn-integrations-list",
        ),
        Div(*integration_rows, cls="integration-list", id="integrations-list"),
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
                Button("Copy chat", id="copy-chat-btn", cls="chat-action-btn",
                       onclick="copyChat()"),
                Button("Share", id="share-chat-btn", cls="chat-action-btn",
                       onclick="shareChat()"),
                Button("Canvas", id="artifact-btn", cls="artifact-toggle-btn",
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
    """Canvas pane — starts empty; filled by SSE artifact_show events."""
    return Div(
        Div(
            Div(H3("Canvas", cls="right-title"),
                Span("", id="artifact-subtitle", cls="right-subtitle"),
                cls="right-header-left"),
            Button("✕", cls="right-close", onclick="toggleArtifactPane()"),
            cls="right-header",
        ),
        Div(
            Div(
                Div("◈", cls="artifact-empty-icon"),
                P("Canvas renders here as agents produce them — company briefs, LBO models, comps tables, IC memo previews, RAG citations.",
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
