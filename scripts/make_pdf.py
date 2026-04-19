"""Generate a PEHero product tour PDF from the demo screenshots.

Output: docs/pehero-product-tour.pdf

Structure:
  - Title page: product summary + synthetic-data KPIs
  - One page per captured screen, with narration
  - Closing page: install / run / regenerate instructions

Usage:
    python -m scripts.make_pdf
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image as RLImage, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
OUT = ROOT / "docs" / "pehero-product-tour.pdf"

# Palette matches the app (dark navy + amber).
INK       = HexColor("#0B1220")
ACCENT    = HexColor("#B8862E")   # darker amber so it reads on white
ACCENT_2  = HexColor("#1F4675")
MUTED     = HexColor("#5B6378")
RULE      = HexColor("#E3E6EE")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "title":    ParagraphStyle("title",    parent=ss["Title"],    fontName="Helvetica-Bold",
                                   fontSize=28, leading=34, textColor=ACCENT_2, spaceAfter=8),
        "subtitle": ParagraphStyle("subtitle", parent=ss["Normal"],   fontName="Helvetica",
                                   fontSize=12, leading=16, textColor=MUTED, spaceAfter=18),
        "h1":       ParagraphStyle("h1",       parent=ss["Heading1"], fontName="Helvetica-Bold",
                                   fontSize=18, leading=22, textColor=ACCENT_2, spaceAfter=6, spaceBefore=4),
        "h2":       ParagraphStyle("h2",       parent=ss["Heading2"], fontName="Helvetica-Bold",
                                   fontSize=13, leading=16, textColor=ACCENT, spaceAfter=4, spaceBefore=8),
        "body":     ParagraphStyle("body",     parent=ss["BodyText"], fontName="Helvetica",
                                   fontSize=10.5, leading=14.5, textColor=INK, alignment=TA_LEFT),
        "caption":  ParagraphStyle("caption",  parent=ss["Italic"],   fontName="Helvetica-Oblique",
                                   fontSize=9, leading=12, textColor=MUTED, spaceBefore=4),
    }


def _fit_image(path: Path, max_w_mm: float, max_h_mm: float) -> RLImage:
    img = Image.open(path)
    w, h = img.size
    ratio = min(max_w_mm * mm / w, max_h_mm * mm / h)
    return RLImage(str(path), width=w * ratio, height=h * ratio)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.2 * cm,
                      "PEHero — agentic AI for commercial real estate (synthetic demo data)")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
    canvas.restoreState()


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()

    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=2 * cm,
        title="PEHero — Product Tour",
        author="Predictive Labs",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=_footer)])

    story = []

    # ── title page ───────────────────────────────────────────────
    story += [
        Paragraph("PEHero", styles["title"]),
        Paragraph(
            "Agentic AI for commercial real estate — 22 specialist agents that underwrite, "
            "close, and manage your deals, already wired into PropAnalyst.",
            styles["subtitle"],
        ),
        Spacer(1, 4 * mm),
        Paragraph("What this product delivers", styles["h1"]),
        Paragraph(
            "PEHero is a full agentic system — not a prompt pack. 22 LangGraph ReAct "
            "agents share one property catalog, one T12/rent-roll store, and one RAG index "
            "across leases, zoning memos, environmental reports, property condition reports "
            "and title commitments. Agents pass artifacts between each other without the "
            "analyst re-keying anything.",
            styles["body"],
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "It ships with a deterministic synthetic CRE dataset so the system can be "
            "demoed, tested and benchmarked end-to-end — no vendor contracts required. "
            "Each data adapter is a drop-in replacement, so real CoStar / RCA / broker "
            "feeds land without code changes above the data layer.",
            styles["body"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Demo dataset", styles["h2"]),
    ]

    kpi_rows = [
        ["Specialist agents",       "22 across 5 workflow stages"],
        ["Synthetic properties",    "40 (MF 15, office 10, industrial 10, retail 5)"],
        ["Metros covered",          "8 (Austin, Phoenix, Nashville, Raleigh, Atlanta, Denver, Dallas, Tampa)"],
        ["Rent-roll line items",    "~2,600 across the catalog"],
        ["T12 rows",                "480 (12 months × 40 properties)"],
        ["Sales + rent comps",      "480 (240 sales + 240 rent)"],
        ["LP CRM contacts",         "60"],
        ["Indexed documents (RAG)", "237 (leases + zoning + env + PCR + title + market)"],
        ["Market signal rows",      "2,640 (24 months × multiple metrics × metros × asset types)"],
    ]
    t = Table(kpi_rows, colWidths=[60 * mm, 110 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("TEXTCOLOR", (0, 0), (0, -1), ACCENT_2),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [HexColor("#f6f7fb"), HexColor("#ffffff")]),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t)

    story += [
        Spacer(1, 8 * mm),
        Paragraph("How this guide is organised", styles["h2"]),
        Paragraph(
            "The following pages walk through the marketing site and a live chat session, "
            "exactly as a new user would see them. All screenshots were captured from the "
            "running FastHTML app via Playwright against the synthetic dataset.",
            styles["body"],
        ),
        PageBreak(),
    ]

    # ── one page per section ─────────────────────────────────────
    sections = [
        (
            "01-home-full.png",
            "Landing page",
            "Agentic AI for CRE — the pitch in 60 seconds.",
            "The home page states the product in one line, names the 22 specialist agents "
            "grouped into five workflow stages, and walks a visitor through Source → "
            "Underwrite → Close. Sticky navigation lands them on the app with one click.",
        ),
        (
            "02-platform-full.png",
            "Platform",
            "Not a wrapper — a system.",
            "Platform page breaks down the architecture: agents (LangGraph ReAct, one per "
            "specialty), tools (70+ StructuredTools), RAG (Postgres + pgvector across all "
            "deal documents), and memory (every conversation and artifact persists across "
            "agents).",
        ),
        (
            "03-agents-full.png",
            "Agents directory",
            "All 22 agents, grouped.",
            "The agents page renders the registry directly — each agent has a slug, a "
            "prefix for direct invocation, and a one-liner. Categories match the deal "
            "lifecycle: sourcing, underwriting, diligence, capital / LP, asset management.",
        ),
        (
            "04-agent-detail-triage.png",
            "Agent detail — Deal Triage",
            "90-second go / no-go.",
            "Each agent has its own detail page with the full description, prefix, and "
            "concrete example prompts pulled from the registry. One click into the app "
            "runs the prompt live against synthetic data.",
        ),
        (
            "05-how-it-works-full.png",
            "How it works",
            "Source → Underwrite → Diligence → Raise → Operate.",
            "The five-stage flow is explained with the participating agents named on each "
            "stage, so the reader understands exactly which specialists show up at each "
            "point in the lifecycle.",
        ),
        (
            "06-pricing-full.png",
            "Pricing",
            "Start with synthetic data. Upgrade when it sticks.",
            "Three tiers — Pilot (free 30 days), Team (per fund), Platform (custom) — "
            "scoped around a sponsor's workflow rather than per-seat or per-token metrics.",
        ),
        (
            "07-chat-empty.png",
            "Chat — empty state",
            "3-pane product — left agents, centre chat, right artifact.",
            "The chat app mirrors how a deal team actually works: sessions and all 22 "
            "agents live on the left, the chat transcript in the centre, and artifacts "
            "(property sheets, rent rolls, pro formas, memo previews) on the right. "
            "Starter prompts show the prefix syntax.",
        ),
        (
            "08-chat-rentroll.png",
            "Chat — Rent Roll Parser",
            "Tool calls flow into visible artifacts.",
            "`rr:` routes to the Rent Roll Parser. The agent searches the property, loads "
            "the current rent roll, computes WALT and the lease-expiry waterfall, and "
            "returns a concise commentary with the tables rendered in the right pane.",
        ),
        (
            "09-chat-pro-forma.png",
            "Chat — Pro Forma Builder",
            "5-year projections with the assumptions stated.",
            "`pf:` routes to the Pro Forma Builder. It normalises the T12, runs a 5-year "
            "projection with rent-growth, vacancy, opex-inflation, capex reserve and exit "
            "cap — persisting the run in `pehero.pro_formas` — and prints the "
            "unlevered IRR, CoC and MOIC in-line.",
        ),
        (
            "10-chat-memo.png",
            "Chat — Investor Memo",
            "An IC-ready memo from the deal's own data.",
            "`memo:` routes to the Investor Memo Writer. It pulls the compact deal "
            "dossier, supplements with sales comps and market signals, and produces a "
            "structured memo — Exec Summary, Strategy, Market, Underwriting, Risks, "
            "Recommendation — with every figure cited from tool calls.",
        ),
    ]

    for fname, title, subtitle, body in sections:
        path = SHOTS / fname
        if not path.exists():
            continue
        story += [
            Paragraph(title, styles["h1"]),
            Paragraph(subtitle, styles["subtitle"]),
            Paragraph(body, styles["body"]),
            Spacer(1, 4 * mm),
            _fit_image(path, max_w_mm=170, max_h_mm=185),
            Paragraph(f"Screenshot: {fname}", styles["caption"]),
            PageBreak(),
        ]

    # ── install / regen ──────────────────────────────────────────
    story += [
        Paragraph("Installing and running", styles["h1"]),
        Paragraph(
            "<b>Requirements:</b> Python 3.12+, PostgreSQL 15+ with pgvector.",
            styles["body"],
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "<font face='Courier'>"
            "git clone &lt;repo&gt; pehero<br/>"
            "cd pehero<br/>"
            "cp .env.example .env  # fill DB_URL, XAI_API_KEY<br/>"
            "python -m venv .venv &amp;&amp; source .venv/bin/activate<br/>"
            "pip install -r requirements.txt<br/>"
            "python -m db.migrate<br/>"
            "python -m synthetic.generate --seed 42<br/>"
            "python main.py"
            "</font>",
            styles["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Regenerating this guide", styles["h2"]),
        Paragraph(
            "Screenshots are captured via Playwright "
            "(<font face='Courier'>scripts/capture_screenshots.py</font>). The PDF is "
            "assembled by <font face='Courier'>scripts/make_pdf.py</font>, and the "
            "animated GIF by <font face='Courier'>scripts/make_gif.py</font>.",
            styles["body"],
        ),
        Spacer(1, 10 * mm),
        Paragraph(
            "<i>All figures in this guide are generated from synthetic data. "
            "Do not cite for operational decisions.</i>",
            styles["caption"],
        ),
    ]

    doc.build(story)
    print(f"Wrote {OUT}  ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build()
