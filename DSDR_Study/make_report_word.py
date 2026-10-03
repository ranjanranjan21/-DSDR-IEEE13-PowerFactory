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
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
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
            block = replace_cmd(block, "caption", lambda c, n=num: BS + "caption{%s %s: %s}" % (word, n, c))
            out += [s[pos:m.start()], "\\begin{%s}" % kind, block]
            pos = end
        out.append(s[pos:])
        s = "".join(out)
    env("figure", "Figure")
    env("table", "Table")
    # ---- equation numbers: every equation environment is numbered in turn, as in LaTeX; the number is
    #      written next to the equation because Word equations have no \tag
    count = [0]

    def eqn(m):
        count[0] += 1
        body = re.sub(r"\\label\{[^}]*\}", "", m.group(1)).strip()
        return "\\begin{equation*}%s\\qquad\\qquad(%d)\\end{equation*}" % (body, count[0])

    s = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", eqn, s, flags=re.S)
    s = re.sub(r"\\tag\{([^}]*)\}", lambda m: "\\qquad(%s)" % m.group(1), s)
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


def toc_field(paragraph):
    run = paragraph.add_run()
    for kind, text in (("begin", None), (None, 'TOC \\o "1-3" \\h \\z \\u'), ("separate", None), (None, None), ("end", None)):
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
    tp = tex[tex.index("\\begin{titlepage}"):tex.index("\\end{titlepage}")]
    title = re.search(r"\\large\\bfseries (An Adaptive.*?)\\par", tp, re.S).group(1)
    title = " ".join(title.replace("\\\\", " ").split())
    first = doc.paragraphs[0]
    lines = [("TRIBHUVAN UNIVERSITY", 14, True, False), ("INSTITUTE OF ENGINEERING", 12, True, False),
             ("PULCHOWK CAMPUS", 12, True, False), ("LOGO", 0, False, False), ("PROJECT REPORT", 12, True, False),
             ("on", 12, False, True), (title, 15, True, False), ("Submitted by", 12, True, False),
             ("Jhala Nath Kafle", 12, True, False), ("Roll No. 081MSPSE009", 12, False, False),
             ("A report submitted in partial fulfillment of the requirements for the 3rd semester project of the "
              "Master's Degree in Power System Engineering", 11, False, True),
             ("Department of Electrical Engineering", 12, False, False)]
    date = re.search(r"Department of Electrical Engineering\\par\s*(.*?)\\par", tp).group(1)
    lines.append((date, 12, False, False))
    for text, size, bold, ital in lines:
        p = first.insert_paragraph_before()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(10)
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


def page_numbers(section, fmt):
    """centred page number in the footer, counting from 1 in this section (fmt: lowerRoman, decimal)"""
    pg = section._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        section._sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt)
    pg.set(qn("w:start"), "1")
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
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
    section.footer.is_linked_to_previous = False
    for p in section.footer.paragraphs:
        p.text = ""


def polish(path, tex):
    doc = Document(path)
    for sec in doc.sections:
        sec.left_margin, sec.right_margin = Cm(3.05), Cm(2.54)
        sec.top_margin, sec.bottom_margin = Cm(2.54), Cm(2.54)
    st = doc.styles
    for name in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if name in [s.name for s in st]:
            set_font(st[name], 12, color=False)
            st[name].paragraph_format.line_spacing = 1.5 if name != "Compact" else 1.0
            st[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if name != "Compact" else None
    for name, size in (("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 12)):
        set_font(st[name], size, True)
        st[name].font.italic = False
    st["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    st["Heading 1"].paragraph_format.page_break_before = True
    for name in ("Image Caption", "Table Caption", "Captioned Figure"):
        if name in [s.name for s in st]:
            set_font(st[name], 11, color=True)
            st[name].font.italic = False
            st[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for t in doc.tables:
        borders(t)
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.alignment = None
                    for r in p.runs:
                        r.font.size = Pt(10)
    for p in doc.paragraphs:
        if p.text.strip() == "TOCMARKER":
            p.text = ""
            h = p.insert_paragraph_before("TABLE OF CONTENTS", style="Heading 1")
            toc_field(p)
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
    page_numbers(secs[1], "lowerRoman")
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
    update_in_word(OUT)
    print("WORD REPORT:", OUT)


def update_in_word(path):
    """fill the table of contents with Word itself (if Word is installed); otherwise Word asks on opening"""
    ps = ("$w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0; "
          "try { $d = $w.Documents.Open('%s', $false, $false); foreach ($t in $d.TablesOfContents) { $t.Update() }; "
          "$d.Save(); $d.Close() } finally { $w.Quit() }" % path.replace("'", "''"))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    if r.returncode:
        print("table of contents not updated (Word not available); Word will ask to update it on opening")


if __name__ == "__main__":
    main()
