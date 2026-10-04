"""
Page breaks of the Word report at the same places as the LaTeX PDF.

For every page of the PDF from Chapter One on, the first line of text on that page is located in the Word
document and a page break is put in front of it:
  - at the start of a paragraph or heading: "page break before" on that paragraph;
  - inside a paragraph: a page-break run at that word;
  - a page that starts with a figure or a table: the break goes in front of the figure (picture paragraph)
    or in front of the table's caption (Word puts table captions above the table).
Used by make_report_word.py after the document has been built.
"""

import copy
import re
import unicodedata

import fitz
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

W_P, W_TBL = qn("w:p"), qn("w:tbl")


PAGE_NO = re.compile(r"^\s*(\d+|[ivxlcIVXLC]+)\s*$")


def page_text(page):
    """text of a page without its page number (top or bottom)"""
    lines = [x for x in page.get_text().strip().splitlines() if x.strip()]
    while lines and PAGE_NO.match(lines[0]):
        lines = lines[1:]
    while lines and PAGE_NO.match(lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines)


def norm(text):
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"[^a-z0-9]", "", text)


# ---------------------------------------------------------------------------------------------
# PDF side: first content of each body page
# ---------------------------------------------------------------------------------------------
def pdf_pages(pdf_path):
    """[(page index, kind, text)] for the pages from 'CHAPTER ONE' on.
    kind = 'text' (first text line), 'figure' (the page starts with a picture; text = its caption)
    or 'table' (the page starts with a table; text = its caption)."""
    doc = fitz.open(pdf_path)
    start = next(i for i, p in enumerate(doc) if page_text(p).startswith("LIST OF SYMBOLS"))
    out = []
    for i in range(start + 1, len(doc)):
        if page_text(doc[i]).startswith("CHAPTER ONE"):           # starts a new section anyway
            continue
        page = doc[i]
        h = page.rect.height
        blocks = [b for b in page.get_text("dict")["blocks"] if b["bbox"][1] < h - 60      # drop the page number
                  and not (b["bbox"][3] < 90 and b["type"] == 0 and
                           PAGE_NO.match("".join(sp["text"] for ln in b["lines"] for sp in ln["spans"])))]
        blocks.sort(key=lambda b: (round(b["bbox"][1]), b["bbox"][0]))
        if not blocks:
            continue
        lines = []
        for b in blocks:
            if b["type"] == 1:
                lines.append(("IMG", b["bbox"]))
                continue
            for ln in b["lines"]:
                t = "".join(sp["text"] for sp in ln["spans"]).strip()
                if t and not (ln["bbox"][3] < 90 and PAGE_NO.match(t)):      # skip the page number at the top
                    lines.append((t, ln["bbox"]))
        caps = [t for t, _ in lines if t != "IMG" and re.match(r"^(Figure|Table) (\d+|[A-Z])(\.\d+)?[: ]", t)]
        first = lines[0][0]
        if first == "IMG":
            cap = next((t for t, _ in lines if t != "IMG" and t.startswith("Figure")), None)
            out.append((i, "figure", cap))
            continue
        # a table at the top: its cells come before any caption and are short pieces of text
        top_words = " ".join(t for t, _ in lines[:3])
        tab_cap = next((t for t in caps if t.startswith("Table")), None)
        if tab_cap and _starts_with_table(lines, tab_cap):
            out.append((i, "table", tab_cap))
            continue
        # a section number extracted as its own line ("4.5" / "Recloser Model"): join it with the title
        if re.fullmatch(r"\d+(\.\d+)+", first) and len(lines) > 1 and lines[1][0] != "IMG":
            first = first + " " + lines[1][0]
            lines = [(first, lines[0][1])] + lines[2:]
        if len(first) < 8 and len(lines) > 1 and lines[1][0] != "IMG" and _clean(lines[1][0]) \
                and not re.search(r"[\u2200-\u23ff]", first):
            first = first + " " + lines[1][0]
            lines = [(first, lines[0][1])] + lines[2:]
        # a page that starts with an equation (garbled text): take the first clean line, break before the equation
        if not _clean(first):
            num = next((t for t, _ in lines if re.fullmatch(r"\(((\d+|[A-Z])\.)?\d+\)", t.strip())), None)
            out.append((i, "equation", num.strip().strip("()") if num else None))
            continue
        # first text line, extended with the next line when it is short
        key = first
        k = 1
        while len(norm(key)) < 15 and k < len(lines):
            if lines[k][0] != "IMG":
                key += " " + lines[k][0]
            k += 1
        out.append((i, "text", key))
    return out


def _clean(t):
    """ordinary text, not a piece of a formula"""
    if re.search(r"[∀-⏿]", t):            # bracket pieces and operators of a displayed formula
        return False
    letters = sum(c.isalpha() for c in t)
    return letters >= 4 and letters >= 0.35 * len(t.replace(" ", ""))


def _starts_with_table(lines, tab_cap):
    """True when the lines before the table caption look like table cells (many short pieces)."""
    before = []
    for t, _ in lines:
        if t == tab_cap:
            break
        before.append(t)
    if len(before) < 4:
        return False
    first3 = [t for t in before[:3] if t != "IMG"]
    if re.match(r"^(\d+(\.\d+)+|CHAPTER|APPENDIX)\b", before[0]):     # a heading, not a table cell
        return False
    return all(len(t) < 45 for t in first3)


# ---------------------------------------------------------------------------------------------
# Word side
# ---------------------------------------------------------------------------------------------
def body_blocks(doc):
    """[(element, kind, normalised text)] in document order"""
    out = []
    for el in doc.element.body.iterchildren():
        if el.tag == W_P:
            out.append((el, "p", norm("".join(t.text or "" for t in el.iter(qn("w:t"))))))
        elif el.tag == W_TBL:
            out.append((el, "tbl", norm("".join(t.text or "" for t in el.iter(qn("w:t"))))))
    return out


def style_of(p):
    ps = p.find(qn("w:pPr"))
    st = ps.find(qn("w:pStyle")) if ps is not None else None
    return st.get(qn("w:val")) if st is not None else ""


def _shrink_empty_before(el):
    """an empty paragraph just before a forced break would spill onto a page of its own: make it 1 pt high"""
    prev = el.getprevious()
    while prev is not None and prev.tag == W_P and not "".join(t.text or "" for t in prev.iter(qn("w:t"))).strip() \
            and prev.find(".//" + qn("w:drawing")) is None and prev.find(".//" + qn("m:oMath")) is None:
        ppr = prev.find(qn("w:pPr"))
        if ppr is None:
            ppr = OxmlElement("w:pPr")
            prev.insert(0, ppr)
        for tag in ("w:spacing", "w:rPr"):
            old = ppr.find(qn(tag))
            if old is not None:
                ppr.remove(old)
        sp = OxmlElement("w:spacing")
        sp.set(qn("w:before"), "0")
        sp.set(qn("w:after"), "0")
        sp.set(qn("w:line"), "20")
        sp.set(qn("w:lineRule"), "exact")
        ppr.append(sp)
        rpr = OxmlElement("w:rPr")
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), "2")
        rpr.append(sz)
        ppr.append(rpr)
        prev = prev.getprevious()


def break_before(p):
    _shrink_empty_before(p)
    ppr = p.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr")
        p.insert(0, ppr)
    if ppr.find(qn("w:pageBreakBefore")) is None:
        # schema order: pStyle, keepNext, keepLines, pageBreakBefore, ... (Word ignores it elsewhere)
        pb = OxmlElement("w:pageBreakBefore")
        prev = [c for c in ppr if c.tag in (qn("w:pStyle"), qn("w:keepNext"), qn("w:keepLines"))]
        if prev:
            prev[-1].addnext(pb)
        else:
            ppr.insert(0, pb)


def break_inside(p, n_chars):
    """page break inside paragraph p after n_chars normalised characters (moved to the next word start)"""
    count = 0
    for t in list(p.iter(qn("w:t"))):
        raw = t.text or ""
        for j, ch in enumerate(raw):
            if norm(ch):
                if count == n_chars:
                    # move back to the start of this word (break before the word)
                    k = j
                    while k > 0 and raw[k - 1].isalnum():
                        k -= 1
                    _split_run(t, k)
                    return True
                count += 1
    return False


def _split_run(t, k):
    r = t.getparent()
    before, after = (t.text or "")[:k], (t.text or "")[k:]
    br_run = OxmlElement("w:r")
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    br_run.append(br)
    if not before:                                  # break before the whole run
        r.addprevious(br_run)
        return
    new_r = copy.deepcopy(r)
    for tt in new_r.iter(qn("w:t")):
        tt.text = after
        tt.set(qn("xml:space"), "preserve")
    t.text = before
    t.set(qn("xml:space"), "preserve")
    r.addnext(br_run)
    br_run.addnext(new_r)


def front_breaks(pdf_path):
    """Entries of the table of contents and the lists of figures and tables that start a new page in the PDF:
    [(list number 1/2/3, text the entry starts with)]"""
    doc = fitz.open(pdf_path)
    body = next(i for i, p in enumerate(doc) if page_text(p).startswith("CHAPTER ONE"))
    current, out = 0, []
    for i in range(1, body):
        lines = [x.strip() for x in page_text(doc[i]).splitlines() if x.strip()]
        if not lines:
            continue
        head = lines[0]
        if head.startswith("TABLE OF CONTENTS"):
            current = 1
            continue
        if head.startswith("LIST OF FIGURES"):
            current = 2
            continue
        if head.startswith("LIST OF TABLES"):
            current = 3
            continue
        if head.startswith("LIST OF"):
            current = 0
            continue
        if current == 1:
            out.append((1, head))
        elif current in (2, 3):
            m = re.match(r"(Figure|Table) ([A-Z]|\d+)\.\d+", head)
            if m:
                out.append((current, m.group(0) + " "))
    return out


def size_images(doc, pdf_path):
    """every picture in Word at the size it has in the LaTeX PDF (same order in both)"""
    from docx.shared import Pt
    pdf = fitz.open(pdf_path)
    boxes = [b["bbox"] for p in pdf for b in p.get_text("dict")["blocks"] if b["type"] == 1]
    shapes = doc.inline_shapes
    if len(boxes) != len(shapes):
        return False
    for sh, (x0, y0, x1, y1) in zip(shapes, boxes):
        sh.width, sh.height = Pt(x1 - x0), Pt(y1 - y0)
    return True


def match(doc, pdf_path, log=None):
    if log is not None:
        log.append("pictures sized as in the PDF: %s" % size_images(doc, pdf_path))
    pages = pdf_pages(pdf_path)
    blocks = body_blocks(doc)
    start = next(k for k, (el, kind, txt) in enumerate(blocks) if txt.startswith("listofsymbols"))
    # one string of the whole body from Chapter One on, with the block of every character
    text, owner, offset = [], [], []
    for k in range(start, len(blocks)):
        txt = blocks[k][2]
        text.append(txt)
        owner += [k] * len(txt)
        offset += list(range(len(txt)))
    full = "".join(text)
    pos, done, missed = len(blocks[start][2]), 0, []
    eqs = [k for k in range(start, len(blocks)) if blocks[k][1] == "p"
           and blocks[k][0].find(".//" + qn("m:oMathPara")) is not None]
    for page, kind, line in pages:
        if kind == "equation":                       # the page starts with display equation (<line>)
            tag = "(%s)" % line if line else None
            hit_eq = None
            for m in eqs:
                txt = "".join(t.text or "" for t in blocks[m][0].iter(qn("m:t")))
                if tag and tag in txt.replace(" ", ""):
                    hit_eq = m
                    break
            if hit_eq is not None:
                break_before(blocks[hit_eq][0])
                done += 1
                pos = max(pos, sum(len(blocks[k][2]) for k in range(start, hit_eq)))
            else:
                missed.append((page, kind, str(line)))
            continue
        if line is None:
            missed.append((page, kind, "no caption"))
            continue
        variants = [line, re.sub(r"^\s*\d+\.\s+", "", line), re.sub(r"^\W+", "", line)]
        hit = -1
        for v in variants:
            key = norm(v)[:20 if kind in ("figure", "table") else 30]
            if len(key) < 8:
                continue
            hit = full.find(key, pos)
            if hit >= 0:
                break
        if hit < 0:
            missed.append((page, kind, line[:50]))
            continue
        k, j = owner[hit], offset[hit]
        el, bk, _ = blocks[k]
        if kind == "figure":                         # picture paragraph is just before its caption
            target = blocks[k - 1][0] if blocks[k - 1][1] == "p" else el
            break_before(target)
        elif kind == "after_math":
            m = k - 1
            while m > start and blocks[m][0].find(".//" + qn("m:oMath")) is None and blocks[m][1] == "p" \
                    and not blocks[m][2]:
                m -= 1
            if blocks[m][0].find(".//" + qn("m:oMath")) is not None:
                break_before(blocks[m][0])
            else:
                missed.append((page, kind, line[:50]))
                continue
        elif kind == "table" and blocks[k - 1][1] == "tbl":     # caption below its table: break before the table
            break_before(blocks[k - 1][0].find(".//" + W_P))
        elif bk == "tbl":                            # the table's caption sits above it in Word
            prev = blocks[k - 1][0]
            break_before(prev if prev.tag == W_P and "caption" in style_of(prev).lower() else el) \
                if prev.tag == W_P else None
        elif j == 0:
            break_before(el)
        elif not break_inside(el, j):
            missed.append((page, kind, line[:50]))
            continue
        done += 1
        pos = hit + 1
    if log is not None:
        log.append("page breaks matched to the PDF: %d of %d pages" % (done, len(pages)))
        for m in missed:
            log.append("  not matched: PDF page %d (%s) %s" % m)
    return done, missed
