"""Build detailed, bilingual Sprint 1 + Sprint 2 team handbooks as paged PDFs.

Install requirements-pdf.txt in a separate environment. Arabic layout and
shaping are handled by WeasyPrint/Pango with locally embedded Noto fonts.
"""

import html
import json
import re
from pathlib import Path

import markdown
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"
INTERMEDIATE = ROOT / "tmp" / "pdfs" / "team-handbooks"
REVIEW_DATE = "2026-11-03"

BOOKS = [
    {
        "key": "frontend", "title": "تيم الفرونت اند", "label": "FRONTEND", "lang": "ar",
        "subtitle": "الشاشات والمكونات والمعمارية ورحلة المستخدم",
        "chapters": [
            ("Sprint 1 - الحسابات والعناوين", ["docs/pdf_sources/frontend_sprint1.md"]),
            ("Sprint 2 - المتاجر والطلب والدفع", ["docs/teams/frontend.md"]),
        ],
    },
    {
        "key": "backend", "title": "Backend Team", "label": "BACKEND", "lang": "en",
        "subtitle": "Architecture, identity, data, business rules and payment verification",
        "chapters": [
            ("Sprint 1 - Identity and customer accounts", ["docs/pdf_sources/backend_sprint1.md"]),
            ("Sprint 2 - Marketplace, orders and payments", ["docs/teams/backend.md"]),
        ],
    },
    {
        "key": "integration", "title": "تيم الانتجريشن", "label": "INTEGRATION", "lang": "ar",
        "subtitle": "ربط الواجهة والباك والعقود والجلسة والدفع",
        "chapters": [
            ("Sprint 1 - ربط الحسابات والعناوين", ["docs/pdf_sources/integration_sprint1.md"]),
            ("Sprint 2 - ربط المتاجر والطلبات والدفع", ["docs/teams/integration.md", "docs/SPRINT_2_INTEGRATION.md"]),
        ],
    },
    {
        "key": "deployment", "title": "تيم الديبلويمنت", "label": "DEPLOYMENT", "lang": "ar",
        "subtitle": "تشغيل المشروع والبيئات والخدمات وخطوات النشر",
        "chapters": [
            ("Sprint 1 - تجهيز الخدمات ونشر الحسابات", ["docs/pdf_sources/deployment_sprint1.md"]),
            ("Sprint 2 - نشر المتاجر والطلبات والدفع", ["docs/teams/deployment.md", "docs/SPRINT_2_DEPLOYMENT.md"]),
        ],
    },
    {
        "key": "testing-documentation", "title": "الاختبارات وأدوات التوثيق", "label": "TESTING & DOCS", "lang": "ar",
        "subtitle": "Unit Tests وIntegration Tests ونتائج التشغيل وطريقة التوثيق",
        "chapters": [
            ("Sprint 1 - أساس الاختبارات والتوثيق", ["docs/pdf_sources/testing_sprint1.md"]),
            ("Sprint 2 - الاختبارات المنفذة وأدوات التوثيق", ["docs/teams/testing.md", "docs/teams/documentation.md"]),
            ("ملحق - فهرس الحالات الـ243 ونتائجها", ["docs/teams/test-catalog.md"]),
        ],
    },
]

CSS = """
@font-face { font-family: 'Foodify Arabic'; src: url('/usr/share/fonts/noto/NotoSansArabic-Regular.ttf'); font-weight: 400; }
@font-face { font-family: 'Foodify Arabic'; src: url('/usr/share/fonts/noto/NotoSansArabic-Bold.ttf'); font-weight: 700; }
@font-face { font-family: 'Foodify Latin'; src: url('/usr/share/fonts/noto/NotoSans-Regular.ttf'); font-weight: 400; }
@font-face { font-family: 'Foodify Latin'; src: url('/usr/share/fonts/noto/NotoSans-Bold.ttf'); font-weight: 700; }
@font-face { font-family: 'Foodify Mono'; src: url('/usr/share/fonts/TTF/DejaVuSansMono.ttf'); }
@page {
  size: A4; margin: 21mm 18mm 20mm;
  @top-left { content: 'FOODIFY / TEAM HANDBOOK'; font: 8pt 'Foodify Latin'; color: #666; }
  @top-right { content: string(chapter-title); font: 7.2pt 'Foodify Arabic', 'Foodify Latin'; color: #777; }
  @bottom-left { content: counter(page) ' / ' counter(pages); font: 8.3pt 'Foodify Latin'; color: #666; direction: ltr; text-align: left; }
  @bottom-right { content: 'SPRINT 1 + SPRINT 2'; font: 8pt 'Foodify Latin'; color: #a72430; }
}
@page:first {
  @top-left { content: none; } @top-right { content: none; }
  @bottom-left { content: none; } @bottom-right { content: none; }
}
* { box-sizing: border-box; }
body { font: 10.8pt/1.9 'Foodify Arabic', 'Foodify Latin'; color: #202431; margin: 0; }
body[dir='ltr'] { font: 10.6pt/1.6 'Foodify Latin', 'Foodify Arabic'; }
body[dir='ltr'] p { margin-bottom: 7pt; }
p { margin: 0 0 8pt; orphans: 3; widows: 3; }
.cover { height: 249mm; break-after: page; padding: 20mm 5mm 8mm; position: relative; border-top: 5mm solid #b82032; }
.wordmark { font: 700 34pt/1.2 'Foodify Latin'; letter-spacing: -.8pt; color: #b82032; direction: ltr; }
.cover-label { color: #727781; font: 10.5pt/1.5 'Foodify Latin'; margin-top: 8mm; letter-spacing: 1.4pt; direction: ltr; }
.cover-title { font-size: 31pt; line-height: 1.6; font-weight: 700; margin: 10mm 0 3mm; color: #161c2a; }
.cover-subtitle { font-size: 14pt; line-height: 1.85; color: #5d626f; max-width: 140mm; }
.sprint-pills { margin-top: 14mm; direction: ltr; font: 700 12pt/1.5 'Foodify Latin'; color: #b82032; }
.cover-note { border-top: 1pt solid #e1e3e8; padding-top: 5mm; margin-top: 20mm; font-size: 10.2pt; color: #565b67; }
.cover-meta { font: 8.8pt/1.7 'Foodify Latin'; color: #777; margin-top: 7mm; direction: ltr; }
.contents { break-after: page; }
.contents h1 { color: #b82032; font-size: 23pt; margin: 0 0 7mm; }
.toc-items { column-count: 2; column-gap: 9mm; column-fill: balance; }
.toc-row { margin: 0 0 2pt; line-height: 1.5; font-size: 8.7pt; break-inside: avoid; }
.toc-row.level-1 { margin-top: 4mm; font-size: 10.2pt; font-weight: 700; color: #b82032; break-after: avoid; }
.toc-row.level-2 { padding-inline-start: 2mm; }
.toc-row a { color: inherit; text-decoration: none; }
.toc-row a::after { content: '  ' target-counter(attr(href), page); font-family: 'Foodify Latin'; font-weight: 700; color: #b82032; }
.toc-note { font-size: 9pt; color: #676c77; margin-bottom: 5mm; }
.chapter { break-before: page; }
.chapter-kicker { font: 700 10pt/1.4 'Foodify Latin'; letter-spacing: 1.3pt; color: #b82032; direction: ltr; margin: 0 0 3mm; }
.chapter-title { string-set: chapter-title content(); font-size: 24pt; line-height: 1.7; color: #b82032; margin: 0 0 9mm; padding-bottom: 4mm; border-bottom: 2pt solid #b82032; }
h2 { font-size: 15.2pt; line-height: 1.8; color: #1a2538; margin: 8mm 0 3mm; break-after: avoid; bookmark-level: 2; }
h3 { font-size: 12.2pt; line-height: 1.75; color: #a72430; margin: 5mm 0 2mm; break-after: avoid; bookmark-level: 3; }
h4 { font-size: 11pt; margin: 4mm 0 2mm; break-after: avoid; }
ul, ol { margin: 3mm 0 4mm; padding-inline-start: 7mm; }
li { padding-inline-start: 1mm; margin-bottom: 3pt; orphans: 2; widows: 2; }
li p { margin-bottom: 3pt; }
strong { font-weight: 700; color: #192438; }
code { font-family: 'Foodify Mono', 'Foodify Arabic'; font-size: 8.4pt; direction: ltr; unicode-bidi: isolate; overflow-wrap: anywhere; }
pre { direction: ltr; text-align: left; font: 8.4pt/1.65 'Foodify Mono', 'Foodify Arabic'; background: #f4f5f8; border: .7pt solid #e0e3e9; border-inline-start: 3pt solid #b82032; padding: 4mm; margin: 4mm 0; white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; }
pre code { font-size: inherit; }
pre.arabic-flow { direction: rtl; text-align: right; font-family: 'Foodify Arabic', 'Foodify Mono'; line-height: 1.8; }
table { width: 100%; table-layout: fixed; border-collapse: collapse; margin: 4mm 0 5mm; font-size: 9pt; line-height: 1.8; }
thead { display: table-header-group; }
th { background: #a91e2d; color: white; font-weight: 700; }
th, td { border: .5pt solid #dedfe5; padding: 2.5mm 2.6mm; vertical-align: top; text-align: start; overflow-wrap: anywhere; }
th strong { color: white; }
tbody tr:nth-child(even) { background: #f8f8fa; }
tr { break-inside: avoid; }
td code { font-size: 7.7pt; }
.catalog table.case-list th:first-child, .catalog table.case-list td:first-child { width: 82%; }
.catalog table.case-list th:last-child, .catalog table.case-list td:last-child { width: 18%; }
.catalog table.case-list td:first-child { direction: ltr; text-align: left; }
.catalog table code { font-size: 7.6pt; }
table.small-table { break-inside: avoid; }
blockquote { border-inline-start: 3pt solid #b82032; background: #faf1f3; padding: 4mm; margin: 5mm 0; }
blockquote p:last-child { margin-bottom: 0; }
a { color: #9a2230; text-decoration: none; }
hr { border: 0; border-top: 1pt solid #e0e1e6; margin: 7mm 0; }
.source-note { color: #6c727e; font-size: 8.5pt; border-top: .6pt solid #ddd; padding-top: 4mm; margin-top: 7mm; }
"""


def normalize(text: str) -> str:
    return text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")


def render_markdown(path: str, prefix: str, headings: list) -> str:
    source = normalize((ROOT / path).read_text())
    source = re.sub(r"^# [^\n]+\n", "", source, count=1)
    if path == "docs/teams/frontend.md":
        source = re.sub(r"\nللرجوع لباقي الفرق:[^\n]*\n?\Z", "\n", source)
    rendered = markdown.markdown(source, extensions=["tables", "fenced_code"])
    # Local README links are not useful once chapters are combined into one PDF.
    # Keep their descriptive text, and retain only real web-source hyperlinks.
    rendered = re.sub(r'<a href="(?!https?://)[^"]*"[^>]*>(.*?)</a>', r"\1", rendered, flags=re.S)
    index = 0

    def heading(match):
        nonlocal index
        level, content = int(match.group(1)), match.group(2)
        index += 1
        identifier = f"{prefix}-section-{index}"
        if level == 2:
            label = html.unescape(re.sub("<[^>]+>", "", content))
            headings.append((2, identifier, label))
        return f'<h{level} id="{identifier}">{content}</h{level}>'

    rendered = re.sub(r"<h([2-4])>(.*?)</h\1>", heading, rendered, flags=re.S)
    if path.endswith("test-catalog.md"):
        def catalog_table(match):
            table = match.group(0)
            head = table.split("</thead>", 1)[0]
            if len(re.findall(r"<th[ >]", head)) == 2:
                rows = table.count("<tr>")
                classes = "case-list small-table" if rows <= 8 else "case-list"
                return table.replace("<table>", f'<table class="{classes}">', 1)
            return table
        rendered = re.sub(r"<table>.*?</table>", catalog_table, rendered, flags=re.S)

    def flow(match):
        content = html.unescape(re.sub("<[^>]+>", "", match.group(1))).strip()
        css_class = "arabic-flow" if content and re.match(r"[\u0600-\u06ff]", content) else ""
        return f'<pre class="{css_class}">{match.group(1)}</pre>'

    return re.sub(r"<pre>(.*?)</pre>", flow, rendered, flags=re.S)


def build(book: dict) -> dict:
    english = book["lang"] == "en"
    direction = "ltr" if english else "rtl"
    headings = []
    sections = []
    for number, (title, sources) in enumerate(book["chapters"], 1):
        identifier = f"chapter-{number}"
        headings.append((1, identifier, title))
        contents = []
        for part, path in enumerate(sources, 1):
            if part > 1:
                part_title = "أدوات التوثيق واستخدامها الفعلي" if book["key"] == "testing-documentation" else "مرجع تنفيذي إضافي"
                contents.append(f'<h2>{part_title}</h2>')
            contents.append(render_markdown(path, f"{identifier}-part-{part}", headings))
        appendix = number > 2
        kicker = "APPENDIX" if appendix else f"SPRINT {number:02d}"
        catalog = " catalog" if appendix else ""
        sections.append(f'<section class="chapter{catalog}"><div class="chapter-kicker">{kicker}</div><h1 class="chapter-title" id="{identifier}">{html.escape(title)}</h1>{"".join(contents)}</section>')
    toc_title = "Contents and page guide" if english else "الفهرس ودليل الصفحات"
    toc_note = "Sprint 1 comes first, followed by Sprint 2. Code paths and terminology match the reviewed source." if english else "Sprint 1 أولًا ثم Sprint 2. الأرقام بجوار العناوين تشير إلى صفحات هذا الملف. أسماء الملفات والدوال مأخوذة من الكود الحالي."
    toc = f'<section class="contents"><h1>{toc_title}</h1><p class="toc-note">{toc_note}</p>'
    toc += '<div class="toc-items">'
    toc += "".join(f'<div class="toc-row level-{level}"><a href="#{identifier}">{html.escape(label)}</a></div>' for level, identifier, label in headings)
    toc += "</div></section>"
    cover_note = (
        "A detailed implementation handbook: the tools used, the purpose of each layer, request-to-database flows, security decisions, and handoffs between teams. Later repairs are identified separately from the original sprint scope."
        if english else
        "شرح تفصيلي للأدوات والاختيارات والمعمارية، وإيه اللي اتعمل وبيمشي إزاي من الشاشة للـAPI وقاعدة البيانات. الإصلاحات اللاحقة متوضحة منفصلة عن نطاق كل سبرنت، والشرح متقسم بعناوين وأمثلة ومسارات ملفات."
    )
    cover = f'<section class="cover"><div class="wordmark">foodify.</div><div class="cover-label">TEAM IMPLEMENTATION HANDBOOK</div><div class="cover-title">{html.escape(book["title"])}</div><div class="cover-subtitle">{html.escape(book["subtitle"])}</div><div class="sprint-pills">SPRINT 1 &nbsp; / &nbsp; SPRINT 2</div><div class="cover-note">{cover_note}</div><div class="cover-meta">REVIEWED SOURCE: {REVIEW_DATE}<br>FOODIFY / {book["label"]}</div></section>'
    document = f'<!doctype html><html lang="{book["lang"]}" dir="{direction}"><head><meta charset="utf-8"><title>Foodify - {html.escape(book["label"])} - Sprints 1 and 2</title><meta name="author" content="Foodify project documentation"><style>{CSS}</style></head><body dir="{direction}">{cover}{toc}{"".join(sections)}</body></html>'
    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (INTERMEDIATE / f'{book["key"]}.html').write_text(document)
    pdf = OUTPUT / f'foodify-{book["key"]}-sprints-1-2.pdf'
    rendered = HTML(string=document, base_url=str(ROOT)).render(font_config=FontConfiguration())
    rendered.write_pdf(pdf, pdf_tags=True)
    result = {"team": book["key"], "language": book["lang"], "pages": len(rendered.pages), "path": str(pdf), "bytes": pdf.stat().st_size}
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


if __name__ == "__main__":
    manifest = [build(book) for book in BOOKS]
    (OUTPUT / "foodify-team-pdfs-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
