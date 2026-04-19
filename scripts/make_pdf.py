"""Generate a PEHero product tour PDF from the demo screenshots.

Output: docs/pehero-product-tour.pdf

Slide-deck format (landscape, 16:9). App-focused — spends one slide per
product surface (chat, pipeline kanban, deal detail, analytics,
instructions) and keeps landing pages in an appendix.

Usage:
    python -m scripts.make_pdf
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image as RLImage, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, KeepTogether,
)


ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
OUT = ROOT / "docs" / "pehero-product-tour.pdf"

# 16:9 slide — 33.87 × 19.05 cm (standard PowerPoint 16:9)
SLIDE = (33.87 * cm, 19.05 * cm)

# Palette matches the app (light parchment + forest green).
BG         = HexColor("#F7F6F1")
INK        = HexColor("#14231B")
INK_MUTED  = HexColor("#415046")
INK_DIM    = HexColor("#7A867E")
ACCENT     = HexColor("#1F5D43")
ACCENT_DIM = HexColor("#CFE5DA")
RULE       = HexColor("#E3DFD2")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "hero":     ParagraphStyle("hero",     parent=ss["Title"], fontName="Helvetica-Bold",
                                   fontSize=42, leading=50, textColor=INK, alignment=TA_CENTER,
                                   spaceAfter=10),
        "hero_sub": ParagraphStyle("hero_sub", parent=ss["Normal"], fontName="Helvetica",
                                   fontSize=16, leading=22, textColor=INK_MUTED, alignment=TA_CENTER,
                                   spaceAfter=16),
        "eyebrow":  ParagraphStyle("eyebrow",  parent=ss["Normal"], fontName="Helvetica-Bold",
                                   fontSize=10, leading=12, textColor=ACCENT, spaceAfter=4,
                                   letterSpacing=1.2),
        "title":    ParagraphStyle("title",    parent=ss["Title"], fontName="Helvetica-Bold",
                                   fontSize=28, leading=34, textColor=INK, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=ss["Normal"], fontName="Helvetica",
                                   fontSize=13, leading=18, textColor=INK_MUTED, spaceAfter=14),
        "body":     ParagraphStyle("body",     parent=ss["BodyText"], fontName="Helvetica",
                                   fontSize=11, leading=15, textColor=INK, alignment=TA_LEFT,
                                   spaceAfter=4),
        "caption":  ParagraphStyle("caption",  parent=ss["Italic"], fontName="Helvetica-Oblique",
                                   fontSize=9, leading=11, textColor=INK_DIM, alignment=TA_CENTER,
                                   spaceBefore=2),
        "bullet":   ParagraphStyle("bullet",   parent=ss["BodyText"], fontName="Helvetica",
                                   fontSize=11, leading=15, textColor=INK, leftIndent=12,
                                   bulletIndent=0),
    }


def _fit_image(path: Path, max_w_mm: float, max_h_mm: float) -> RLImage:
    img = Image.open(path)
    w, h = img.size
    ratio = min(max_w_mm * mm / w, max_h_mm * mm / h)
    return RLImage(str(path), width=w * ratio, height=h * ratio)


def _footer(canvas, doc):
    canvas.saveState()
    # Slide background
    canvas.setFillColor(BG)
    canvas.rect(0, 0, SLIDE[0], SLIDE[1], fill=1, stroke=0)
    # Thin footer line + page number
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(1.5 * cm, 1 * cm, SLIDE[0] - 1.5 * cm, 1 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(INK_DIM)
    canvas.drawString(1.5 * cm, 0.55 * cm, "PEHero · agentic AI for private equity")
    canvas.drawRightString(SLIDE[0] - 1.5 * cm, 0.55 * cm, f"{doc.page}")
    canvas.restoreState()


def _slide_frame(doc):
    return Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height,
        id="main",
        leftPadding=6, rightPadding=6,
        topPadding=0, bottomPadding=0,
    )


def _hero_slide(styles):
    return [
        Spacer(1, 40 * mm),
        Paragraph("PEHero", styles["hero"]),
        Paragraph("Agentic AI for private equity deal teams.", styles["hero_sub"]),
        Paragraph("22 specialist agents · pipeline kanban · LBO modeling · text-to-SQL analytics",
                  styles["hero_sub"]),
        PageBreak(),
    ]


def _slide(styles, *, eyebrow: str, title: str, subtitle: str,
           bullets: list[str], screenshot: str, caption: str = None) -> list:
    """A two-column slide: left = text, right = screenshot.

    Using a Table so left/right stay aligned horizontally (Platypus doesn't
    otherwise support columns in a Frame cleanly).
    """
    left_cell = [
        Paragraph(eyebrow.upper(), styles["eyebrow"]),
        Paragraph(title, styles["title"]),
        Paragraph(subtitle, styles["subtitle"]),
    ]
    for b in bullets:
        left_cell.append(Paragraph(f"• {b}", styles["bullet"]))

    shot_path = SHOTS / screenshot
    if shot_path.exists():
        img = _fit_image(shot_path, max_w_mm=170, max_h_mm=135)
        right_cell = [img]
        if caption:
            right_cell.append(Paragraph(caption, styles["caption"]))
    else:
        right_cell = [Paragraph(f"[missing {screenshot}]", styles["caption"])]

    t = Table(
        [[left_cell, right_cell]],
        colWidths=[120 * mm, 180 * mm],
    )
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [Spacer(1, 3 * mm), t, PageBreak()]


def _agenda_slide(styles):
    rows = [
        ["01", "Chat — 22 agents, SSE streaming, artifact side pane",
         "triage, LBO, IC memo, VDR audit"],
        ["02", "Pipeline — kanban across 10 deal stages",
         "sector + ownership filters, click into deal"],
        ["03", "Deal detail — brief on the right, chat in the centre",
         "LTM, top customers, DD findings, LBO"],
        ["04", "Analytics — text → SQL → Plotly chart",
         "sector multiples, stage counts, LP mix"],
        ["05", "Instructions — edit the 22 agent prompts",
         "saves to prompts/system/*.md, hot-reloads"],
        ["06", "Extensions — web search + Baltic registries",
         "Tavily/EXA · LT, LV, EE business registries"],
    ]
    t = Table(rows, colWidths=[20 * mm, 130 * mm, 150 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 12),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 14),
        ("FONT", (1, 0), (1, -1), "Helvetica-Bold", 12),
        ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("TEXTCOLOR", (2, 0), (2, -1), INK_MUTED),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, RULE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return [
        Spacer(1, 8 * mm),
        Paragraph("TOUR".upper(), styles["eyebrow"]),
        Paragraph("What you'll see", styles["title"]),
        Paragraph("Six product surfaces, in order of a deal's life.", styles["subtitle"]),
        Spacer(1, 6 * mm),
        t,
        PageBreak(),
    ]


def _closing_slide(styles):
    return [
        Spacer(1, 25 * mm),
        Paragraph("Get PEHero running in 5 minutes".upper(), styles["eyebrow"]),
        Paragraph("Local install", styles["title"]),
        Spacer(1, 4 * mm),
        Paragraph(
            "<font face='Courier' size='11'>"
            "git clone &lt;repo&gt; pehero &amp;&amp; cd pehero<br/>"
            "cp .env.example .env       # fill DB_URL + XAI_API_KEY<br/>"
            "pip install -r requirements.txt<br/>"
            "python -m db.migrate<br/>"
            "python -m synthetic.generate --seed 42<br/>"
            "python main.py             # → http://localhost:5058"
            "</font>",
            styles["body"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Deploy to Coolify (pehero.fyi)", styles["title"]),
        Paragraph(
            "Coolify picks up docker-compose.yaml; set DB_URL and XAI_API_KEY and attach the "
            "pehero.fyi domain. Seeding synthetic data is one docker compose exec away.",
            styles["body"],
        ),
        Spacer(1, 8 * mm),
        Paragraph(
            "All screenshots rendered against synthetic PE data — 40 companies, 960 months "
            "of financials, 480 comps, 725 contracts, 60 LPs, 345 documents indexed in pgvector.",
            styles["caption"],
        ),
        PageBreak(),
    ]


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()

    doc = BaseDocTemplate(
        str(OUT), pagesize=SLIDE,
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
        topMargin=1 * cm, bottomMargin=1.5 * cm,
        title="PEHero — Product Tour",
        author="Predictive Labs",
    )
    doc.addPageTemplates([PageTemplate(id="slide", frames=[_slide_frame(doc)], onPage=_footer)])

    story: list = []
    story += _hero_slide(styles)
    story += _agenda_slide(styles)

    # ── Chat product (the main show) ──────────────────────────────
    story += _slide(
        styles,
        eyebrow="01 · Chat",
        title="One chat, 22 specialists",
        subtitle="Type a prefix or plain English — the router picks the right agent.",
        bullets=[
            "Left nav: sessions, the 22 agents by category, Pipeline / Instructions / Analytics links.",
            "Centre: the transcript. Gemini-style contextual sample cards under the input.",
            "Right: the artifact pane — tables, citations, memo previews stream in.",
            "SSE streams tokens + tool calls with a live thinking indicator.",
        ],
        screenshot="07-chat-empty.png",
        caption="Empty chat + contextual sample cards",
    )
    story += _slide(
        styles,
        eyebrow="01 · Chat",
        title="Deal Triage — go / no-go in 90 seconds",
        subtitle="Prefix routing → triage: … returns a 3-bullet decision.",
        bullets=[
            "`triage:` prefix goes straight to the Deal Triage Agent.",
            "Calls search_companies, find_transaction_comps, fetch_market_signals.",
            "Returns verdict, 3-bullet rationale, and a concrete next step.",
            "'Next step — X' pattern surfaces a follow-up button to continue.",
        ],
        screenshot="08-chat-triage.png",
        caption="Live triage on synthetic vertical-SaaS target",
    )
    story += _slide(
        styles,
        eyebrow="01 · Chat",
        title="LBO Model Builder",
        subtitle="5-year model + sensitivity from one sentence of assumptions.",
        bullets=[
            "Normalizes LTM financials with QoE add-backs.",
            "Projects revenue, margin, capex, interest, FCF, debt paydown.",
            "Writes the run to pehero.lbo_models — Return Metrics reads it back.",
            "Artifact: year-by-year table with MOIC + levered IRR.",
        ],
        screenshot="09-chat-lbo.png",
        caption="LBO built from a plain-English prompt",
    )
    story += _slide(
        styles,
        eyebrow="01 · Chat",
        title="IC Memo Writer",
        subtitle="Exec-ready memo straight from the deal's own data.",
        bullets=[
            "Pulls deal brief, LTM, LBO, debt stack, comps, DD findings.",
            "Drafts full sections: Thesis, Market, Financials, VCP, Risks, Recommendation.",
            "Every quantitative claim cites a tool call — no fabrication.",
            "IC-length by default; configurable to a 1-page summary.",
        ],
        screenshot="10-chat-memo.png",
        caption="IC memo generated from synthetic data",
    )

    # ── Pipeline kanban ────────────────────────────────────────────
    story += _slide(
        styles,
        eyebrow="02 · Pipeline",
        title="Kanban across 10 deal stages",
        subtitle="Sourced → Closed / Held / Exited — every live target on one board.",
        bullets=[
            "Card = company with sector, LTM rev/EBITDA, ask EV + multiple.",
            "Heat dot on each card reflects seller intent (cold/warm/hot).",
            "Sector + ownership chips filter the board in a click.",
            "Click a card → the deal detail page.",
        ],
        screenshot="11-pipeline-kanban.png",
        caption="Full pipeline kanban",
    )
    story += _slide(
        styles,
        eyebrow="02 · Pipeline",
        title="Filtered — software pipeline only",
        subtitle="Narrow to a sector in one click; board re-groups by stage.",
        bullets=[
            "Filter chips: sector · ownership (founder / family / PE / VC / carve-out).",
            "All cards update instantly without a page jump.",
            "Great for mandate conversations: 'show me LMM software deals only'.",
            "State is in the URL so the view is shareable.",
        ],
        screenshot="12-pipeline-software.png",
        caption="?sector=software",
    )
    story += _slide(
        styles,
        eyebrow="03 · Deal detail",
        title="Every deal has its own workspace",
        subtitle="Brief on the right, chat in the centre, artifacts stream in from tool calls.",
        bullets=[
            "Right pane: HQ, LTM financials, top customers, DD findings, margin + multiple.",
            "Centre: per-deal chat. Ask 'triage this', 'draft IC memo', 'show DD findings'.",
            "Any agent can be invoked without leaving the deal.",
            "New artifacts from tool calls land in the right pane alongside the brief.",
        ],
        screenshot="13-pipeline-deal.png",
        caption="Single-deal workspace",
    )

    # ── Analytics ──────────────────────────────────────────────────
    story += _slide(
        styles,
        eyebrow="04 · Analytics",
        title="Text → SQL → Plotly",
        subtitle="Ask a PE question in English; get a guarded SELECT + a chart.",
        bullets=[
            "LLM drafts a SELECT against the pehero schema; runs read-only.",
            "Chart type, x/y, and title chosen automatically from the result shape.",
            "8 curated sample questions seed the UI for first-time users.",
            "SQL is shown under the chart — auditable + reproducible.",
        ],
        screenshot="15-analytics-stages.png",
        caption="Company count by deal stage",
    )
    story += _slide(
        styles,
        eyebrow="04 · Analytics",
        title="Sector multiples over time",
        subtitle="EV/EBITDA median by sector from pehero.market_signals.",
        bullets=[
            "pehero.market_signals holds 24 months × 6 sectors × 6 metrics.",
            "Generates a grouped line chart with sector as the color dimension.",
            "Answers 'what's happening to multiples in X' in three clicks.",
            "Drops straight into the LP update / IC pre-read.",
        ],
        screenshot="16-analytics-sector.png",
        caption="EV/EBITDA median by sector",
    )

    # ── Instructions ───────────────────────────────────────────────
    story += _slide(
        styles,
        eyebrow="05 · Instructions",
        title="Prompt editing, live",
        subtitle="Every agent's system prompt is editable — from the same UI.",
        bullets=[
            "22 agents + 1 shared PE glossary, each a markdown file.",
            "Save writes to prompts/system/<slug>.md and clears the agent cache.",
            "Next conversation picks up the new prompt — no restart needed.",
            "Keeps the 'why does this agent behave this way' loop one click away.",
        ],
        screenshot="17-instructions-list.png",
        caption="All 22 agents, editable",
    )
    story += _slide(
        styles,
        eyebrow="05 · Instructions",
        title="Editing the Deal Triage prompt",
        subtitle="Workflow + tone + output format, all in markdown.",
        bullets=[
            "Prompt lives in prompts/system/deal_triage.md — version controlled.",
            "Edits go through a simple POST to /app/instructions/<slug>.",
            "The shared PE glossary (pe_context.md) is prepended to every agent prompt.",
            "Perfect for onboarding a new partner's preferred memo style.",
        ],
        screenshot="18-instructions-edit.png",
        caption="Editing an agent's system prompt",
    )

    story += _closing_slide(styles)

    doc.build(story)
    print(f"Wrote {OUT}  ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build()
