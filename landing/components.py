"""Landing-page components — PE repositioning of the predictivelabsai-landing kit.

Lighter, slightly warmer palette than Bricksmith: off-white parchment background
with a slate/forest-green accent that plays to PE's "institutional but modern"
feel. All pages share the `page()` wrapper below.
"""

from __future__ import annotations

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Nav, Main, Footer, Section, Article, Div, Span, A, Img,
    H1, H2, H3, H4, P, Ul, Li, Button, Form, Input, Textarea, Label,
)

from agents.registry import CATEGORIES, AGENTS, AGENTS_BY_CATEGORY

SITE_NAME = "PEHero"
SITE_TAGLINE = "Agentic AI for private equity deal teams."
CONTACT_EMAIL = "hello@pehero.fyi"
GITHUB_URL = "https://github.com/predictivelabsai/pehero"
LINKEDIN_URL = "https://www.linkedin.com/company/predictive-labs-ltd/"

NAV_ITEMS = [
    ("Platform", "/platform"),
    ("Agents", "/agents"),
    ("How it works", "/how-it-works"),
    ("Pricing", "/pricing"),
    ("Contact", "/contact"),
]

# Lighter parchment background with a deep-forest / slate accent.
# Distinct from Bricksmith's dark-navy + amber but keeps a similar cadence.
TAILWIND_CONFIG = """
tailwind.config = {
  theme: {
    extend: {
      colors: {
        bg:     { DEFAULT: '#F7F6F1', elevated: '#FFFFFF', raised: '#EFEDE4' },
        ink:    { DEFAULT: '#14231B', muted: '#415046', dim: '#7A867E' },
        line:   { DEFAULT: '#E3DFD2', bright: '#CFC8B4' },
        accent: { DEFAULT: '#1F5D43', dim: '#CFE5DA', deep: '#0F3226' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      letterSpacing: { tightest: '-0.04em', tighter: '-0.025em' },
    },
  },
};
"""


def Eyebrow(text: str, *, cls: str = ""):
    return Span(text, cls=f"font-mono text-[11px] tracking-[0.18em] uppercase text-accent {cls}".strip())


def Heading(level: int, text, *, cls: str = ""):
    tag = {1: H1, 2: H2, 3: H3, 4: H4}[level]
    base = {
        1: "text-4xl sm:text-5xl md:text-7xl font-medium tracking-tightest text-ink leading-[1.05] md:leading-[1.02]",
        2: "text-2xl sm:text-3xl md:text-5xl font-medium tracking-tighter text-ink leading-[1.12] md:leading-[1.08]",
        3: "text-lg sm:text-xl md:text-2xl font-medium tracking-tight text-ink",
        4: "text-base md:text-lg font-medium text-ink",
    }[level]
    return tag(text if not isinstance(text, tuple) else Span(*text), cls=f"{base} {cls}".strip())


def Body_(text, *, cls: str = "", muted: bool = True):
    tone = "text-ink-muted" if muted else "text-ink"
    return P(text, cls=f"text-base md:text-lg leading-relaxed {tone} {cls}".strip())


def Button_(text: str, *, href: str = "#", primary: bool = True, cls: str = ""):
    base = "inline-flex items-center gap-2 px-5 py-3 rounded-full text-sm font-medium transition-all duration-200"
    if primary:
        style = "bg-accent text-bg hover:bg-ink shadow-[0_0_0_1px_#1F5D43] hover:shadow-[0_0_0_1px_#14231B]"
    else:
        style = "bg-transparent text-ink border border-line-bright hover:border-accent hover:text-accent"
    return A(text, Span("→", cls="text-base"), href=href, cls=f"{base} {style} {cls}".strip())


def Pill(text: str, *, cls: str = ""):
    return Span(
        text,
        cls=f"inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono tracking-wider uppercase text-ink-muted bg-bg-elevated border border-line {cls}".strip(),
    )


def _navbar(current_path: str = "/"):
    items = [
        Li(A(label, href=href,
             cls=f"text-sm text-ink-muted hover:text-ink transition-colors {'text-ink' if current_path == href or current_path.startswith(href + '/') else ''}"))
        for label, href in NAV_ITEMS
    ]
    return Nav(
        Div(
            A(
                Span("◆", cls="text-accent mr-2"),
                Span(SITE_NAME, cls="font-medium tracking-tight"),
                href="/",
                cls="flex items-center text-ink text-base hover:text-accent transition-colors",
            ),
            Ul(*items, cls="hidden lg:flex items-center gap-7"),
            Div(
                A("Book a demo", href="/contact",
                  cls="hidden lg:inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium text-ink border border-line-bright hover:border-accent hover:text-accent transition-colors"),
                A("Open app", href="/app",
                  cls="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium bg-accent text-bg hover:bg-ink transition-colors"),
                cls="flex items-center gap-3",
            ),
            cls="max-w-7xl mx-auto px-5 md:px-6 flex items-center justify-between h-16 gap-4",
        ),
        cls="sticky top-0 z-50 backdrop-blur-md bg-bg/80 border-b border-line",
    )


def _footer():
    return Footer(
        Div(
            Div(
                Div(
                    A(Span("◆", cls="text-accent mr-2"), Span(SITE_NAME, cls="font-medium text-ink"),
                      href="/", cls="flex items-center text-lg mb-4"),
                    P(SITE_TAGLINE, cls="text-ink-muted text-sm max-w-xs mb-5"),
                    P("Built by a small team that's sourced, underwritten, and held the phone at 2 AM the night before IC.",
                      cls="text-ink-dim text-xs leading-relaxed max-w-xs"),
                ),
                Div(
                    H4("Product", cls="text-xs font-mono tracking-[0.18em] uppercase text-ink-muted mb-5"),
                    Ul(
                        Li(A("Platform", href="/platform", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("Agents", href="/agents", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("How it works", href="/how-it-works", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("Pricing", href="/pricing", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("Open the app", href="/app", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                    ),
                ),
                Div(
                    H4("Company", cls="text-xs font-mono tracking-[0.18em] uppercase text-ink-muted mb-5"),
                    Ul(
                        Li(A("Contact", href="/contact", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("GitHub", href=GITHUB_URL, cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("LinkedIn", href=LINKEDIN_URL, cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                    ),
                ),
                cls="grid grid-cols-2 md:grid-cols-3 gap-10",
            ),
            Div(
                Div(f"© {__import__('datetime').datetime.now().year} PEHero · Predictive Labs Ltd.",
                    cls="text-ink-dim text-xs"),
                A(CONTACT_EMAIL, href=f"mailto:{CONTACT_EMAIL}",
                  cls="text-ink-dim text-xs hover:text-accent"),
                cls="mt-10 md:mt-14 pt-6 border-t border-line flex items-start md:items-center justify-between flex-wrap gap-4",
            ),
            cls="max-w-7xl mx-auto px-5 md:px-6",
        ),
        cls="py-12 md:py-16 border-t border-line bg-bg-elevated",
    )


def page(title: str, *content, current_path: str = "/", head_extra=None):
    head_children = [
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="description", content=f"{SITE_NAME} — {SITE_TAGLINE}"),
        Title(f"{title} · {SITE_NAME}"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap",
        ),
        Script(src="https://cdn.tailwindcss.com"),
        Script(NotStr(TAILWIND_CONFIG)),
        Link(rel="stylesheet", href="/static/site.css"),
    ]
    if head_extra:
        head_children.extend(head_extra if isinstance(head_extra, list) else [head_extra])

    return Html(
        Head(*head_children),
        Body(
            _navbar(current_path),
            Main(*content, cls="min-h-screen"),
            _footer(),
            cls="bg-bg text-ink font-sans antialiased",
        ),
        lang="en",
    )


# ─── Higher-level blocks ───────────────────────────────────────────────

def Section_(*content, bleed: bool = False, cls: str = ""):
    inner_cls = "max-w-7xl mx-auto px-5 md:px-6" if not bleed else "w-full"
    return Section(Div(*content, cls=inner_cls), cls=f"py-14 md:py-20 lg:py-24 {cls}".strip())


def Hero():
    headline = (
        Span("22 specialist agents "),
        Span("sourcing, ", cls="text-accent"),
        Span("underwriting, "),
        Span("and closing ", cls="text-accent"),
        Span("your next platform."),
    )
    lede = (
        "Not a prompt pack. Not a build-it-yourself kit. PEHero is a full agentic system "
        "already wired into your deal flow — scanning targets, running QoE, building LBO "
        "models, and drafting IC memos while your team focuses on the call."
    )
    return Section(
        Div(
            Div(id="hero-grid", cls="absolute inset-0 z-10 opacity-40 pointer-events-none"),
            Div(cls="absolute inset-0 z-20 bg-gradient-to-b from-bg/40 via-transparent to-bg pointer-events-none"),
            Div(
                Eyebrow("Agentic AI for private equity"),
                H1(*headline,
                   cls="mt-5 md:mt-6 text-[40px] sm:text-5xl md:text-7xl lg:text-[84px] font-medium tracking-tightest text-ink leading-[1.05] md:leading-[1.02] max-w-5xl"),
                P(lede, cls="mt-6 md:mt-8 text-base md:text-xl text-ink-muted max-w-2xl leading-relaxed"),
                Div(
                    Button_("Open the app", href="/app", primary=True),
                    Button_("Meet the 22 agents", href="/agents", primary=False),
                    cls="mt-8 md:mt-10 flex items-center gap-3 flex-wrap",
                ),
                cls="relative z-30 max-w-7xl mx-auto px-5 md:px-6 py-24 md:py-0",
            ),
            cls="relative min-h-[80vh] md:min-h-[86vh] flex items-center overflow-hidden bg-bg",
        ),
        Div(
            Div(
                _StatCell("22", "specialist agents"),
                _StatCell("5", "workflow stages, end-to-end"),
                _StatCell("<90s", "to a go / no-go decision"),
                _StatCell("$0", "to try with synthetic data"),
                cls="max-w-7xl mx-auto px-5 md:px-6 py-5 md:py-6 grid grid-cols-2 md:grid-cols-4 gap-6",
            ),
            cls="border-y border-line bg-bg-elevated/60",
        ),
    )


def ProductTour():
    """Rotating GIF preview + CTA into the app / README / PDF tour."""
    return Section(
        Div(
            Div(
                Eyebrow("Product tour"),
                Heading(2, "See it in motion.", cls="mt-3 max-w-3xl mb-2"),
                P("A 30-second walk through chat, the pipeline kanban, deal detail, "
                  "analytics and prompt editing — captured from the running app against "
                  "synthetic PE data.",
                  cls="mt-2 text-ink-muted text-base max-w-2xl leading-relaxed mb-6"),
                cls="mb-6",
            ),
            A(
                Img(src="/docs/pehero.gif",
                    alt="PEHero product tour — chat, pipeline, analytics",
                    cls="block w-full h-auto rounded-2xl border border-line shadow-[0_8px_40px_rgba(0,0,0,0.06)]",
                    loading="lazy"),
                href="https://github.com/predictivelabsai/pehero#readme",
                target="_blank", rel="noopener",
                cls="block rounded-2xl overflow-hidden hover:opacity-95 transition-opacity",
                title="Open the README",
            ),
            Div(
                A(Span("View README"), Span("→", cls="ml-1"),
                  href="https://github.com/predictivelabsai/pehero#readme",
                  target="_blank", rel="noopener",
                  cls="inline-flex items-center gap-2 text-sm text-accent hover:text-ink"),
                Span("·", cls="text-ink-dim mx-3"),
                A(Span("Download product tour (PDF)"), Span("↓", cls="ml-1"),
                  href="/docs/pehero-product-tour.pdf",
                  cls="inline-flex items-center gap-2 text-sm text-accent hover:text-ink"),
                Span("·", cls="text-ink-dim mx-3"),
                A(Span("Open the app"), Span("→", cls="ml-1"),
                  href="/app",
                  cls="inline-flex items-center gap-2 text-sm text-ink hover:text-accent"),
                cls="mt-5 flex items-center flex-wrap gap-y-2",
            ),
            cls="max-w-7xl mx-auto px-5 md:px-6 py-14 md:py-20 border-t border-line",
        ),
    )


def _StatCell(value: str, caption: str):
    return Div(
        Span(value, cls="text-2xl md:text-3xl font-medium tracking-tighter text-ink"),
        P(caption, cls="text-ink-muted text-xs md:text-sm mt-1"),
    )


def CategoryPillar(cat: dict, *, sample_count: int = 4):
    agents_in_cat = AGENTS_BY_CATEGORY.get(cat["key"], [])
    sample = agents_in_cat[:sample_count]
    total = len(agents_in_cat)
    return Article(
        Div(
            Span(cat["icon"], cls="text-accent text-2xl"),
            Span(f"{total} agents", cls="ml-auto font-mono text-[11px] tracking-widest uppercase text-ink-dim"),
            cls="flex items-center mb-5",
        ),
        Heading(3, cat["name"], cls="mb-2"),
        P(cat["blurb"], cls="text-ink-muted text-sm leading-relaxed mb-5"),
        Ul(
            *[Li(
                Div(
                    Span("•", cls="text-accent mr-2"),
                    Span(a.name, cls="text-ink text-sm"),
                    cls="flex items-baseline",
                ),
                cls="mb-1.5",
            ) for a in sample],
            cls="space-y-1",
        ),
        A(f"See all {total} → ", href=f"/agents#{cat['key']}", cls="text-accent text-xs font-mono tracking-wider uppercase hover:text-ink mt-6 inline-block"),
        cls="p-7 rounded-2xl bg-bg-elevated border border-line hover:border-accent/50 transition-colors group h-full flex flex-col",
    )


def AgentCard(agent, *, as_link: bool = True):
    inner = Article(
        Div(
            Span(agent.icon, cls="text-accent text-xl"),
            Span(agent.prefix, cls="ml-auto font-mono text-[11px] tracking-widest uppercase text-ink-dim"),
            cls="flex items-center mb-4",
        ),
        H4(agent.name, cls="text-ink font-medium mb-1.5"),
        P(agent.one_liner, cls="text-ink-muted text-sm leading-relaxed"),
        cls="p-6 rounded-2xl bg-bg-elevated border border-line hover:border-accent/50 transition-colors h-full",
    )
    if as_link:
        return A(inner, href=f"/agents/{agent.slug}", cls="block h-full")
    return inner


def CategorySection(cat: dict):
    agents_in_cat = AGENTS_BY_CATEGORY.get(cat["key"], [])
    return Section(
        Div(id=cat["key"]),
        Div(
            Div(
                Eyebrow(cat["name"]),
                Heading(2, cat["blurb"], cls="mt-3 max-w-3xl"),
                cls="mb-10",
            ),
            Div(
                *[AgentCard(a) for a in agents_in_cat],
                cls="grid sm:grid-cols-2 lg:grid-cols-3 gap-4",
            ),
            cls="max-w-7xl mx-auto px-5 md:px-6",
        ),
        cls="py-14 md:py-20 border-t border-line",
    )


def CaseStudyStrip():
    cases = [
        {"label": "Sourcing → triage", "metric": "1,240 deals", "caption": "surfaced and triaged against a lower-middle-market software mandate in one week of scanning."},
        {"label": "Underwriting", "metric": "3 days → 40 min", "caption": "from seller financials + cap table to a full 5-year LBO model with sensitivity and debt stack."},
        {"label": "Capital", "metric": "60 LPs, ranked", "caption": "by fund-fit, staleness, and commitment size — with drafted re-engagement emails."},
    ]
    return Section_(
        Eyebrow("What you get"),
        Heading(2, "Time compressed, confidence higher.", cls="mt-3 max-w-3xl mb-10"),
        Div(
            *[Article(
                P(c["label"], cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
                P(c["metric"], cls="text-3xl md:text-4xl font-medium tracking-tighter text-ink mb-3"),
                P(c["caption"], cls="text-ink-muted text-sm leading-relaxed"),
                cls="p-7 rounded-2xl bg-bg-elevated border border-line",
            ) for c in cases],
            cls="grid md:grid-cols-3 gap-4",
        ),
        cls="border-t border-line",
    )


def CTASection(*, headline: str = "Stop stitching tools. Start closing deals.",
               body: str = "Book a 20-minute walkthrough. We'll load one of your recent deals into PEHero and show you the full agent flow end-to-end.",
               cta_label: str = "Book a demo", cta_href: str = "/contact"):
    return Section(
        Div(
            Div(
                Eyebrow("Talk to us"),
                Heading(2, headline, cls="mt-3 max-w-3xl"),
                P(body, cls="mt-5 text-ink-muted text-lg max-w-2xl leading-relaxed"),
                Div(
                    Button_(cta_label, href=cta_href, primary=True),
                    Button_("Try with synthetic data", href="/app", primary=False),
                    cls="mt-8 flex items-center gap-3 flex-wrap",
                ),
                cls="max-w-7xl mx-auto px-5 md:px-6 py-20 md:py-28 relative z-10",
            ),
            Div(cls="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-transparent pointer-events-none"),
            cls="relative border-y border-line bg-bg-elevated/60 overflow-hidden",
        ),
    )
