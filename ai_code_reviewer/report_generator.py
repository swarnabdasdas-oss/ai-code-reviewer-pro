import io
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Color palette ──────────────────────────────────────────────────────────────
DARK_BG   = colors.HexColor('#050a14')
CARD_BG   = colors.HexColor('#0d1528')
CYAN      = colors.HexColor('#00d4ff')
PURPLE    = colors.HexColor('#a855f7')
GREEN     = colors.HexColor('#22c55e')
ORANGE    = colors.HexColor('#f97316')
RED       = colors.HexColor('#ef4444')
YELLOW    = colors.HexColor('#eab308')
TEXT_PRI  = colors.HexColor('#e2eaf8')
TEXT_SEC  = colors.HexColor('#6b82a8')
WHITE     = colors.white
BORDER    = colors.HexColor('#0d1e3a')

SEV_COLORS = {
    'critical': RED,
    'high':     ORANGE,
    'medium':   YELLOW,
    'low':      GREEN,
}


def _styles():
    base = getSampleStyleSheet()
    s = {}

    s['title'] = ParagraphStyle('title',
        fontSize=26, fontName='Helvetica-Bold',
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=4)

    s['subtitle'] = ParagraphStyle('subtitle',
        fontSize=12, fontName='Helvetica',
        textColor=CYAN, alignment=TA_CENTER, spaceAfter=20)

    s['h2'] = ParagraphStyle('h2',
        fontSize=16, fontName='Helvetica-Bold',
        textColor=WHITE, spaceBefore=18, spaceAfter=8)

    s['h3'] = ParagraphStyle('h3',
        fontSize=13, fontName='Helvetica-Bold',
        textColor=CYAN, spaceBefore=10, spaceAfter=4)

    s['body'] = ParagraphStyle('body',
        fontSize=10, fontName='Helvetica',
        textColor=TEXT_PRI, spaceAfter=4, leading=14)

    s['mono'] = ParagraphStyle('mono',
        fontSize=8, fontName='Courier',
        textColor=CYAN, spaceAfter=2, leading=12,
        backColor=CARD_BG, leftIndent=8, rightIndent=8,
        spaceBefore=4)

    s['small_sec'] = ParagraphStyle('small_sec',
        fontSize=9, fontName='Helvetica',
        textColor=TEXT_SEC)

    s['score_big'] = ParagraphStyle('score_big',
        fontSize=48, fontName='Helvetica-Bold',
        textColor=GREEN, alignment=TA_CENTER)

    s['label_cyan'] = ParagraphStyle('label_cyan',
        fontSize=10, fontName='Helvetica-Bold',
        textColor=CYAN, spaceAfter=2)

    return s


def _score_color(score):
    if score >= 70:
        return GREEN
    elif score >= 40:
        return YELLOW
    return RED


def _sev_badge_color(sev):
    return SEV_COLORS.get(sev.lower(), TEXT_SEC)


def generate_review_pdf(review: dict) -> bytes:
    """Generate a PDF for a single review and return bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    s = _styles()
    story = []
    W = A4[0] - 4*cm   # usable width

    # ── Cover header ────────────────────────────────────────────────────────────
    story.append(Paragraph('🚀 AI Code Reviewer Pro', s['title']))
    story.append(Paragraph('Code Review Report', s['subtitle']))
    story.append(HRFlowable(width='100%', thickness=1, color=CYAN, spaceAfter=16))

    # Meta table
    meta = [
        ['File', review.get('filename', 'N/A'),
         'Language', review.get('language', 'N/A')],
        ['Date', review.get('review_date', 'N/A'),
         'Status', review.get('status', 'completed').upper()],
    ]
    mt = Table(meta, colWidths=[2.5*cm, W/2-2.5*cm, 2.5*cm, W/2-2.5*cm])
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('TEXTCOLOR', (0, 0), (0, -1), CYAN),
        ('TEXTCOLOR', (2, 0), (2, -1), CYAN),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_PRI),
        ('TEXTCOLOR', (3, 0), (3, -1), TEXT_PRI),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [CARD_BG, BORDER]),
        ('BOX', (0, 0), (-1, -1), 0.5, CYAN),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDER),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(mt)
    story.append(Spacer(1, 20))

    # ── Score ───────────────────────────────────────────────────────────────────
    score = review.get('review_score', 0)
    sc = _score_color(score)
    score_p = ParagraphStyle('score_dyn',
        fontSize=52, fontName='Helvetica-Bold',
        textColor=sc, alignment=TA_CENTER)
    story.append(Paragraph(f'{score}', score_p))
    story.append(Paragraph('REVIEW SCORE / 100', ParagraphStyle(
        'sc_lbl', fontSize=11, fontName='Helvetica',
        textColor=TEXT_SEC, alignment=TA_CENTER, spaceAfter=4)))

    label = 'EXCELLENT' if score >= 80 else ('GOOD' if score >= 60 else ('NEEDS WORK' if score >= 40 else 'CRITICAL'))
    story.append(Paragraph(label, ParagraphStyle(
        'sc_grade', fontSize=14, fontName='Helvetica-Bold',
        textColor=sc, alignment=TA_CENTER, spaceAfter=20)))

    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=16))

    # ── Summary ─────────────────────────────────────────────────────────────────
    story.append(Paragraph('Summary', s['h2']))
    story.append(Paragraph(review.get('review_summary', 'No summary available.'), s['body']))
    story.append(Spacer(1, 12))

    # ── Quick stats ─────────────────────────────────────────────────────────────
    story.append(Paragraph('At a Glance', s['h2']))
    glance_data = [
        ['Metric', 'Value'],
        ['Bugs Found',      str(review.get('bug_count', 0))],
        ['Total Issues',    str(review.get('issue_count', 0))],
        ['Review Score',    f"{score}/100"],
        ['Language',        review.get('language', 'N/A')],
    ]
    gt = Table(glance_data, colWidths=[W*0.5, W*0.5])
    gt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CYAN),
        ('TEXTCOLOR', (0, 0), (-1, 0), DARK_BG),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, BORDER]),
        ('TEXTCOLOR', (0, 1), (0, -1), CYAN),
        ('TEXTCOLOR', (1, 1), (1, -1), TEXT_PRI),
        ('BOX', (0, 0), (-1, -1), 0.5, CYAN),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDER),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ]))
    story.append(gt)
    story.append(Spacer(1, 16))

    # ── Issues ──────────────────────────────────────────────────────────────────
    issues = review.get('issues', [])
    if issues:
        story.append(Paragraph('Detected Issues', s['h2']))
        cat_map = {}
        for iss in issues:
            cat = iss.get('category', 'General')
            cat_map.setdefault(cat, []).append(iss)

        for cat, items in cat_map.items():
            story.append(Paragraph(f'▸  {cat}  ({len(items)} issue{"s" if len(items)!=1 else ""})', s['h3']))
            for iss in items:
                sev = iss.get('severity', 'low')
                sev_col = _sev_badge_color(sev)
                row_data = [
                    [Paragraph(f"<b>{iss.get('title','')}</b>", ParagraphStyle(
                        'iss_title', fontSize=10, fontName='Helvetica-Bold',
                        textColor=WHITE)),
                     Paragraph(sev.upper(), ParagraphStyle(
                        'sev_tag', fontSize=8, fontName='Helvetica-Bold',
                        textColor=sev_col, alignment=TA_RIGHT))],
                    [Paragraph(iss.get('description', ''), ParagraphStyle(
                        'iss_desc', fontSize=9, fontName='Helvetica',
                        textColor=TEXT_PRI, leading=13)), ''],
                ]
                if iss.get('suggestion'):
                    row_data.append([
                        Paragraph(f"💡 {iss['suggestion']}", ParagraphStyle(
                            'iss_sug', fontSize=9, fontName='Helvetica',
                            textColor=GREEN, leading=13)), ''])

                it = Table(row_data, colWidths=[W-1.5*cm, 1.5*cm])
                it.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
                    ('BOX', (0, 0), (-1, -1), 0.5, sev_col),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('SPAN', (0, 1), (1, 1)),
                    *([('SPAN', (0, 2), (1, 2))] if iss.get('suggestion') else []),
                ]))
                story.append(KeepTogether([it, Spacer(1, 6)]))
        story.append(Spacer(1, 8))

    # ── Suggestions ─────────────────────────────────────────────────────────────
    suggestions = review.get('suggestions', [])
    if isinstance(suggestions, str):
        try:
            suggestions = json.loads(suggestions)
        except Exception:
            suggestions = [suggestions]
    if suggestions:
        story.append(Paragraph('Improvement Suggestions', s['h2']))
        for i, sug in enumerate(suggestions, 1):
            story.append(Paragraph(f'<b>{i}.</b> {sug}', s['body']))
        story.append(Spacer(1, 12))

    # ── Optimized code ──────────────────────────────────────────────────────────
    opt_code = review.get('optimized_code', '')
    if opt_code and opt_code.strip():
        story.append(Paragraph('Optimized Code', s['h2']))
        story.append(Paragraph(
            'Below is the refactored version of your code with all identified issues resolved:',
            s['body']))
        story.append(Spacer(1, 4))
        lines = opt_code.split('\n')
        for line in lines:
            txt = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(txt if txt.strip() else '&nbsp;', s['mono']))
        story.append(Spacer(1, 12))

    # ── Footer ──────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceBefore=20, spaceAfter=8))
    story.append(Paragraph(
        f'Generated by AI Code Reviewer Pro  •  {datetime.now().strftime("%B %d, %Y %H:%M")}',
        ParagraphStyle('footer', fontSize=8, fontName='Helvetica',
                       textColor=TEXT_SEC, alignment=TA_CENTER)))

    doc.build(story)
    buf.seek(0)
    return buf.read()


def generate_analytics_pdf(stats: dict) -> bytes:
    """Generate a full analytics / report PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    s = _styles()
    story = []
    W = A4[0] - 4*cm

    story.append(Paragraph('🚀 AI Code Reviewer Pro', s['title']))
    story.append(Paragraph('Analytics Report', s['subtitle']))
    story.append(HRFlowable(width='100%', thickness=1, color=CYAN, spaceAfter=16))
    story.append(Paragraph(
        f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}',
        ParagraphStyle('gen', fontSize=10, fontName='Helvetica',
                       textColor=TEXT_SEC, alignment=TA_CENTER, spaceAfter=20)))

    # Overview stats
    overview = stats.get('overview', {})
    story.append(Paragraph('Platform Overview', s['h2']))
    ov_data = [
        ['Total Reviews', 'Bugs Found', 'Avg Quality', 'Issues Fixed'],
        [
            str(overview.get('total_reviews', 0)),
            str(overview.get('bugs_found', 0)),
            f"{overview.get('avg_quality', 0)}%",
            str(overview.get('issues_fixed', 0)),
        ]
    ]
    ot = Table(ov_data, colWidths=[W/4]*4)
    ot.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), CARD_BG),
        ('BACKGROUND', (0, 1), (-1, 1), BORDER),
        ('TEXTCOLOR', (0, 0), (-1, 0), CYAN),
        ('TEXTCOLOR', (0, 1), (-1, 1), WHITE),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 20),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, CYAN),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDER),
        ('ROWHEIGHTS', (0, 0), (-1, -1), [24, 48]),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(ot)
    story.append(Spacer(1, 20))

    # Language distribution
    lang_dist = stats.get('language_distribution', [])
    if lang_dist:
        story.append(Paragraph('Language Distribution', s['h2']))
        ld_data = [['Language', 'Reviews', 'Share']]
        total_r = sum(r.get('count', 0) for r in lang_dist) or 1
        for r in lang_dist:
            pct = round(r['count'] / total_r * 100, 1)
            ld_data.append([r.get('language', ''), str(r['count']), f'{pct}%'])
        ldt = Table(ld_data, colWidths=[W*0.5, W*0.25, W*0.25])
        ldt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), CYAN),
            ('TEXTCOLOR', (0, 0), (-1, 0), DARK_BG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, BORDER]),
            ('TEXTCOLOR', (0, 1), (0, -1), TEXT_PRI),
            ('TEXTCOLOR', (1, 1), (-1, -1), CYAN),
            ('BOX', (0, 0), (-1, -1), 0.5, CYAN),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(ldt)
        story.append(Spacer(1, 16))

    # Bug distribution
    bug_dist = stats.get('bug_distribution', [])
    if bug_dist:
        story.append(Paragraph('Issue Category Distribution', s['h2']))
        bd_data = [['Category', 'Count']]
        for r in bug_dist:
            bd_data.append([r.get('category', ''), str(r.get('count', 0))])
        bdt = Table(bd_data, colWidths=[W*0.7, W*0.3])
        bdt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PURPLE),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, BORDER]),
            ('TEXTCOLOR', (0, 1), (0, -1), TEXT_PRI),
            ('TEXTCOLOR', (1, 1), (1, -1), PURPLE),
            ('BOX', (0, 0), (-1, -1), 0.5, PURPLE),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(bdt)
        story.append(Spacer(1, 16))

    # Score trend
    score_trend = stats.get('score_trend', [])
    if score_trend:
        story.append(Paragraph('Score Trend (Last 30 Days)', s['h2']))
        st_data = [['Date', 'Average Score']]
        for r in score_trend:
            st_data.append([r.get('day', ''), f"{round(r.get('avg_score', 0), 1)}/100"])
        stt = Table(st_data, colWidths=[W*0.6, W*0.4])
        stt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), DARK_BG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, BORDER]),
            ('TEXTCOLOR', (0, 1), (0, -1), TEXT_PRI),
            ('TEXTCOLOR', (1, 1), (1, -1), GREEN),
            ('BOX', (0, 0), (-1, -1), 0.5, GREEN),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(stt)

    # Footer
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceBefore=24, spaceAfter=8))
    story.append(Paragraph(
        f'AI Code Reviewer Pro — Analytics Report  •  {datetime.now().strftime("%B %d, %Y %H:%M")}',
        ParagraphStyle('footer', fontSize=8, fontName='Helvetica',
                       textColor=TEXT_SEC, alignment=TA_CENTER)))

    doc.build(story)
    buf.seek(0)
    return buf.read()
