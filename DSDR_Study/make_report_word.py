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
    s = s.replace("$\\checkmark$", "\u2713").replace("$\\times$", "\u2717")
    s = re.sub(r"\\ok\b", "\u2713", s)
    s = re.sub(r"\\no\b", "\u2717", s)
    s = re.sub(r"\\ohm(\{\})?", "\u2009\u03a9", s)
    s = re.sub(r"\\PF(\{\})?", "PowerFactory", s)
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
            return BS + "subsection*{%d.%d %s}" % (chap[0], chap[1], m.group(2))
        chap[2] += 1
        return BS + "subsubsection*{%d.%d.%d %s}" % (chap[0], chap[1], chap[2], m.group(2))

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
    lines = [("LOGO", 0, False, False, 24), ("TRIBHUVAN UNIVERSITY", 14, False, False, 4),
             ("INSTITUTE OF ENGINEERING", 16, True, False, 4), ("PULCHOWK CAMPUS", 14, True, False, 40),
             (title, 14, True, True, 40), ("BY:", 12, False, False, 4), ("Jhala Nath Kafle", 12, True, True, 4),
             ("(081MSPSE009)", 12, False, False, 90),
             ("A PROJECT REPORT SUBMITTED IN PARTIAL FULFILLMENT OF THE REQUIREMENTS FOR THE MASTER'S DEGREE IN "
              "POWER SYSTEM ENGINEERING", 12, False, False, 10),
             ("DEPARTMENT OF ELECTRICAL ENGINEERING", 12, False, False, 30), ("OCTOBER, 2026", 12, False, True, 0)]
    for text, size, bold, ital, after in lines:
        p = first.insert_paragraph_before()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(after)
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
    """page number at the top right (header), fmt: lowerRoman or decimal; start: first number"""
    pg = section._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        section._sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt)
    pg.set(qn("w:start"), str(start))
    section.footer.is_linked_to_previous = False
    for fp in section.footer.paragraphs:
        fp.text = ""
    header = section.header
    header.is_linked_to_previous = False
    p = header.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
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


def polish(path, tex):
    doc = Document(path)
    for sec in doc.sections:
        sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)      # A4
        sec.left_margin, sec.right_margin = Cm(3.5), Cm(2.0)
        sec.top_margin, sec.bottom_margin = Cm(3.5), Cm(2.0)
        sec.header_distance = Cm(2.0)
    st = doc.styles
    for name in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if name in [s.name for s in st]:
            set_font(st[name], 12, color=False)
            pf = st[name].paragraph_format
            if name == "Compact":
                pf.line_spacing = 1.0
            else:                                      # as the LaTeX report: one-and-a-half spacing, 8 pt parskip
                pf.line_spacing = Pt(17)
                pf.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
                pf.space_before, pf.space_after = Pt(0), Pt(6)
                pf.first_line_indent = Cm(1)
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if name != "Compact" else None
    for name, size in (("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 12)):
        set_font(st[name], size, True)
        st[name].font.italic = False
        st[name].paragraph_format.space_before = Pt(10 if name != "Heading 1" else 0)
        st[name].paragraph_format.space_after = Pt(4 if name != "Heading 1" else 12)
    st["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    st["Heading 1"].paragraph_format.page_break_before = True
    for name in ("Image Caption", "Table Caption", "Captioned Figure"):
        if name in [s.name for s in st]:
            set_font(st[name], 12, color=True)
            st[name].font.italic = False
            st[name].paragraph_format.space_before = Pt(3)
            st[name].paragraph_format.space_after = Pt(6)
            st[name].paragraph_format.line_spacing = 1.0
            st[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for t in doc.tables:
        borders(t)
        size = Pt(8) if len(t.columns) >= 8 else Pt(8.5)      # wide tables at the guideline minimum of 8 pt
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.alignment = None
                    for r in p.runs:
                        r.font.size = size
        # full text width, small cell margins: fewer wrapped lines, closer to the LaTeX tables
        pr = t._tbl.tblPr
        tw = pr.find(qn("w:tblW"))
        if tw is None:
            tw = OxmlElement("w:tblW")
            pr.append(tw)
        tw.set(qn("w:type"), "pct")
        tw.set(qn("w:w"), "5000")
        mar = pr.find(qn("w:tblCellMar"))
        if mar is not None:
            pr.remove(mar)
        mar = OxmlElement("w:tblCellMar")
        for side, v in (("top", 15), ("left", 60), ("bottom", 15), ("right", 60)):
            e = OxmlElement("w:%s" % side)
            e.set(qn("w:w"), str(v))
            e.set(qn("w:type"), "dxa")
            mar.append(e)
        pr.append(mar)
    for p in doc.paragraphs:
        if p.text.strip() == "TOCMARKER":
            p.text = ""
            h = p.insert_paragraph_before("TABLE OF CONTENTS", style="Heading 1")
            toc_field(p)
            # lists of figures and tables: Word tables of contents built from the caption styles
            nxt = next(q for q in doc.paragraphs if q.style.name == "Heading 1" and q.text.startswith("LIST OF SYMBOLS"))
            for title, style in (("LIST OF FIGURES", "Image Caption"), ("LIST OF TABLES", "Table Caption")):
                nxt.insert_paragraph_before(title, style="Heading 1")
                toc_field(nxt.insert_paragraph_before(), 'TOC '+chr(92)+'h '+chr(92)+'z '+chr(92)+'t "%s,1"' % style)
        if any(r._r.find(qn("w:drawing")) is not None for r in p.runs):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
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
    page_numbers(secs[1], "lowerRoman", start=2)      # the title page counts as page i
    page_numbers(secs[2], "decimal")
    s = doc.settings.element
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
          "foreach ($t in $d.TablesOfContents) { $t.Update() }; "
          # the empty paragraph that ends each list is made 1 pt high, so that it never spills onto a page
          # of its own when a list fills its last page exactly
          "foreach ($t in $d.TablesOfContents) { $e = $t.Range.End; $q = $d.Range($e, $e).Paragraphs.Item(1); "
          "$q.Range.Font.Size = 1; $q.SpaceAfter = 0; $q.SpaceBefore = 0; $q.LineSpacingRule = 4; $q.LineSpacing = 1 }; "
          # page breaks inside the lists where the PDF starts a new page, then refresh the page numbers
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
