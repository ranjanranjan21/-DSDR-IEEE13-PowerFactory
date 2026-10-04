"""
Word version of the report: report/main.tex -> report/DSDR_Report.docx

The LaTeX source is converted with pandoc, so headings, tables and equations stay editable in Word.  Figure,
table and equation numbers, cross references and citations are taken from a LaTeX run (main.aux), so they
are the same as in the PDF.  python-docx then adds the title page, the table of contents, Times New Roman,
framed tables and a page break before every chapter.

Needs: pypandoc_binary, python-docx (pip install pypandoc_binary python-docx) and TinyTeX.
"""

import copy
import os
import re
import shutil
import subprocess
import tempfile

import pypandoc
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from table_style import _balanced, _columns

HERE = os.path.dirname(os.path.abspath(__file__))
REP = os.path.join(HERE, "report")
FIGS = os.path.join(REP, "figures")
OUT = os.path.join(REP, "DSDR_Report.docx")
PDFLATEX = os.path.join(os.environ.get("APPDATA", ""), "TinyTeX", "bin", "windows", "pdflatex.exe")
BS = "\\"


# ---------------------------------------------------------------------------------------------
def aux_numbers(tex):
    """compile once (twice for the references) and read label numbers and citation numbers"""
    work = tempfile.mkdtemp(prefix="docx_")
    shutil.copytree(FIGS, os.path.join(work, "figures"))
    open(os.path.join(work, "main.tex"), "w", encoding="utf-8").write(tex)
    exe = PDFLATEX if os.path.exists(PDFLATEX) else "pdflatex"
    for _ in range(2):
        subprocess.run([exe, "-interaction=nonstopmode", "main.tex"], cwd=work, capture_output=True)
    aux = open(os.path.join(work, "main.aux"), encoding="utf-8", errors="replace").read()
    labels = dict(re.findall(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}", aux))
    cites = dict(re.findall(r"\\bibcite\{([^}]*)\}\{([^}]*)\}", aux))
    shutil.rmtree(work, ignore_errors=True)
    return labels, cites


def arg(s, i):
    """(content, end) of the brace group starting at s[i] == '{'"""
    j = _balanced(s, i)
    return s[i + 1:j - 1], j


def replace_cmd(s, name, fn, nargs=1):
    """replace \\name{a}{b}.. by fn(a, b, ..)"""
    out, pos = [], 0
    pat = re.compile(re.escape(BS + name) + r"\s*\{")
    while True:
        m = pat.search(s, pos)
        if not m:
            break
        args, j = [], m.end() - 1
        for _ in range(nargs):
            while s[j] in " \n":
                j += 1
            a, j = arg(s, j)
            args.append(a)
        out.append(s[pos:m.start()])
        out.append(fn(*args))
        pos = j
    out.append(s[pos:])
    return "".join(out)


def body_for_pandoc(tex, labels, cites):
    s = tex[tex.index("\\end{titlepage}") + len("\\end{titlepage}"):tex.index("\\end{document}")]
    # ---- front matter commands that only make sense in LaTeX
    for pat in (r"\\pagenumbering\{[^}]*\}", r"\\setcounter\{[^}]*\}\{[^}]*\}", r"\\clearpage", r"\\phantomsection",
                r"\\addcontentsline\{[^}]*\}\{[^}]*\}\{[^}]*\}", r"\\begin\{spacing\}\{[^}]*\}", r"\\end\{spacing\}",
                r"\\listoffigures", r"\\listoftables", r"\\vfill", r"\\vspace\*?\{[^}]*\}",
                r"\\setlength\{[^}]*\}\{[^}]*\}", r"\\(footnotesize|scriptsize|small|large|centering)\b",
                r"\\cellcolor\{[^}]*\}", r"\\rowcolor\{[^}]*\}", r"\\hd\b"):
        s = re.sub(pat, "", s)
    s = s.replace(BS + "tableofcontents", "\n\nTOCMARKER\n\n")
    # ---- macros
    s = s.replace("$\\checkmark$", "\u2713").replace("$\\times$", "×")
    s = re.sub(r"\\ok\b", "\u2713", s)
    s = re.sub(r"\\no\b", "×", s)
    s = re.sub(r"\\ohm(\{\})?", "\u2009\u03a9", s)
    s = re.sub(r"\\PF(\{\})?", "PowerFactory", s)
    s = re.sub(r"\$([+-]?)(\d[\d.,]*)\$", lambda m: m.group(1).replace("-", "\u2212") + m.group(2), s)
    s = s.replace("$\\approx$", "\u2248").replace("$\\rightarrow$", "\u2192")
    # ---- headings with the numbering of the PDF
    chap = [0, 0, 0]

    def head(m):
        kind = m.group(1)
        if kind == "chapterhead":
            chap[:] = [chap[0] + 1, 0, 0]
            return BS + "section*{CHAPTER %s: %s}" % (m.group(2), m.group(3))
        if kind == "fronthead":
            return BS + "section*{%s}" % m.group(2)
        if kind == "appendixhead":
            return BS + "section*{APPENDIX %s: %s}" % (m.group(2), m.group(3))
        if kind == "subsection":
            chap[1], chap[2] = chap[1] + 1, 0
            return BS + "subsection*{%d.%d\u2002\u2009%s}" % (chap[0], chap[1], m.group(2))
        chap[2] += 1
        return BS + "subsubsection*{%d.%d.%d  %s}" % (chap[0], chap[1], chap[2], m.group(2))

    s = re.sub(r"\\(chapterhead|appendixhead)\{([^}]*)\}\{([^}]*)\}|\\(fronthead)\{([^}]*)\}|\\(subsection|subsubsection)\{([^}]*)\}",
               lambda m: head(_Groups(m)), s)
    # ---- figure and table captions with their numbers
    def env(kind, word):
        nonlocal s
        out, pos = [], 0
        for m in re.finditer(r"\\begin\{%s\}(\[[^\]]*\])?" % kind, s):
            if m.start() < pos:
                continue
            end = s.index("\\end{%s}" % kind, m.end())
            block = s[m.end():end]
            lab = re.search(r"\\label\{([^}]*)\}", block)
            num = labels.get(lab.group(1), "?") if lab else "?"
            block = replace_cmd(block, "caption", lambda c, n=num: BS + "caption{%s %s %s}" % (word, n, c))
            out += [s[pos:m.start()], "\\begin{%s}" % kind, block]
            pos = end
        out.append(s[pos:])
        s = "".join(out)
    env("figure", "Figure")
    env("table", "Table")
    # ---- equation numbers: every equation environment is numbered in turn, as in LaTeX; the number is
    #      written next to the equation because Word equations have no \tag
    state = {"pre": "0", "n": 0, "chap": 0}

    def number(m):
        if m.group("chap") is not None:                         # a new chapter or appendix
            if m.group("chap").startswith("APPENDIX"):
                state["pre"] = m.group("chap").split()[1].rstrip(":")
            else:
                state["chap"] += 1
                state["pre"] = str(state["chap"])
            state["n"] = 0
            return m.group(0)
        env, body = m.group("env"), m.group("body")
        body = re.sub(r"\\label\{[^}]*\}", "", body).strip()
        if env == "equation":
            state["n"] += 1
            return "\\begin{equation*}%s\\qquad\\qquad(%s.%d)\\end{equation*}" % (body, state["pre"], state["n"])
        lines = []
        for ln in re.split(r"\\\\", body):                   # align: every line numbered
            if ln.strip():
                state["n"] += 1
                lines.append("%s\\qquad(%s.%d)" % (ln.rstrip(), state["pre"], state["n"]))
        return "\\begin{align*}%s\\end{align*}" % "\\\\".join(lines)

    s = re.sub(r"\\section\*\{(?P<chap>(?:CHAPTER|APPENDIX) [^}]*)\}"
               r"|\\begin\{(?P<env>equation|align)\}(?P<body>.*?)\\end\{(?P=env)\}", number, s, flags=re.S)
    # ---- references and citations
    s = re.sub(r"\\eqref\{([^}]*)\}", lambda m: "(%s)" % labels.get(m.group(1), "?"), s)
    s = re.sub(r"\\ref\{([^}]*)\}", lambda m: labels.get(m.group(1), "?"), s)
    s = re.sub(r"\\cite\{([^}]*)\}", lambda m: "[%s]" % ", ".join(cites.get(k.strip(), "?") for k in m.group(1).split(",")), s)
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = replace_cmd(s, "bibitem", lambda k: "\n\n[%s] " % cites.get(k, "?"))
    s = s.replace("\\begin{thebibliography}{99}", BS + "section*{REFERENCES}").replace("\\end{thebibliography}", "")
    s = re.sub(r"\\begin\{thebibliography\}\{[^}]*\}", lambda m: BS + "section*{REFERENCES}", s)
    # ---- tabularx -> tabular with simple column types
    def tabx(m):
        spec, j = arg(s_ref[0], m.end() - 1)
        cols = []
        for c in _columns(spec):
            c = c.split("}")[-1] if c.startswith(">") else c
            cols.append("l" if c in ("L", "X") else c)
        return "\\begin{tabular}{|%s|}" % "|".join(cols), j

    out, pos = [], 0
    s_ref = [s]
    for m in re.finditer(r"\\begin\{tabularx\}\{\\(?:text|line)width\}\{", s):
        new, j = tabx(m)
        out += [s[pos:m.start()], new]
        pos = j
    out.append(s[pos:])
    s = "".join(out).replace("\\end{tabularx}", "\\end{tabular}")
    return s


class _Groups:
    """normalise the alternatives of the heading regex to (kind, a, b)"""

    def __init__(self, m):
        g = [x for x in m.groups()]
        if g[0]:
            self.g = (g[0], g[1], g[2])
        elif g[3]:
            self.g = (g[3], g[4], None)
        else:
            self.g = (g[5], g[6], None)

    def group(self, k):
        return self.g[k - 1]


# ---------------------------------------------------------------------------------------------
def set_font(style, size=None, bold=None, color=True):
    style.font.name = "Times New Roman"
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(a), "Times New Roman")
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if fonts.get(qn(a)) is not None:
            del fonts.attrib[qn(a)]
    if size:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if color:
        style.font.color.rgb = RGBColor(0, 0, 0)


def borders(table):
    tbl = table._tbl
    pr = tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:%s" % edge)
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")
        b.append(e)
    old = pr.find(qn("w:tblBorders"))
    if old is not None:
        pr.remove(old)
    pr.append(b)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "center")
    pr.append(jc)


def plain_list(table):
    """two-column list without borders (3.6 cm + 11.4 cm), 12 pt, as the lists of symbols and abbreviations"""
    pr = table._tbl.tblPr
    for tag in ("w:tblBorders", "w:tblW", "w:jc", "w:tblLayout", "w:tblCellMar", "w:tblStyle"):
        old = pr.find(qn(tag))
        if old is not None:
            pr.remove(old)
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:%s" % edge)
        e.set(qn("w:val"), "nil")
        b.append(e)
    pr.append(b)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    pr.append(lay)
    mar = OxmlElement("w:tblCellMar")
    for side, v in (("top", 20), ("left", 0), ("bottom", 20), ("right", 60)):
        e = OxmlElement("w:%s" % side)
        e.set(qn("w:w"), str(v))
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    pr.append(mar)
    widths = (Cm(3.6), Cm(11.4))
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(w.twips)))
    for row in table.rows:
        for c, w in zip(row.cells, widths):
            c.width = w
            for p in c.paragraphs:
                pf = p.paragraph_format
                pf.first_line_indent, pf.left_indent = Cm(0), Cm(0)
                pf.space_before = pf.space_after = Pt(0)
                pf.line_spacing, pf.line_spacing_rule = Pt(18.6), WD_LINE_SPACING.EXACTLY
                pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.size = Pt(12)
                    r.bold = False


def toc_field(paragraph, instr=None):
    run = paragraph.add_run()
    for kind, text in (("begin", None), (None, instr or 'TOC \\o "1-3" \\h \\z \\u'), ("separate", None), (None, None), ("end", None)):
        if kind:
            f = OxmlElement("w:fldChar")
            f.set(qn("w:fldCharType"), kind)
            run._r.append(f)
        elif text:
            t = OxmlElement("w:instrText")
            t.set(qn("xml:space"), "preserve")
            t.text = text
            run._r.append(t)
        else:
            t = OxmlElement("w:t")
            t.text = "Right-click here and choose Update Field to build the table of contents."
            run._r.append(t)


def title_page(doc, tex):
    """title page as in the IoE guideline: logo, university, institute, campus, title, BY, name, purpose, date"""
    tp = tex[tex.index("\\begin{titlepage}"):tex.index("\\end{titlepage}")]
    title = re.search(r"\\itshape (An Adaptive.*?)\\par", tp, re.S).group(1)
    title = " ".join(title.replace("\\\\", " ").split())
    first = doc.paragraphs[0]
    lines = [("LOGO", 0, False, False, 50), ("TRIBHUVAN UNIVERSITY", 14, False, False, 21),
             ("INSTITUTE OF ENGINEERING", 16, True, False, 17), ("PULCHOWK CAMPUS", 14, True, False, 53),
             (title, 14, True, True, 50), ("BY:", 12, False, False, 10), ("Jhala Nath Kafle", 12, True, True, 10),
             ("(081MSPSE009)", 12, False, False, 36),
             ("A PROJECT REPORT SUBMITTED IN PARTIAL FULFILLMENT OF THE REQUIREMENTS FOR THE MASTER'S DEGREE IN "
              "POWER SYSTEM ENGINEERING", 12, False, False, 21),
             ("DEPARTMENT OF ELECTRICAL ENGINEERING", 12, False, False, 30), ("OCTOBER, 2026", 12, False, True, 0)]
    for text, size, bold, ital, after in lines:
        p = first.insert_paragraph_before()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = Pt(22 if text == title else 20 if size >= 14 else 18)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY if text != "LOGO" else WD_LINE_SPACING.SINGLE
        if text == "LOGO":
            p.add_run().add_picture(os.path.join(FIGS, "tu_logo.png"), width=Cm(3.4))
            continue
        r = p.add_run(text)
        r.font.size, r.bold, r.italic = Pt(size), bold, ital
    return first.insert_paragraph_before()           # carries the section break after the title page


def section_break(doc, paragraph):
    """end a section at this paragraph (next section starts on a new page)"""
    body_sect = doc.element.body.find(qn("w:sectPr"))
    new = copy.deepcopy(body_sect)
    for ref in new.findall(qn("w:headerReference")) + new.findall(qn("w:footerReference")):
        new.remove(ref)
    paragraph._p.get_or_add_pPr().append(new)


def page_numbers(section, fmt, start=1):
    """page number at the bottom centre (footer), fmt: lowerRoman or decimal; start: first number"""
    pg = section._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        section._sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt)
    pg.set(qn("w:start"), str(start))
    section.header.is_linked_to_previous = False
    for hp in section.header.paragraphs:
        hp.text = ""
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(0)
    run = p.add_run()
    run.font.name, run.font.size = "Times New Roman", Pt(12)
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            f = OxmlElement("w:fldChar")
            f.set(qn("w:fldCharType"), kind)
            run._r.append(f)
        else:
            t = OxmlElement("w:instrText")
            t.set(qn("xml:space"), "preserve")
            t.text = text
            run._r.append(t)


def no_page_number(section):
    for part in (section.footer, section.header):
        part.is_linked_to_previous = False
        for p in part.paragraphs:
            p.text = ""


def pdf_table_sizes():
    """font size of every table of the LaTeX PDF, by table number (the text above each table caption)"""
    pdf = os.path.join(REP, "DSDR_Report.pdf")
    sizes = {}
    if not os.path.exists(pdf):
        return sizes
    import collections
    import fitz
    for pg in fitz.open(pdf):
        spans = [(ln["bbox"][1], sp["size"], sp["text"], sp["bbox"][0], sp["bbox"][2])
                 for b in pg.get_text("dict")["blocks"] if b["type"] == 0
                 for ln in b["lines"] for sp in ln["spans"] if sp["text"].strip()]
        caps = sorted((y, m.group(1)) for y, sz, t, x0, x1 in spans
                      for m in [re.match(r"Table ([A-Z0-9]+\.\d+)", t)] if m and abs(sz - 12) < 0.3)
        prev = 0
        for y, num in caps:
            cell = [(z, x0, x1) for y0, z, t, x0, x1 in spans if prev < y0 < y and z < 11.5]
            if cell:
                size = collections.Counter(round(z * 2) / 2 for z, _, _ in cell).most_common(1)[0][0]
                span = max(x1 for _, _, x1 in cell) - min(x0 for _, x0, _ in cell)
                sizes[num] = (size, span > 0.85 * 467)        # 467 pt = text width: a full-width table
            prev = y
    return sizes


def table_number(tbl):
    """number of a Word table from its caption (just after or just before it)"""
    for el in (tbl.getnext(), tbl.getprevious()):
        if el is not None and el.tag == qn("w:p"):
            m = re.match(r"\s*Table ([A-Z0-9]+\.\d+)", "".join(t.text or "" for t in el.iter(qn("w:t"))))
            if m:
                return m.group(1)
    return None


def approval_page(doc):
    """page of approval laid out as in the PDF: institution lines centred, the certificate text, the four
    signature blocks in a two-by-two grid, the date of approval centred"""
    heads = [p for p in doc.paragraphs if p.style.name == "Heading 1"]
    head = next((p for p in heads if p.text.strip() == "PAGE OF APPROVAL"), None)
    if head is None:
        return
    nxt = heads[heads.index(head) + 1]
    el = head._p.getnext()
    while el is not None and el is not nxt._p:           # drop what pandoc made of the minipages
        following = el.getnext()
        el.getparent().remove(el)
        el = following

    def para(align, before=0, after=0):
        q = nxt.insert_paragraph_before()
        f = q.paragraph_format
        f.alignment, f.first_line_indent, f.left_indent = align, Cm(0), Cm(0)
        f.space_before, f.space_after = Pt(before), Pt(after)
        f.line_spacing, f.line_spacing_rule = Pt(17.9), WD_LINE_SPACING.AT_LEAST
        return q

    def run(q, text, bold=False, italic=False):
        r = q.add_run(text)
        r.font.size, r.bold, r.italic = Pt(12), bold, italic
        return r

    q = para(WD_ALIGN_PARAGRAPH.CENTER, after=14)
    lines = ("TRIBHUVAN UNIVERSITY", "INSTITUTE OF ENGINEERING", "PULCHOWK CAMPUS", "DEPARTMENT OF ELECTRICAL ENGINEERING")
    for k, t in enumerate(lines):
        r = run(q, t)
        if k < len(lines) - 1:
            r.add_break()
    q = para(WD_ALIGN_PARAGRAPH.JUSTIFY, after=56)
    run(q, "The undersigned certify that they have read, and recommended to the Institute of Engineering for "
           "acceptance, a project report entitled \u201c")
    run(q, "An Adaptive Overcurrent Protection Scheme for Dual-Setting Directional Recloser and Fuse Coordination "
           "in Unbalanced Distribution Networks With Distributed Generation", italic=True)
    run(q, "\u201d submitted by ")
    run(q, "Jhala Nath Kafle", italic=True)
    run(q, " in partial fulfilment of the requirements for the Master\u2019s degree in Power System Engineering.")

    blocks = [[("Jeetendra Chaudhary", True), ("Head of Department &", True),
               ("M.Sc. Program Coordinator (MSPDE)", True), ("Department of Electrical Engineering", True)],
              [("Akhileshwar Mishra", True), ("M.Sc. Program Coordinator (MSPSE)", True),
               ("Department of Electrical Engineering", True)]]
    table = doc.add_table(rows=1, cols=2)
    nxt._p.addprevious(table._tbl)
    pr = table._tbl.tblPr
    for tag in ("w:tblStyle", "w:tblBorders", "w:tblLayout", "w:tblW", "w:tblLook"):
        old = pr.find(qn(tag))
        if old is not None:
            pr.remove(old)
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:%s" % edge)
        e.set(qn("w:val"), "nil")
        b.append(e)
    pr.append(b)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    pr.append(lay)
    look = OxmlElement("w:tblLook")                      # no header-row formatting of the default table style
    for a_, v_ in (("w:val", "0000"), ("w:firstRow", "0"), ("w:lastRow", "0"), ("w:firstColumn", "0"),
                   ("w:lastColumn", "0"), ("w:noHBand", "1"), ("w:noVBand", "1")):
        look.set(qn(a_), v_)
    pr.append(look)
    for tc in table._tbl.iter(qn("w:tc")):               # and no borders on the cells themselves
        tcpr = tc.get_or_add_tcPr()
        tb = OxmlElement("w:tcBorders")
        for edge in ("top", "left", "bottom", "right"):
            e = OxmlElement("w:%s" % edge)
            e.set(qn("w:val"), "nil")
            tb.append(e)
        tcpr.append(tb)
    for k, items in enumerate(blocks):
        cell = table.rows[k // 2].cells[k % 2]
        cell.width = Cm(7.75)
        q = cell.paragraphs[0]
        for j, (text, ital) in enumerate([("\u2500" * 22, False)] + items):
            if j:
                q = cell.add_paragraph()
            f = q.paragraph_format
            f.alignment, f.first_line_indent = WD_ALIGN_PARAGRAPH.LEFT, Cm(0)
            f.space_before = Pt(0)
            f.space_after = Pt(0)
            f.line_spacing, f.line_spacing_rule = Pt(17.9), WD_LINE_SPACING.AT_LEAST
            r = run(q, text, italic=ital)
            if j == 0:
                r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    q = para(WD_ALIGN_PARAGRAPH.CENTER, before=74)
    run(q, "DATE OF APPROVAL: ", bold=True)
    run(q, "6 October 2026", italic=True)


def polish(path, tex):
    doc = Document(path)
    for sec in doc.sections:
        sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)      # A4
        sec.left_margin, sec.right_margin = Cm(3.5), Cm(2.0)
        sec.top_margin, sec.bottom_margin = Cm(3.5), Cm(2.0)
        sec.header_distance = Cm(2.0)
        sec.footer_distance = Cm(1.0)
    st = doc.styles
    for name in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if name in [s.name for s in st]:
            set_font(st[name], 12, color=False)
            pf = st[name].paragraph_format
            if name == "Compact":
                pf.line_spacing = 1.0
            else:                                      # as the LaTeX report: 17.9 pt lines, 10 pt parskip
                pf.line_spacing = Pt(17.9)
                pf.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
                pf.space_before, pf.space_after = Pt(0), Pt(10)
                pf.first_line_indent = Cm(1)
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if name != "Compact" else None
    for name, size in (("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 12)):
        set_font(st[name], size, True)
        st[name].font.italic = False
        hf = st[name].paragraph_format
        hf.space_before, hf.space_after = {"Heading 1": (Pt(0), Pt(30)), "Heading 2": (Pt(22), Pt(14)),
                                           "Heading 3": (Pt(14), Pt(10))}[name]
        hf.first_line_indent, hf.left_indent = Cm(0), Cm(0)
        hf.line_spacing = 1.0
        hf.keep_with_next = True
    st["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    st["Heading 1"].paragraph_format.page_break_before = True
    for name in ("Image Caption", "Table Caption", "Captioned Figure"):
        if name in [s.name for s in st]:
            set_font(st[name], 12, color=True)
            st[name].font.italic = False
            st[name].paragraph_format.space_before = Pt(8)
            st[name].paragraph_format.space_after = Pt(14)
            st[name].paragraph_format.first_line_indent = Cm(0)
            st[name].paragraph_format.line_spacing = 1.0
            st[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tsizes = pdf_table_sizes()
    for t in doc.tables:
        if table_number(t._tbl) is None:                      # symbols and abbreviations: a plain list
            plain_list(t)
            continue
        borders(t)
        tsize, wide = tsizes.get(table_number(t._tbl), (10, False))
        for row in t.rows:
            for c in row.cells:
                mark = c._tc.xpath("string(.)").strip()
                if mark in ("\u2713", "×"):
                    pr_ = c._tc.get_or_add_tcPr()
                    shd = pr_.find(qn("w:shd"))
                    if shd is None:
                        shd = OxmlElement("w:shd")
                        pr_.append(shd)
                    shd.set(qn("w:val"), "clear")
                    shd.set(qn("w:color"), "auto")
                    shd.set(qn("w:fill"), "DFF3DF" if mark == "\u2713" else "FBE0E0")
                    for cp in c.paragraphs:
                        cp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for row in t.rows:                                   # short labels of the first column on one line
            tc = row.cells[0]._tc
            if len(tc.xpath("string(.)")) <= 32:
                pr_ = tc.get_or_add_tcPr()
                if pr_.find(qn("w:noWrap")) is None:
                    pr_.append(OxmlElement("w:noWrap"))
        size = Pt(tsize)                                      # as the same table in the PDF
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.first_line_indent = Cm(0)
                    if p.paragraph_format.alignment in (None, WD_ALIGN_PARAGRAPH.JUSTIFY):
                        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for r in p.runs:
                        r.font.size = size
                    for mr in p._p.iter(qn("m:r")):           # equations in the cells at the same size
                        rpr = mr.find(qn("w:rPr"))
                        if rpr is None:
                            rpr = OxmlElement("w:rPr")
                            mr.insert(0 if mr.find(qn("m:rPr")) is None else 1, rpr)
                        for tag in ("w:sz", "w:szCs"):
                            old = rpr.find(qn(tag))
                            if old is not None:
                                rpr.remove(old)
                            e = OxmlElement(tag)
                            e.set(qn("w:val"), "20")
                            rpr.append(e)
        # full text width, small cell margins: fewer wrapped lines, closer to the LaTeX tables
        pr = t._tbl.tblPr
        tw = pr.find(qn("w:tblW"))
        if tw is None:
            tw = OxmlElement("w:tblW")
            pr.append(tw)
        tw.set(qn("w:type"), "pct" if wide else "auto")      # full width or as wide as the contents (as LaTeX)
        tw.set(qn("w:w"), "5000" if wide else "0")
        lay = pr.find(qn("w:tblLayout"))
        if lay is None:
            lay = OxmlElement("w:tblLayout")
            pr.append(lay)
        lay.set(qn("w:type"), "autofit")
        for tc in t._tbl.iter(qn("w:tcW")):
            tc.set(qn("w:type"), "auto")
            tc.set(qn("w:w"), "0")
        mar = pr.find(qn("w:tblCellMar"))
        if mar is not None:
            pr.remove(mar)
        mar = OxmlElement("w:tblCellMar")
        for side, v in (("top", 40), ("left", 100), ("bottom", 40), ("right", 100)):
            e = OxmlElement("w:%s" % side)
            e.set(qn("w:w"), str(v))
            e.set(qn("w:type"), "dxa")
            mar.append(e)
        pr.append(mar)
    # references as in the PDF: label hanging in front, single spacing, a gap between entries
    for p in doc.paragraphs:
        if re.match(r"^\[\d+\] ", p.text):
            pf = p.paragraph_format
            pf.left_indent, pf.first_line_indent = Cm(0.75), Cm(-0.75)
            pf.line_spacing, pf.space_before, pf.space_after = 1.0, Pt(0), Pt(10)
            pf.tab_stops.add_tab_stop(Cm(0.75))
            for r in p.runs:
                if "] " in r.text:
                    r.text = r.text.replace("] ", "]\t", 1)
                    break
    for p in doc.paragraphs:
        if p.text.strip() in ("Symbols", "Abbreviations"):
            p.paragraph_format.first_line_indent = Cm(1)
    # list items close together, as in the PDF (2 pt between items)
    paras = doc.paragraphs
    for k, p in enumerate(paras):
        if p._p.find(qn("w:pPr") + "/" + qn("w:numPr")) is not None:
            pf = p.paragraph_format
            pf.line_spacing, pf.line_spacing_rule = Pt(17.9), WD_LINE_SPACING.AT_LEAST
            pf.space_before = Pt(0)
            last = k + 1 >= len(paras) or paras[k + 1]._p.find(qn("w:pPr") + "/" + qn("w:numPr")) is None
            pf.space_after = Pt(10 if last else 2)
    for t in doc.tables:
        prev = t._tbl.getprevious()
        if prev is not None and prev.tag == qn("w:p"):
            sty = prev.find(qn("w:pPr") + "/" + qn("w:pStyle"))
            if sty is not None and sty.get(qn("w:val")) in ("TableCaption", "Table Caption"):
                t._tbl.addnext(prev)
    for p in doc.paragraphs:
        if p.text.strip() == "TOCMARKER":
            p.text = ""
            h = p.insert_paragraph_before("TABLE OF CONTENTS", style="Heading 1")
            toc_field(p)
            # lists of figures and tables: Word tables of contents built from the caption styles
            nxt = next(q for q in doc.paragraphs if q.style.name == "Heading 1" and q.text.startswith("LIST OF SYMBOLS"))
            for title, style in (("LIST OF FIGURES", "Image Caption"), ("LIST OF TABLES", "Table Caption")):
                nxt.insert_paragraph_before(title, style="Heading 1")
                toc_field(nxt.insert_paragraph_before(), 'TOC '+chr(92)+'h '+chr(92)+'z '+chr(92)+'t "%s,9"' % style)    # level 9: own style
        if any(r._r.find(qn("w:drawing")) is not None for r in p.runs):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    approval_page(doc)
    # ---- three sections: title page (no number), front matter (i, ii, ...), chapters (1, 2, ...)
    end_title = title_page(doc, tex)
    section_break(doc, end_title)
    heads = [p for p in doc.paragraphs if p.style.name == "Heading 1"]
    heads[0].paragraph_format.page_break_before = False          # ABSTRACT: the section already starts a page
    ch1 = next(p for p in heads if p.text.startswith("CHAPTER ONE"))
    ch1.paragraph_format.page_break_before = False
    section_break(doc, ch1.insert_paragraph_before())
    secs = doc.sections
    no_page_number(secs[0])
    page_numbers(secs[1], "upperRoman", start=2)      # the title page counts as page i
    page_numbers(secs[2], "decimal")
    s = doc.settings.element
    compat = s.find(qn("w:compat"))
    if compat is None:
        compat = OxmlElement("w:compat")
        s.append(compat)
    if compat.find(qn("w:doNotExpandShiftReturn")) is None:
        compat.insert(0, OxmlElement("w:doNotExpandShiftReturn"))
    if s.find(qn("w:autoHyphenation")) is None:              # words hyphenated at line ends, as in LaTeX
        hy = OxmlElement("w:autoHyphenation")
        compat.addprevious(hy)
    u = OxmlElement("w:updateFields")
    u.set(qn("w:val"), "true")
    s.append(u)
    doc.save(path)


def main():
    tex = open(os.path.join(REP, "main.tex"), encoding="utf-8").read()
    labels, cites = aux_numbers(tex)
    body = body_for_pandoc(tex, labels, cites)
    src = "\\documentclass{article}\n\\usepackage{amsmath,amssymb,graphicx,multirow}\n\\begin{document}\n%s\n\\end{document}\n" % body
    tmp = os.path.join(tempfile.gettempdir(), "dsdr_word.tex")
    open(tmp, "w", encoding="utf-8").write(src)
    try:
        pypandoc.convert_file(tmp, "docx", format="latex", outputfile=OUT,
                              extra_args=["--resource-path=%s" % FIGS])
    except PermissionError:
        raise SystemExit("close DSDR_Report.docx in Word and run again")
    polish(OUT, tex)
    # page breaks at the same places as in the LaTeX PDF
    pdf = os.path.join(REP, "DSDR_Report.pdf")
    if os.path.exists(pdf) and os.path.getmtime(pdf) >= os.path.getmtime(os.path.join(REP, "main.tex")):
        import word_page_match
        doc = Document(OUT)
        log = []
        word_page_match.match(doc, pdf, log)
        doc.save(OUT)
        front = word_page_match.front_breaks(pdf)
        print("\n".join(log).encode("ascii", "replace").decode())
    else:
        print("DSDR_Report.pdf is older than main.tex: build the PDF first (build_report_pdf.py) to match the pages")
        front = []
    update_in_word(OUT, front)
    print("WORD REPORT:", OUT)


def update_in_word(path, front=()):
    """fill the table of contents with Word itself (if Word is installed); otherwise Word asks on opening.
    front: [(list 1/2/3, entry text)] entries that start a new page, as in the PDF"""
    brk = "".join(
        "foreach ($q in $d.TablesOfContents.Item(%d).Range.Paragraphs) { if ($q.Range.Text.Trim().StartsWith('%s')) "
        "{ $q.Format.PageBreakBefore = -1; break } }; " % (n, txt.replace("'", "''")) for n, txt in front)
    ps = ("$w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0; "
          "try { $d = $w.Documents.Open('DOCPATH', $false, $false); "
          # compact entries in the contents and the lists of figures and tables (Word's built-in styles
          # toc 1-3 = -20..-22, table of figures = -36; 5 = multiple line spacing, 13.8 pt = 1.15 lines)
          "foreach ($k in -20,-21,-22,-36) { $f = $d.Styles.Item($k).ParagraphFormat; $f.LineSpacingRule = 5; "
          "$f.LineSpacing = 12; $f.SpaceAfter = 2; $f.SpaceBefore = 0; $f.Alignment = 0 }; "
          "$t1 = $d.Styles.Item(-20); $t1.Font.Bold = -1; $t1.ParagraphFormat.SpaceBefore = 9; "
          "$d.Styles.Item(-21).ParagraphFormat.LeftIndent = 14; $d.Styles.Item(-22).ParagraphFormat.LeftIndent = 42; "
          # lists of figures and tables (TOC level 9): plain entries, the text hanging after the number
          "$t9 = $d.Styles.Item(-28); $t9.Font.Bold = 0; $f = $t9.ParagraphFormat; $f.LeftIndent = 62; "
          "$f.FirstLineIndent = -62; $f.SpaceBefore = 0; $f.SpaceAfter = 3; $f.LineSpacingRule = 0; $f.Alignment = 0; "
          "foreach ($t in $d.TablesOfContents) { $t.Update() }; "
          # the empty paragraph that ends each list is made 1 pt high, so that it never spills onto a page
          # of its own when a list fills its last page exactly
          "foreach ($t in $d.TablesOfContents) { $e = $t.Range.End; $q = $d.Range($e, $e).Paragraphs.Item(1); "
          "$q.Range.Font.Size = 1; $q.SpaceAfter = 0; $q.SpaceBefore = 0; $q.LineSpacingRule = 4; $q.LineSpacing = 1 }; "
          # page breaks inside the lists where the PDF starts a new page, then refresh the page numbers
          "$rt = $d.PageSetup.PageWidth - $d.PageSetup.LeftMargin - $d.PageSetup.RightMargin; "
          "foreach ($q in $d.TablesOfContents.Item(1).Range.Paragraphs) { if ($q.Style.NameLocal -eq $d.Styles.Item(-20).NameLocal) "
          "{ $q.TabStops.ClearAll(); $null = $q.TabStops.Add($rt, 2, 0) } }; "
          "BREAKS"
          "foreach ($t in $d.TablesOfContents) { $t.UpdatePageNumbers() }; "
          "$d.Save(); $d.Close() } finally { $w.Quit() }")
    ps = ps.replace("DOCPATH", path.replace("'", "''")).replace("BREAKS", brk)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    if r.returncode:
        print("table of contents not updated (Word not available); Word will ask to update it on opening")
        print(r.stderr[-800:])


if __name__ == "__main__":
    main()
