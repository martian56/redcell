"""Render the PDF report with ReportLab: cover, TOC, executive summary,
methodology, findings, attack surface, recommendations."""

from __future__ import annotations

import base64
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from .text import humanize

INK = colors.HexColor("#14181f")
MUTED = colors.HexColor("#5b6675")
ACCENT = colors.HexColor("#c8102e")
RULE = colors.HexColor("#d8dee7")
PANEL = colors.HexColor("#f4f6f9")

SEV = {
    "critical": colors.HexColor("#b3123a"),
    "high": colors.HexColor("#e05a1a"),
    "medium": colors.HexColor("#c99700"),
    "low": colors.HexColor("#2f77c9"),
    "info": colors.HexColor("#5b6675"),
}
SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _styles():
    ss = getSampleStyleSheet()
    st = {
        "title": ParagraphStyle("rc_title", parent=ss["Title"], fontName="Helvetica-Bold",
                                fontSize=30, leading=34, textColor=INK, alignment=TA_LEFT),
        "subtitle": ParagraphStyle("rc_sub", fontName="Helvetica", fontSize=13, leading=18,
                                   textColor=MUTED),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=16, leading=20,
                             textColor=INK, spaceBefore=6, spaceAfter=8),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                             textColor=INK, spaceBefore=12, spaceAfter=4),
        "body": ParagraphStyle("rc_body", fontName="Helvetica", fontSize=10, leading=15,
                               textColor=INK, spaceAfter=6),
        "small": ParagraphStyle("rc_small", fontName="Helvetica", fontSize=8.5, leading=12,
                                textColor=MUTED),
        "verified": ParagraphStyle("rc_verified", fontName="Helvetica-Bold", fontSize=8.5,
                                   leading=12, textColor=colors.HexColor("#1a7f4b")),
        "meta": ParagraphStyle("rc_meta", fontName="Helvetica", fontSize=9, leading=13, textColor=INK),
        "mono": ParagraphStyle("rc_mono", fontName="Courier", fontSize=8, leading=11, textColor=INK),
        "label": ParagraphStyle("rc_label", fontName="Helvetica-Bold", fontSize=8, leading=11,
                                textColor=MUTED),
        "coverlabel": ParagraphStyle("rc_cl", fontName="Helvetica-Bold", fontSize=9, leading=12,
                                     textColor=MUTED),
        "covervalue": ParagraphStyle("rc_cv", fontName="Helvetica", fontSize=11, leading=15, textColor=INK),
    }
    return st


def _p(text, style):
    return Paragraph(humanize(str(text or "")).replace("\n", "<br/>"), style)


class _Bar(Flowable):
    """A thin colored severity chip used inline in tables."""
    def __init__(self, label, color, width=26 * mm, height=5 * mm):
        super().__init__()
        self.label, self.color, self.width, self.height = label, color, width, height

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.roundRect(0, 0, self.width, self.height, 1.5, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(self.width / 2, self.height / 2 - 2.6, self.label.upper())


class _Doc(BaseDocTemplate):
    def __init__(self, buf, *, company, classification, report_id, **kw):
        super().__init__(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                         topMargin=24 * mm, bottomMargin=20 * mm, **kw)
        self.company = company
        self.classification = classification
        self.report_id = report_id
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="body")
        cover = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="cover")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover]),
            PageTemplate(id="content", frames=[frame], onPage=self._decorate),
        ])

    def _decorate(self, canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, h - 14 * mm, self.company.upper())
        canvas.drawRightString(w - 20 * mm, h - 14 * mm, self.classification.upper())
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, h - 16 * mm, w - 20 * mm, h - 16 * mm)
        canvas.line(20 * mm, 15 * mm, w - 20 * mm, 15 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(20 * mm, 11 * mm, self.classification.upper())
        canvas.drawCentredString(w / 2, 11 * mm, self.report_id)
        canvas.drawRightString(w - 20 * mm, 11 * mm, f"Page {doc.page - 1}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            name = flowable.style.name
            # Footer numbering excludes the cover (Page = doc.page - 1); match it
            # in the TOC so the listed page numbers line up with the footers.
            page = max(1, self.page - 1)
            if name == "H1":
                self.notify("TOCEntry", (0, flowable.getPlainText(), page))
            elif name == "H2":
                self.notify("TOCEntry", (1, flowable.getPlainText(), page))


def _cover(st, ctx) -> list:
    out: list = []
    out.append(Spacer(1, 6 * mm))
    logo = _logo_image(ctx.get("logo_data_url"), max_h=22 * mm)
    if logo is not None:
        out.append(logo)
        out.append(Spacer(1, 10 * mm))
    else:
        out.append(_p(ctx["company"], ParagraphStyle("cc", fontName="Helvetica-Bold", fontSize=16,
                                                     textColor=ACCENT)))
        out.append(Spacer(1, 8 * mm))
    out.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=14))
    out.append(_p(ctx["title"], st["title"]))
    out.append(Spacer(1, 3 * mm))
    out.append(_p("Penetration Test Report", st["subtitle"]))
    out.append(Spacer(1, 16 * mm))
    rows = [
        ("Client", ctx["session"].client or "Unknown"),
        ("Engagement", ctx["session"].name),
        ("Targets", ", ".join(ctx["session"].targets or []) or "unset"),
        ("Report ID", ctx["report_id"]),
        ("Date", ctx["generated_at"][:10]),
        ("Classification", ctx["classification"]),
    ]
    if ctx.get("contact"):
        rows.append(("Prepared by", ctx["contact"]))
    data = [[_p(k, st["coverlabel"]), _p(v, st["covervalue"])] for k, v in rows]
    t = Table(data, colWidths=[38 * mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
    ]))
    out.append(t)
    out.append(Spacer(1, 20 * mm))
    out.append(HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=6))
    out.append(_p("This document contains confidential information intended only for the named "
                  "recipient. Handle and distribute according to its classification.", st["small"]))
    return out


def _logo_image(data_url, max_h):
    if not data_url or "," not in data_url:
        return None
    try:
        raw = base64.b64decode(data_url.split(",", 1)[1])
        img = Image(BytesIO(raw))
        ratio = img.imageWidth / max(1, img.imageHeight)
        img.drawHeight = max_h
        img.drawWidth = max_h * ratio
        img.hAlign = "LEFT"
        return img
    except Exception:
        return None


def _sev_summary_table(st, findings) -> Table:
    counts = {s: sum(1 for f in findings if f.severity == s) for s in SEV}
    header = [_p("Severity", st["label"]), _p("Count", st["label"])]
    rows = [header]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for s in ["critical", "high", "medium", "low", "info"]:
        rows.append([_Bar(s, SEV[s]), _p(str(counts[s]), st["meta"])])
    t = Table(rows, colWidths=[40 * mm, None])
    t.setStyle(TableStyle(style))
    return t


def _findings_index(st, findings) -> Table:
    header = [_p("ID", st["label"]), _p("Finding", st["label"]),
              _p("Severity", st["label"]), _p("CVSS", st["label"]), _p("Status", st["label"])]
    rows = [header]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PANEL),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for f in findings:
        verified = f.status == "verified"
        rows.append([
            _p(f.id.replace("finding-", "")[:8], st["small"]),
            _p(f.title, st["meta"]),
            _Bar(f.severity, SEV.get(f.severity, MUTED), width=22 * mm),
            _p(f"{f.cvss:.1f}" if f.cvss else "-", st["meta"]),
            _p("verified" if verified else f.status, st["verified"] if verified else st["small"]),
        ])
    t = Table(rows, colWidths=[16 * mm, None, 26 * mm, 14 * mm, 20 * mm], repeatRows=1)
    t.setStyle(TableStyle(style))
    return t


def _finding_detail(st, f, narrative) -> list:
    nf = (narrative.get("findings") or {}).get(f.id, {})
    meta = [
        [_p("Severity", st["label"]), _Bar(f.severity, SEV.get(f.severity, MUTED), width=24 * mm),
         _p("CVSS", st["label"]), _p(f"{f.cvss:.1f}" if f.cvss else "-", st["meta"])],
        [_p("CWE", st["label"]), _p(f.cwe or "-", st["meta"]),
         _p("Status", st["label"]), _p(f.status, st["meta"])],
        [_p("Location", st["label"]), _p(f.location or "-", st["meta"]), _p("", st["meta"]), _p("", st["meta"])],
    ]
    mt = Table(meta, colWidths=[22 * mm, None, 18 * mm, 26 * mm])
    mt.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("SPAN", (1, 2), (3, 2)),
    ]))
    block: list = [
        _p(f.title, st["h2"]),
        mt,
        Spacer(1, 3),
        _p("Impact", st["label"]),
        _p(nf.get("impact") or "-", st["body"]),
    ]
    ev = (f.evidence_request or "") + (("\n\n" + f.evidence_response) if f.evidence_response else "")
    if ev.strip():
        block.append(_p("Evidence", st["label"]))
        et = Table([[_p(ev[:1600], st["mono"])]], colWidths=[None])
        et.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PANEL),
                                ("BOX", (0, 0), (-1, -1), 0.4, RULE),
                                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
        block.append(et)
        block.append(Spacer(1, 3))
    block.append(_p("Remediation", st["label"]))
    block.append(_p(nf.get("remediation") or f.remediation or "-", st["body"]))
    block.append(HRFlowable(width="100%", thickness=0.4, color=RULE, spaceBefore=8, spaceAfter=8))
    return block


def build_pdf(ctx: dict) -> bytes:
    st = _styles()
    findings = sorted(ctx["findings"], key=lambda f: (SEV_ORDER.get(f.severity, 9), -(f.cvss or 0)))
    narrative = ctx["narrative"]
    buf = BytesIO()
    doc = _Doc(buf, company=ctx["company"], classification=ctx["classification"],
               report_id=ctx["report_id"])

    story: list = []
    story += _cover(st, ctx)
    story.append(NextPageTemplate("content"))
    story.append(PageBreak())

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("toc0", fontName="Helvetica-Bold", fontSize=11, leading=18, textColor=INK),
        ParagraphStyle("toc1", fontName="Helvetica", fontSize=9.5, leading=15, leftIndent=12,
                       textColor=MUTED),
    ]
    story.append(_p("Contents", st["h1"]))
    story.append(toc)
    story.append(PageBreak())

    story.append(_p("Executive Summary", st["h1"]))
    story.append(_p(narrative.get("executive_summary"), st["body"]))
    story.append(_p(narrative.get("posture"), st["body"]))
    story.append(Spacer(1, 4))
    story.append(_sev_summary_table(st, findings))
    story.append(PageBreak())

    story.append(_p("Engagement Overview", st["h1"]))
    story.append(_p(narrative.get("overview"), st["body"]))
    story.append(_p("Scope", st["h2"]))
    story.append(_p("Targets: " + (", ".join(ctx["session"].targets or []) or "unset"), st["body"]))
    story.append(_p("In-scope boundary: " + (", ".join(ctx["session"].scope or []) or "unrestricted"),
                    st["body"]))
    if ctx["session"].roe:
        story.append(_p("Rules of engagement: " + ctx["session"].roe, st["body"]))
    story.append(_p("Methodology", st["h2"]))
    story.append(_p(narrative.get("methodology"), st["body"]))
    story.append(PageBreak())

    story.append(_p("Findings Summary", st["h1"]))
    if findings:
        story.append(_findings_index(st, findings))
    else:
        story.append(_p("No findings were recorded for this engagement.", st["body"]))
    story.append(PageBreak())

    story.append(_p("Detailed Findings", st["h1"]))
    for f in findings:
        story += _finding_detail(st, f, narrative)

    hosts = ctx.get("hosts") or []
    if hosts:
        story.append(PageBreak())
        story.append(_p("Attack Surface", st["h1"]))
        rows = [[_p("Host", st["label"]), _p("IP", st["label"]), _p("Tech", st["label"]),
                 _p("Source", st["label"])]]
        for h in hosts:
            rows.append([_p(h.host, st["meta"]), _p(h.ip or "-", st["meta"]),
                         _p(", ".join(h.tech or []) or "-", st["small"]), _p(h.source or "-", st["small"])])
        t = Table(rows, colWidths=[None, 34 * mm, 45 * mm, 26 * mm], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PANEL),
                               ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                               ("LEFTPADDING", (0, 0), (-1, -1), 6), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(t)

    loot = ctx.get("loot") or []
    if loot:
        story.append(PageBreak())
        story.append(_p("Collected Artifacts", st["h1"]))
        story.append(_p("Credentials, tokens, and files obtained during the engagement. Treat as "
                        "sensitive.", st["small"]))
        rows = [[_p("Type", st["label"]), _p("Label", st["label"]), _p("Value", st["label"]),
                 _p("Source", st["label"])]]
        for x in loot:
            rows.append([_p(x.kind, st["small"]), _p(x.label, st["meta"]),
                         _p((x.value or "")[:60], st["mono"]), _p(x.source or "-", st["small"])])
        t = Table(rows, colWidths=[20 * mm, None, 55 * mm, 26 * mm], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PANEL),
                               ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                               ("LEFTPADDING", (0, 0), (-1, -1), 6), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(t)

    recs = narrative.get("recommendations") or []
    if recs:
        story.append(PageBreak())
        story.append(_p("Prioritized Recommendations", st["h1"]))
        for i, r in enumerate(recs, start=1):
            story.append(_p(f"{i}. {r}", st["body"]))

    doc.multiBuild(story)
    return buf.getvalue()
