"""Memo → PDF preview + PDF viewer routes.

Flow
----
1. After any chat message (esp. IC Memo Writer output), the client can POST
   the rendered markdown to /app/memo-pdf/render. We save it as an HTML →
   PDF in a session-scoped cache and return a file_id.

2. The right pane iframe loads /app/memo-pdf/view/<file_id>?search=<text>
   which redirects to Mozilla's public PDF.js viewer pointed at
   /app/memo-pdf/file/<file_id>. `#search=...&phrase=true` enables the
   highlight.

3. Subsequent chat turns that want to "show me the deal size" can trigger
   the same highlight without a full reload.

We keep the PDFs on disk (one directory per user session) to avoid leaking
across users.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Optional

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr, Div, Span, H1, P, A,
)
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer,
)
from starlette.requests import Request
from starlette.responses import (
    FileResponse, HTMLResponse, JSONResponse, RedirectResponse,
)

from app import rt
from utils.session import get_currency, currency_symbol

log = logging.getLogger(__name__)

CACHE_DIR = Path("/tmp/pehero-memo-pdf")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

INK = HexColor("#14231B")
INK_MUTED = HexColor("#415046")
ACCENT = HexColor("#1F5D43")
RULE = HexColor("#E3DFD2")


def _session_dir(request: Request) -> Path:
    sess_id = request.session.get("memo_pdf_session")
    if not sess_id:
        sess_id = uuid.uuid4().hex
        request.session["memo_pdf_session"] = sess_id
    d = CACHE_DIR / sess_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── markdown → PDF ───────────────────────────────────────────────────

def _styles():
    ss = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                              fontSize=20, leading=24, textColor=ACCENT, spaceAfter=8, spaceBefore=4),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                              fontSize=14, leading=18, textColor=INK, spaceAfter=6, spaceBefore=10),
        "h3": ParagraphStyle("h3", parent=ss["Heading3"], fontName="Helvetica-Bold",
                              fontSize=12, leading=16, textColor=INK, spaceAfter=4, spaceBefore=8),
        "body": ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica",
                                fontSize=10.5, leading=15, textColor=INK, alignment=TA_LEFT,
                                spaceAfter=4),
        "bullet": ParagraphStyle("bullet", parent=ss["BodyText"], fontName="Helvetica",
                                  fontSize=10.5, leading=15, textColor=INK, leftIndent=14,
                                  bulletIndent=0, spaceAfter=2),
        "caption": ParagraphStyle("caption", parent=ss["Italic"], fontName="Helvetica-Oblique",
                                   fontSize=8.5, leading=11, textColor=INK_MUTED),
    }


# Inline markdown → reportlab mini-HTML (Platypus supports <b>, <i>, <font>, <br/>)
_INLINE = [
    (re.compile(r"\*\*(.+?)\*\*"), r"<b>\1</b>"),
    (re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"), r"<i>\1</i>"),
    (re.compile(r"`([^`]+)`"), r"<font face='Courier'>\1</font>"),
]


def _inline(text: str) -> str:
    out = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for rx, repl in _INLINE:
        out = rx.sub(repl, out)
    return out


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(INK_MUTED)
    canvas.drawString(2 * cm, 1.2 * cm, "PEHero · IC memo (generated)")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.4)
    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.restoreState()


def markdown_to_pdf(markdown_text: str, out_path: Path, *, title: str = "IC memo") -> None:
    styles = _styles()
    doc = BaseDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=2 * cm,
        title=title, author="PEHero",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=_footer)])

    story = []
    lines = markdown_text.splitlines()
    in_list: list[str] = []

    def flush_list():
        for item in in_list:
            story.append(Paragraph("• " + _inline(item), styles["bullet"]))
        in_list.clear()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_list()
            story.append(Spacer(1, 4))
            continue
        if line.startswith("# "):
            flush_list()
            story.append(Paragraph(_inline(line[2:].strip()), styles["h1"]))
        elif line.startswith("## "):
            flush_list()
            story.append(Paragraph(_inline(line[3:].strip()), styles["h2"]))
        elif line.startswith("### "):
            flush_list()
            story.append(Paragraph(_inline(line[4:].strip()), styles["h3"]))
        elif line.startswith("- ") or line.startswith("* "):
            in_list.append(line[2:].strip())
        else:
            flush_list()
            story.append(Paragraph(_inline(line), styles["body"]))

    flush_list()
    if not story:
        story.append(Paragraph("(empty memo)", styles["caption"]))
    doc.build(story)


# ── Routes ───────────────────────────────────────────────────────────

@rt("/app/memo-pdf/render", methods=["POST"])
async def memo_render(request: Request):
    """Accept the memo markdown, render a PDF, return a file_id."""
    form = await request.form()
    md = (form.get("markdown") or "").strip()
    title = (form.get("title") or "IC memo").strip()[:120]
    if not md:
        return JSONResponse({"error": "empty markdown"}, status_code=400)

    # Content-addressed ID so identical memos share a cached PDF.
    fid = hashlib.sha1(md.encode("utf-8")).hexdigest()[:16]
    out = _session_dir(request) / f"{fid}.pdf"
    if not out.exists():
        try:
            markdown_to_pdf(md, out, title=title)
        except Exception as e:  # noqa: BLE001
            log.exception("memo pdf render failed")
            return JSONResponse({"error": str(e)}, status_code=500)
    request.session["memo_pdf_last_id"] = fid
    return JSONResponse({
        "ok": True,
        "file_id": fid,
        "view_url": f"/app/memo-pdf/view/{fid}",
        "file_url": f"/app/memo-pdf/file/{fid}",
        "title": title,
    })


@rt("/app/memo-pdf/file/{file_id}")
async def memo_file(request: Request, file_id: str):
    """Serve the raw PDF (consumed by PDF.js viewer in iframe)."""
    if not re.fullmatch(r"[a-f0-9]{8,64}", file_id):
        return JSONResponse({"error": "bad id"}, status_code=400)
    p = _session_dir(request) / f"{file_id}.pdf"
    if not p.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(str(p), media_type="application/pdf")


@rt("/app/memo-pdf/view/{file_id}")
async def memo_view(request: Request, file_id: str, search: str = ""):
    """Redirect to Mozilla's hosted PDF.js viewer pointed at our /file/<id>.

    Uses #search=&phrase=true so the viewer highlights + scrolls to the
    first match. Returns an iframe-friendly HTML fragment rather than a
    redirect so we can embed it directly in the right pane.
    """
    if not re.fullmatch(r"[a-f0-9]{8,64}", file_id):
        return JSONResponse({"error": "bad id"}, status_code=400)

    base = str(request.base_url).rstrip("/")
    file_url = f"{base}/app/memo-pdf/file/{file_id}"
    from urllib.parse import quote
    viewer = ("https://mozilla.github.io/pdf.js/web/viewer.html"
              f"?file={quote(file_url, safe='')}")
    if search:
        viewer += f"#search={quote(search[:120])}&phrase=true"
    # Return a tiny HTML that just redirects (we embed the PDF.js URL
    # directly in the iframe, so this endpoint is rarely hit; keeping for
    # completeness + linkability).
    return RedirectResponse(url=viewer, status_code=302)


@rt("/app/memo-pdf/highlight", methods=["POST"])
async def memo_highlight(request: Request):
    """Return a PDF.js viewer URL for the last-rendered memo with a search term.

    Client calls this when the user asks a follow-up question like
    'show me the deal size'. The client then updates the iframe src.
    """
    form = await request.form()
    search = (form.get("search") or "").strip()
    file_id = (form.get("file_id") or request.session.get("memo_pdf_last_id") or "").strip()
    if not file_id:
        return JSONResponse({"error": "no pdf rendered yet"}, status_code=400)
    if not re.fullmatch(r"[a-f0-9]{8,64}", file_id):
        return JSONResponse({"error": "bad id"}, status_code=400)

    base = str(request.base_url).rstrip("/")
    file_url = f"{base}/app/memo-pdf/file/{file_id}"
    from urllib.parse import quote
    url = ("https://mozilla.github.io/pdf.js/web/viewer.html"
           f"?file={quote(file_url, safe='')}")
    if search:
        url += f"#search={quote(search[:120])}&phrase=true"
    return JSONResponse({"ok": True, "file_id": file_id, "viewer_url": url,
                         "search": search})
