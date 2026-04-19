"""Marketing routes: /, /platform, /agents, /agents/<slug>, /how-it-works, /pricing, /contact."""

from __future__ import annotations

from fasthtml.common import (
    Div, H1, H2, H3, H4, P, Ul, Li, Section, Article, Span, A, Form, Input, Textarea, Label, Button, NotStr,
)

from app import rt
from agents.registry import AGENTS, AGENTS_BY_CATEGORY, AGENTS_BY_SLUG, CATEGORIES
from landing.components import (
    page, Hero, ProductTour, CategoryPillar, AgentCard, CategorySection, CaseStudyStrip, CTASection,
    Eyebrow, Heading, Body_, Button_, Pill, Section_, SITE_NAME, SITE_TAGLINE,
)


# ── / ────────────────────────────────────────────────────────────────
@rt("/")
def home():
    pillars = Section_(
        Div(
            Eyebrow("Five stages, one system"),
            Heading(2, "Every role your deal team plays — live inside PEHero.", cls="mt-3 max-w-4xl mb-10"),
            cls="mb-6",
        ),
        Div(
            *[CategoryPillar(c) for c in CATEGORIES],
            cls="grid md:grid-cols-2 lg:grid-cols-5 gap-4",
        ),
        cls="border-t border-line",
    )

    how = Section_(
        Div(
            Eyebrow("How it works"),
            Heading(2, "Source → Underwrite → Close → Hold.", cls="mt-3 max-w-3xl mb-10"),
            cls="mb-6",
        ),
        Div(
            *[Article(
                P(num, cls="font-mono text-[11px] tracking-widest uppercase text-ink-dim mb-3"),
                H3(title, cls="text-ink text-xl font-medium mb-3"),
                P(body, cls="text-ink-muted text-sm leading-relaxed"),
                cls="p-7 rounded-2xl bg-bg-elevated border border-line h-full",
            ) for (num, title, body) in [
                ("01", "Source deals that fit your mandate",
                 "Market Scanner watches PitchBook, Grata, banker feeds, and proprietary founder outreach. Deal Triage returns a go/no-go on each in under 90 seconds against your fund's criteria."),
                ("02", "Model them in hours, not weeks",
                 "Cap Table Parser, LTM Normalizer, and LBO Model Builder take seller financials into an IC-ready 5-year model with sensitivity and debt stack — already benchmarked against live transaction comps."),
                ("03", "Close, raise, and hold with conviction",
                 "IC Memo Writer, Teaser Designer, LP Update Generator, and Portfolio Ops agents keep every thesis, covenant, and KPI variance in view from signing through exit."),
            ]],
            cls="grid md:grid-cols-3 gap-4",
        ),
        cls="border-t border-line",
    )

    return page(
        "Agentic AI for private equity",
        Hero(),
        ProductTour(),
        pillars,
        how,
        CaseStudyStrip(),
        CTASection(),
        current_path="/",
    )


# ── /platform ────────────────────────────────────────────────────────
@rt("/platform")
def platform():
    return page(
        "Platform",
        Section_(
            Eyebrow("Platform"),
            Heading(1, "One system. Every stage. All your deal data.", cls="mt-4 max-w-4xl"),
            P(
                "PEHero lives where your deal team already works. Twenty-two specialist "
                "agents share a single model of your pipeline, your portfolio, and your market. "
                "Each agent has its own tools and prompts — and they pass artifacts between each "
                "other without the associate re-keying anything.",
                cls="mt-6 text-ink-muted text-lg max-w-3xl leading-relaxed",
            ),
            cls="border-t border-line",
        ),
        Section_(
            Div(
                *[Article(
                    Div(Span(c["icon"], cls="text-accent text-xl"),
                        Span(f"{len(AGENTS_BY_CATEGORY[c['key']])} agents",
                             cls="ml-auto font-mono text-[11px] tracking-widest uppercase text-ink-dim"),
                        cls="flex items-center mb-4"),
                    H3(c["name"], cls="text-ink text-xl font-medium mb-2"),
                    P(c["blurb"], cls="text-ink-muted leading-relaxed"),
                    cls="p-7 rounded-2xl bg-bg-elevated border border-line h-full",
                ) for c in CATEGORIES],
                cls="grid md:grid-cols-2 lg:grid-cols-5 gap-4",
            ),
            cls="border-t border-line",
        ),
        Section_(
            Eyebrow("Under the hood"),
            Heading(2, "Not a wrapper. A system.", cls="mt-3 max-w-3xl mb-10"),
            Div(
                *[Article(
                    P(k, cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
                    P(v, cls="text-ink leading-relaxed"),
                    cls="p-7 rounded-2xl bg-bg-elevated border border-line h-full",
                ) for (k, v) in [
                    ("Squad", "A full squad of specialist agents, one per role, sharing a common tool registry and prompt library."),
                    ("Tools", "70+ StructuredTools that read cap tables, financials, VDR PDFs, and sector comps directly — not through copy-paste."),
                    ("RAG", "Postgres + pgvector index of every CIM, QoE, MSA, legal DD memo, ESG assessment, and industry report in your deal."),
                    ("Memory", "Every conversation and every artifact persists, queryable across agents, so Week 3 of diligence still knows what Week 1 agreed."),
                ]],
                cls="grid md:grid-cols-2 lg:grid-cols-4 gap-4",
            ),
            cls="border-t border-line",
        ),
        CTASection(),
        current_path="/platform",
    )


# ── /agents ──────────────────────────────────────────────────────────
@rt("/agents")
def agents_page():
    return page(
        "Agents",
        Section_(
            Eyebrow("Your Private Equity AI Agent Squad"),
            Heading(1, "Every role already wired in.", cls="mt-4 max-w-4xl"),
            P(
                "Each agent has a narrow remit, deep tooling, and a prefix you can type in the chat "
                "to call it directly. Or just ask in plain English — the router picks the right one.",
                cls="mt-6 text-ink-muted text-lg max-w-3xl leading-relaxed",
            ),
            cls="border-t border-line",
        ),
        *[CategorySection(c) for c in CATEGORIES],
        CTASection(),
        current_path="/agents",
    )


# ── /agents/<slug> ───────────────────────────────────────────────────
@rt("/agents/{slug}")
def agent_detail(slug: str):
    agent = AGENTS_BY_SLUG.get(slug)
    if agent is None:
        return page(
            "Agent not found",
            Section_(
                H1("Not found", cls="text-ink text-3xl"),
                P("No agent at that URL. See the ", A("full squad", href="/agents", cls="text-accent underline"), ".",
                  cls="text-ink-muted mt-4"),
            ),
            current_path="/agents",
        )
    cat = next(c for c in CATEGORIES if c["key"] == agent.category)
    return page(
        f"{agent.name}",
        Section_(
            Div(
                A("← All agents", href="/agents", cls="text-ink-dim text-xs hover:text-accent"),
                cls="mb-6",
            ),
            Div(
                Span(agent.icon, cls="text-accent text-4xl"),
                Span(cat["name"], cls="ml-4 font-mono text-[11px] tracking-widest uppercase text-ink-dim"),
                cls="flex items-center mb-4",
            ),
            Heading(1, agent.name, cls="max-w-4xl"),
            P(agent.one_liner, cls="mt-5 text-ink-muted text-lg max-w-3xl"),
            Div(Pill(f"prefix: {agent.prefix}"),
                Pill(f"category: {cat['key']}"),
                cls="mt-6 flex flex-wrap gap-2"),
            cls="border-t border-line",
        ),
        Section_(
            Div(
                Div(
                    Eyebrow("What it does"),
                    P(agent.description, cls="mt-4 text-ink leading-relaxed"),
                    cls="md:col-span-2",
                ),
                Div(
                    Eyebrow("Example prompts"),
                    Ul(
                        *[Li(
                            Div(f'"{p}"', cls="px-4 py-3 rounded-xl bg-bg-elevated border border-line text-sm text-ink leading-relaxed"),
                            cls="mb-2",
                        ) for p in agent.example_prompts],
                        cls="mt-4 space-y-2",
                    ),
                    cls="",
                ),
                cls="grid md:grid-cols-3 gap-10",
            ),
            cls="border-t border-line",
        ),
        CTASection(headline=f"Try {agent.name} now.",
                   body="BYOD — bring your own deal data and try the example prompt above against it.",
                   cta_label="Open the app", cta_href="/app"),
        current_path="/agents",
    )


# ── /how-it-works ────────────────────────────────────────────────────
@rt("/how-it-works")
def how_it_works():
    return page(
        "How it works",
        Section_(
            Eyebrow("How it works"),
            Heading(1, "From teaser to signed SPA — in one system.", cls="mt-4 max-w-4xl"),
            cls="border-t border-line",
        ),
        *[Section_(
            Div(
                Span(num, cls="font-mono text-[11px] tracking-widest uppercase text-ink-dim"),
                Heading(2, title, cls="mt-3 max-w-3xl"),
                P(body, cls="mt-5 text-ink-muted text-lg max-w-3xl leading-relaxed"),
                cls="mb-8",
            ),
            Div(*[Pill(name) for name in agents], cls="flex flex-wrap gap-2"),
            cls="border-t border-line",
        ) for (num, title, body, agents) in [
            ("01 — Source",
             "Surface the right deals faster than the next MD.",
             "Market Scanner watches PitchBook, Grata, banker feeds, and off-market founder-intent signals. Deal Triage returns a go/no-go in under 90 seconds. Transaction Comps tightens multiple benchmarks before you sign an NDA.",
             ["Market Scanner", "Deal Triage", "Transaction Comps", "Owner Intent"]),
            ("02 — Underwrite",
             "Seller financials to IC-ready LBO in under an hour.",
             "Cap Table Parser and LTM Normalizer ingest whatever format the banker sends. LBO Model Builder produces a 5-year model with sensitivity. Debt Stack Modeler sizes the capital structure. Return Metrics outputs IRR, MOIC, and the value-creation bridge.",
             ["Cap Table Parser", "LTM Normalizer", "LBO Model Builder", "Debt Stack Modeler", "Return Metrics"]),
            ("03 — Diligence",
             "No surprises at signing.",
             "VDR Auditor checks the seller data room against a 140-item PE checklist. Contract Abstractor reads every MSA. Legal & Regulatory, Operational Diligence, and ESG agents flag material issues with page-level citations.",
             ["VDR Auditor", "Contract Abstractor", "Legal & Regulatory", "Operational Diligence", "ESG Risk"]),
            ("04 — Raise",
             "LP material your chair will actually sign.",
             "IC Memo Writer drafts the investment-committee memo from your own data. Teaser Designer produces a 2-page blind teaser for co-invest distribution. LP Update Generator writes the quarterly letter. Fundraising CRM Copilot ranks prospects and drafts outreach.",
             ["IC Memo Writer", "Teaser Designer", "LP Update Generator", "Fundraising CRM Copilot"]),
            ("05 — Hold & Grow",
             "Post-close, the agents stay on.",
             "Pricing Optimization recommends increases at renewal. EBITDA Variance Watcher flags monthly drift. Value Creation Prioritizer ranks VCP initiatives by ROI. Customer Churn Predictor scores renewal risk across the ARR base.",
             ["Pricing Optimization", "EBITDA Variance Watcher", "Value Creation Prioritizer", "Customer Churn Predictor"]),
        ]],
        CTASection(),
        current_path="/how-it-works",
    )


# ── /pricing ─────────────────────────────────────────────────────────
@rt("/pricing")
def pricing():
    tiers = [
        {
            "name": "Pilot",
            "price": "BYOD",
            "sub": "bring your own data · 30-day pilot",
            "blurb": "One associate, one deal, the full squad — running against your own data.",
            "features": [
                "Full squad of specialists",
                "1 concurrent user",
                "Up to 5 live deals",
                "BYOD — connect your deal data on day one",
                "Email support",
            ],
            "cta": ("Start pilot", "/contact"),
            "primary": False,
        },
        {
            "name": "Team",
            "price": "Contact us",
            "sub": "per fund",
            "blurb": "Fund actively deploying capital with 5-25 investment professionals.",
            "features": [
                "Full squad of specialists",
                "Up to 25 seats",
                "Unlimited deals + portcos",
                "SSO + audit log",
                "Shared memory across team",
                "Priority support",
            ],
            "cta": ("Book a demo", "/contact"),
            "primary": True,
        },
        {
            "name": "Platform",
            "price": "Custom",
            "sub": "for multi-fund GPs",
            "blurb": "Dedicated cluster, your brand, custom agents.",
            "features": [
                "Everything in Team",
                "Unlimited seats",
                "Dedicated instance",
                "Bring your own LLM provider",
                "Custom agents and tools",
                "Onsite training",
            ],
            "cta": ("Contact sales", "/contact"),
            "primary": False,
        },
    ]
    return page(
        "Pricing",
        Section_(
            Eyebrow("Pricing"),
            Heading(1, "BYOD — bring your own data. Upgrade when it sticks.", cls="mt-4 max-w-4xl"),
            P("No setup fee. No per-seat tax. No prompt-token surprise.",
              cls="mt-6 text-ink-muted text-lg max-w-3xl leading-relaxed"),
            cls="border-t border-line",
        ),
        Section_(
            Div(
                *[Article(
                    P(t["name"], cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
                    Div(
                        Span(t["price"], cls="text-4xl md:text-5xl font-medium tracking-tighter text-ink"),
                        Span(f" {t['sub']}", cls="text-ink-muted text-sm ml-2"),
                        cls="mb-4",
                    ),
                    P(t["blurb"], cls="text-ink-muted leading-relaxed mb-6"),
                    Ul(
                        *[Li(
                            Span("✓ ", cls="text-accent mr-2"),
                            Span(f, cls="text-ink text-sm"),
                            cls="mb-2 flex items-baseline",
                        ) for f in t["features"]],
                        cls="mb-8 space-y-1",
                    ),
                    Button_(t["cta"][0], href=t["cta"][1], primary=t["primary"]),
                    cls=("p-8 rounded-2xl bg-bg-elevated h-full flex flex-col " +
                         ("border border-accent/60" if t["primary"] else "border border-line")),
                ) for t in tiers],
                cls="grid md:grid-cols-3 gap-4",
            ),
            cls="border-t border-line",
        ),
        CTASection(),
        current_path="/pricing",
    )


# ── /contact ─────────────────────────────────────────────────────────
@rt("/contact")
def contact(sent: bool = False):
    form = Form(
        Div(
            Label("Your name", cls="block text-xs font-mono tracking-widest uppercase text-ink-dim mb-2"),
            Input(name="name", type="text", required=True,
                  cls="w-full px-4 py-3 rounded-xl bg-bg-elevated border border-line text-ink focus:border-accent focus:outline-none"),
            cls="mb-5",
        ),
        Div(
            Label("Email", cls="block text-xs font-mono tracking-widest uppercase text-ink-dim mb-2"),
            Input(name="email", type="email", required=True,
                  cls="w-full px-4 py-3 rounded-xl bg-bg-elevated border border-line text-ink focus:border-accent focus:outline-none"),
            cls="mb-5",
        ),
        Div(
            Label("Firm (optional)", cls="block text-xs font-mono tracking-widest uppercase text-ink-dim mb-2"),
            Input(name="firm", type="text",
                  cls="w-full px-4 py-3 rounded-xl bg-bg-elevated border border-line text-ink focus:border-accent focus:outline-none"),
            cls="mb-5",
        ),
        Div(
            Label("Tell us about your pipeline", cls="block text-xs font-mono tracking-widest uppercase text-ink-dim mb-2"),
            Textarea(name="message", rows="5", required=True,
                     cls="w-full px-4 py-3 rounded-xl bg-bg-elevated border border-line text-ink focus:border-accent focus:outline-none"),
            cls="mb-8",
        ),
        Button("Send message →", type="submit",
               cls="inline-flex items-center gap-2 px-5 py-3 rounded-full text-sm font-medium bg-accent text-bg hover:bg-ink transition-all"),
        method="post",
        action="/contact",
    )

    success = Div(
        Div(
            Span("✓", cls="text-accent text-2xl"),
            cls="mb-4",
        ),
        H3("Thanks — we'll be in touch shortly.", cls="text-ink text-xl mb-2"),
        P("Usually within one business day.", cls="text-ink-muted"),
        cls="p-8 rounded-2xl bg-bg-elevated border border-line",
    )

    return page(
        "Contact",
        Section_(
            Eyebrow("Contact"),
            Heading(1, "Let's look at one of your deals.", cls="mt-4 max-w-4xl"),
            P("Send us a note and we'll set up a 20-minute walkthrough. We'll load one of your "
              "recent deals into PEHero and show you the full agent flow — live.",
              cls="mt-6 text-ink-muted text-lg max-w-3xl leading-relaxed"),
            Div(
                success if sent else form,
                cls="mt-12 max-w-xl",
            ),
            cls="border-t border-line",
        ),
        current_path="/contact",
    )


@rt("/contact", methods=["POST"])
def contact_post(name: str = "", email: str = "", firm: str = "", message: str = ""):
    import logging
    logging.getLogger(__name__).info("contact form submitted: %s (%s) %s chars",
                                     name, email, len(message or ""))
    return page(
        "Thanks",
        Section_(
            Eyebrow("Contact"),
            Heading(1, "Thanks — we'll be in touch shortly.", cls="mt-4 max-w-4xl"),
            P("Usually within one business day. In the meantime, ",
              A("open the app", href="/app", cls="text-accent underline"),
              " — BYOD: connect your deal data to see the squad on real work.",
              cls="mt-6 text-ink-muted text-lg max-w-3xl leading-relaxed"),
            cls="border-t border-line",
        ),
        current_path="/contact",
    )
