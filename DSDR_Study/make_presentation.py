"""
Final presentation: keeps the title slide and the design of the earlier presentation (navy bar, Aptos
fonts) and fills it with the results of this study, in the order asked by the department:
Title, Introduction, Objectives, Scope, Methodology, Results, Conclusions, References, Appendix
(comparison with the reference paper).

Input : Presentation and report/DSDR_Final_Project_Presentation final.pptx  (design and title slide)
        report/figures/*.png                                                (figures of the report)
Output: Presentation and report/DSDR_Final_Presentation.pptx
"""

import copy
import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FOLDER = os.path.join(ROOT, "Presentation and report")
SRC = os.path.join(FOLDER, "DSDR_Final_Project_Presentation final.pptx")
OUT = os.path.join(FOLDER, "DSDR_Final_Presentation.pptx")
FIGS = os.path.join(HERE, "report", "figures")

NAVY = RGBColor(0x1B, 0x37, 0x55)
INK = RGBColor(0x26, 0x2D, 0x34)
GREY = RGBColor(0x6B, 0x72, 0x7A)
LIGHT = RGBColor(0xEE, 0xF4, 0xF9)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
RED = RGBColor(0xC6, 0x28, 0x28)
W, H = 12192000, 6858000
IN = 914400


def emu(x):
    return Emu(int(x * IN))


# ---------------------------------------------------------------------------------------------
# drawing helpers (same look as the earlier slides)
# ---------------------------------------------------------------------------------------------
def new_slide(prs, title):
    s = prs.slides.add_slide(prs.slide_layouts[6])            # Blank
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Emu(91440))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tb = s.shapes.add_textbox(Emu(594360), Emu(274320), Emu(10972800), Emu(566928))
    r = tb.text_frame.paragraphs[0].add_run()
    r.text = title
    r.font.size, r.font.bold, r.font.name = Pt(27), True, "Aptos Display"
    r.font.color.rgb = NAVY
    return s


def text(s, x, y, w, h, items, size=17, bullet=True, color=INK, bold_first=False, space=8):
    """items: strings, or (string, level) tuples; '**x**' at the start makes that part bold"""
    tb = s.shapes.add_textbox(emu(x), emu(y), emu(w), emu(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for k, it in enumerate(items):
        t, lvl = (it, 0) if isinstance(it, str) else it
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.space_after = Pt(space)
        if bullet:
            pPr = p._p.get_or_add_pPr()
            ind = 342900 + 285750 * lvl
            pPr.set("marL", str(ind))
            pPr.set("indent", "-285750")
            bu = pPr.makeelement(qn("a:buChar"), {"char": "•" if lvl == 0 else "–"})
            pPr.append(bu)
        parts = t.split("**")
        for j, part in enumerate(parts):
            if not part:
                continue
            r = p.add_run()
            r.text = part
            r.font.size = Pt(size - 2 * lvl)
            r.font.name = "Aptos"
            r.font.color.rgb = color
            r.font.bold = (j % 2 == 1)
    return tb


def picture(s, name, x, y, w, h):
    """picture fitted into the box (x, y, w, h in inches), centred"""
    path = os.path.join(FIGS, name)
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    return s.shapes.add_picture(path, emu(x + (w - pw) / 2), emu(y + (h - ph) / 2), emu(pw), emu(ph))


def caption(s, x, y, w, t):
    tb = s.shapes.add_textbox(emu(x), emu(y), emu(w), emu(0.35))
    p = tb.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = t
    r.font.size, r.font.name, r.font.italic = Pt(12), "Aptos", True
    r.font.color.rgb = GREY


def _border(cell, color="808080", width=9525):
    tcPr = cell._tc.get_or_add_tcPr()
    for edge in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        old = tcPr.find(qn(edge))
        if old is not None:
            tcPr.remove(old)
        ln = tcPr.makeelement(qn(edge), {"w": str(width), "cap": "flat", "cmpd": "sng", "algn": "ctr"})
        fill = ln.makeelement(qn("a:solidFill"), {})
        clr = fill.makeelement(qn("a:srgbClr"), {"val": color})
        fill.append(clr)
        ln.append(fill)
        ln.append(ln.makeelement(qn("a:prstDash"), {"val": "solid"}))
        tcPr.insert(0, ln) if False else tcPr.append(ln)


def table(s, rows, x, y, w, widths, size=13, row_h=0.36, first_col_left=True, colors=None):
    """framed table; the first row is the header (bold, light fill)"""
    nr, nc = len(rows), len(rows[0])
    shp = s.shapes.add_table(nr, nc, emu(x), emu(y), emu(w), emu(row_h * nr))
    tbl = shp.table
    tblPr = tbl._tbl.tblPr
    for a in ("firstRow", "bandRow"):
        tblPr.set(a, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None:
        sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"          # "No Style, Table Grid"
    tot = float(sum(widths))
    for j, cw in enumerate(widths):
        tbl.columns[j].width = emu(w * cw / tot)
    for i, row in enumerate(rows):
        tbl.rows[i].height = emu(row_h)
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = emu(0.06)
            c.margin_top = c.margin_bottom = emu(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = LIGHT if i == 0 else RGBColor(0xFF, 0xFF, 0xFF)
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if (j == 0 and first_col_left) else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(val)
            r.font.size, r.font.name = Pt(size), "Aptos"
            r.font.bold = i == 0
            r.font.color.rgb = NAVY if i == 0 else INK
            if colors and (i, j) in colors:
                r.font.color.rgb = colors[(i, j)]
                r.font.bold = True
            _border(c)
    return shp


def card(s, x, y, w, h, head, body, head_color=NAVY):
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, emu(x), emu(y), emu(w), emu(h))
    b.adjustments[0] = 0.08
    b.fill.solid()
    b.fill.fore_color.rgb = LIGHT
    b.line.color.rgb = RGBColor(0x9D, 0xB4, 0xCF)
    tf = b.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = emu(0.12)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = head
    r.font.size, r.font.bold, r.font.name = Pt(18), True, "Aptos"
    r.font.color.rgb = head_color
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r = p2.add_run()
    r.text = body
    r.font.size, r.font.name = Pt(14), "Aptos"
    r.font.color.rgb = INK
    return b


def page_numbers(prs):
    n = len(prs.slides)
    for k, s in enumerate(prs.slides, 1):
        if k == 1:
            for sh in s.shapes:
                if sh.has_text_frame and "/" in sh.text_frame.text and len(sh.text_frame.text) <= 6:
                    sh.text_frame.paragraphs[0].runs[0].text = "%d/%d" % (k, n)
            continue
        tb = s.shapes.add_textbox(Emu(594360), Emu(6510528), Emu(10972800), Emu(164592))
        p = tb.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run()
        r.text = "%d/%d" % (k, n)
        r.font.size, r.font.name = Pt(9), "Aptos"
        r.font.color.rgb = GREY


# ---------------------------------------------------------------------------------------------
# speaker notes, one per slide, to be read aloud (about 9-10 minutes in total)
# ---------------------------------------------------------------------------------------------
NOTES = [
    # 1 title
    """Good afternoon. I am Jhala Nath Kafle, roll number 081MSPSE009. My project is an adaptive overcurrent
    protection scheme for dual-setting directional recloser and fuse coordination in distribution networks
    with distributed generation, implemented on the IEEE 13-node feeder in DIgSILENT PowerFactory.""",
    # 2 outline
    """I will cover the introduction, objectives, scope, methodology, results, conclusions and references.
    The comparison with the reference paper is in the appendix.""",
    # 3 background
    """In a fuse-saving scheme the recloser trips first on its fast curve, so a temporary fault clears and
    the fuse is saved. For a permanent fault the delayed curve lets the fuse blow and isolate only its lateral.
    In the graph the fast curve lies below the green fuse band and the delayed curve above it. This works only
    while the recloser and the fuse carry the same current, and a DG changes both the size and the direction
    of the fault current.""",
    # 4 problem
    """Without DG, recloser and fuse see the same current. With a DG, the fuse carries grid plus DG current,
    while the recloser sees only the grid part, and a mid-line recloser can even see reverse current. The fuse
    may then melt before the fast trip. The solution studied is the dual-setting directional recloser, or
    DSDR: the mid-line recloser R2 gets separate forward and reverse settings, chosen by the current
    direction. I implemented this in PowerFactory with real relay and fuse curves.""",
    # 5 objectives
    """The general objective was to build and validate a PowerFactory implementation of the DSDR method on
    the IEEE 13-node feeder, with and without DG. To reach it there are seven specific
    objectives: the model, load flow and short circuit, the settings, coordination without and
    with the DG, the dual setting of R2, a time-domain check, and the effect of DG penetration.""",
    # 6 scope
    """The study covers four fault types at twelve locations, which gives 39 node and fault-type cells,
    plus one EMT simulation and a penetration study. The limitations: some settings are not published and
    were chosen and documented; the CDG34 relay model is not directional, so two relay units are used; a zero
    margin is used; and only one DG location is studied.""",
    # 7 method
    """The method has three stages: A, the conventional design without DG, with pickup equal to 1.25 times
    the rated current; B, the same settings with the DG; and C, R2 as a DSDR. If coordination is lost, the
    time dial is revised first, and at the dial limit the fuse is made larger. The fuse must not melt before
    the fast trip, and must clear before the delayed trip.""",
    # 8 system
    """This is the PowerFactory model: a 4.16 kV feeder fed from a 115 kV grid, a 4.05 MVA synchronous
    generator at node 692, R1 a GE IAC77 relay at the feeder head, R2 a CDG34 relay on line 632 to 671, and
    A055C fuses on the laterals.""",
    # 9 settings
    """R1 has a pickup of 720 amperes and dials 0.5 and 10. R2 forward uses plugs of 300 and 600 amperes,
    the new reverse group 150 and 300 amperes. With the DG, the load current through R2 reverses to 252
    amperes, giving a reverse pickup of about 315 amperes. The dials were already at their limits, so the
    fuse sizes were revised as shown.""",
    # 10 without DG
    """The fault levels agree with the IEEE benchmark within about 2 percent. Without DG, 35 of 39 cells were
    coordinated, and all 39 after one fuse change. The figure shows R2's fast curve below both fuses and its
    delayed curve above them. With the DG, R2 carries 1.1 to 2 kiloamperes in reverse for faults upstream of
    it.""",
    # 11 conventional
    """With the DG and unchanged settings, coordination holds in only 24 of 39 cells. Losses are at 633,
    645, 646, the distributed load and 675: the fuse melts before the fast trip, and for some LG faults R2
    does not even pick up the reverse current.""",
    # 12 dsdr
    """With R2 as a DSDR and revised fuses, 38 of 39 cells are held. With the same fuses and a single
    setting only 31, so the dual setting itself restores seven cells, at 633, 645, 646 and the distributed
    load. Only the LG fault at 692 stays lost, at the limit of R2's dial range.""",
    # 13 case
    """One case in detail: a three-phase fault near 632, with 1777 amperes in reverse through R2. With the
    single setting R2 trips in 0.121 seconds but the fuse starts melting at 0.100 seconds: lost. With the
    reverse group R2 trips in 0.052 seconds: held. Only the setting group changed.""",
    # 14 sequence
    """As a second check I followed every fault in time. Above R2 the single setting holds 15 of 18 cells
    and the DSDR all 18; the restored cells are the LG faults at 633, 645 and 646. Below R2 the DG feeds the
    fault directly, so the setting of R2 makes no difference.""",
    # 15 emt
    """This EMT simulation is a line-to-line fault at 684 with conventional settings. Without DG the two fast
    shots use only 45 percent of the fuse's melting heat, and the fuse then clears the permanent fault. With
    the DG, current keeps flowing while R2 is open, and the fuse melts at 0.75 seconds, during the second
    fast shot.""",
    # 16 penetration
    """Seven models with the DG from 0 to 100 percent and fixed settings show the CTI, the fuse melting
    time minus the recloser fast time, falling: at 633 from plus 4 to minus 51 milliseconds, at 671 from 403
    to 75 milliseconds. The fuse carries grid plus DG current, the recloser only the grid share, so the fuse
    speeds up much faster.""",
    # 17 summary
    """In summary: 39 cells without DG, 24 with the DG, and 38 with the DSDR. PowerFactory's own relay and
    fuse models reproduced all 1896 operating times within 1.22 percent.""",
    # 18 conclusions
    """To conclude: the DG reduces coordination from 39 to 24 cells, and a dual-setting R2 with the fuse
    revision restores it to 38. The DSDR works in the zone between the grid and the DG, but needs the fuse
    revision, and faults below R2 remain a limit. Future work includes the 34-node feeder, a true directional
    element, practical margins and inverter-based DG.""",
    # 19 references
    """These are the main references; the method is from Yousaf and co-authors, 2022.""",
    # 20 appendix
    """Compared with the reference paper, load currents agree within 2 percent and the R1 worked example
    almost exactly. My fault levels are lower because I validated against the IEEE benchmark. The paper
    reports 30 and 39 coordinated cells, I obtained 24 and 38. The main finding is reproduced.""",
    # 21 appendix penetration
    """Both studies show the margin decreasing with DG penetration; where it turns negative depends on
    settings the paper does not publish.""",
    # 22 close
    """Thank you for your attention. I am happy to take your questions.""",
]


def objectives_slide(prs):
    """two labelled blocks: the general objective, then the numbered specific objectives"""
    s = new_slide(prs, "2. Objectives")

    def block(y, h, label, color):
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(0.75), emu(y), emu(0.09), emu(h))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()
        tb = s.shapes.add_textbox(emu(1.0), emu(y - 0.05), emu(8), emu(0.45))
        r = tb.text_frame.paragraphs[0].add_run()
        r.text = label
        r.font.size, r.font.bold, r.font.name = Pt(20), True, "Aptos"
        r.font.color.rgb = color

    block(1.25, 1.2, "General Objective", NAVY)
    text(s, 1.0, 1.75, 11.2, 0.8, [
        "To build and validate a DIgSILENT PowerFactory implementation of the dual-setting directional recloser "
        "(DSDR) coordination method on the IEEE 13-node feeder, with and without distributed generation."],
        bullet=False, size=17)

    block(2.85, 2.95, "Specific Objectives", RGBColor(0x2F, 0x6F, 0xB3))
    items = ["Build and verify the IEEE 13-node feeder with its recloser and fuse protection.",
             "Perform unbalanced load-flow and short-circuit studies for LG, LL, LLG and LLL faults.",
             "Calculate the recloser pickups, time dials and fuse coefficients.",
             "Establish the coordination without DG, then with a 4.05 MVA synchronous DG at node 692.",
             "Design the forward and reverse settings of R2 as a DSDR and check the coordination again.",
             "Verify the reclosing sequence in the time domain (EMT simulation).",
             "Study the effect of DG penetration from 0 to 100 %."]
    tb = s.shapes.add_textbox(emu(1.0), emu(3.35), emu(11.2), emu(3.1))
    tf = tb.text_frame
    tf.word_wrap = True
    for k, t in enumerate(items):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.space_after = Pt(5)
        r = p.add_run()
        r.text = "%d.  " % (k + 1)
        r.font.size, r.font.bold, r.font.name = Pt(16), True, "Aptos"
        r.font.color.rgb = RGBColor(0x2F, 0x6F, 0xB3)
        r = p.add_run()
        r.text = t
        r.font.size, r.font.name = Pt(16), "Aptos"
        r.font.color.rgb = INK
    return s


def title_slide(prs):
    """keep slide 1 of the earlier presentation, with the final wording; drop all other slides"""
    ids = prs.slides._sldIdLst
    for sid in list(ids)[1:]:
        prs.part.drop_rel(sid.get(qn("r:id")))
        ids.remove(sid)
    s = prs.slides[0]
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r.text = r.text.replace("Progress report presentation on", "Final project presentation on")
                r.text = r.text.replace("Progress report", "Final project").replace("September 2026", "October 2026")
        if sh.text_frame.text.startswith("Jhala Nath Kafle"):
            pass


def build():
    prs = Presentation(SRC)
    title_slide(prs)

    # ---- outline ---------------------------------------------------------------------------
    s = new_slide(prs, "Presentation Outline")
    items = [("Introduction", "Background and problem"), ("Objectives", "General and specific"),
             ("Scope", "What the study covers"), ("Methodology", "Method, model and settings"),
             ("Results", "Coordination, time domain, DG penetration"), ("Conclusions", "Findings and future work"),
             ("References", "Sources used"), ("Appendix", "Comparison with the reference paper")]
    for k, (h, b) in enumerate(items):
        x = 0.65 + (k % 4) * 3.05
        y = 1.45 + (k // 4) * 2.35
        card(s, x, y, 2.75, 1.95, "%d. %s" % (k + 1, h), b)

    # ---- introduction ----------------------------------------------------------------------
    s = new_slide(prs, "1. Introduction: Recloser–Fuse Coordination")
    text(s, 0.75, 1.3, 5.6, 4.8, [
        "**Fuse saving:** the recloser's fast trip clears a temporary fault before the lateral fuse melts; "
        "its delayed trip lets the fuse clear a permanent fault.",
        "Fast curve **below** the fuse's melting curve, delayed curve **above** its clearing curve.",
        "Coordination is guaranteed only while the recloser and the fuse carry the **same current**.",
        "A distributed generator (DG) changes the **magnitude** and the **direction** of the fault current."])
    picture(s, "fig01.png", 6.55, 1.15, 5.95, 4.9)
    caption(s, 6.55, 6.0, 5.95, "Conventional recloser–fuse coordination (R1 and fuse F646)")

    s = new_slide(prs, "1. Introduction: Problem Statement")
    card(s, 0.75, 1.35, 3.6, 1.85, "Without DG", "Fault current flows from the substation to the fault; "
         "recloser and fuse see the same current.")
    card(s, 4.65, 1.35, 3.6, 1.85, "With DG", "The fuse carries grid + DG current; the recloser only the grid "
         "share. A mid-line recloser sees reverse current.")
    card(s, 8.55, 1.35, 3.6, 1.85, "Consequence", "The fuse can melt before the fast trip: fuse saving is lost.",
         head_color=RED)
    text(s, 0.75, 3.55, 11.4, 2.7, [
        "**Problem:** loss of recloser–fuse coordination when a DG is connected; a single fixed setting does not "
        "suit both the forward (grid) and the reverse (DG) fault current.",
        "**Proposed solution:** a **Dual-Setting Directional Recloser (DSDR)** – the mid-line recloser R2 gets "
        "independent forward and reverse settings, selected by the direction of the current.",
        "**This project:** implements and tests the DSDR method on the IEEE 13-node feeder in DIgSILENT "
        "PowerFactory with the real characteristics of commercial relays and fuses."])

    # ---- objectives ------------------------------------------------------------------------
    objectives_slide(prs)

    # ---- scope -----------------------------------------------------------------------------
    s = new_slide(prs, "3. Scope and Limitations")
    text(s, 0.75, 1.25, 5.5, 0.5, ["Scope"], bullet=False, size=20, color=NAVY)
    text(s, 0.75, 1.8, 5.5, 4.4, [
        "IEEE 13-node feeder, 4.16 kV, unbalanced.",
        "LG, LL, LLG and LLL faults at 12 locations: 39 node/fault-type cells.",
        "Pickup, time-dial and fuse coordination calculations.",
        "DSDR forward and reverse settings; coordination with and without the DSDR.",
        "One EMT simulation of the reclosing sequence; DG penetration 0–100 %."], size=16, space=6)
    text(s, 6.55, 1.25, 5.6, 0.5, ["Limitations"], bullet=False, size=20, color=NAVY)
    text(s, 6.55, 1.8, 5.6, 4.4, [
        "R2 settings, fuse sizes and fault type of each operating-time case are not published; they were chosen "
        "and documented.",
        "The CDG34 library relay is not directional: two relay units, direction from the fault location.",
        "Zero-margin criterion (fuse must not start to melt before the fast trip).",
        "One DG location (692); IEEE 34-node feeder not modelled."], size=16, space=6)

    # ---- methodology -----------------------------------------------------------------------
    s = new_slide(prs, "4. Methodology: Coordination Method")
    text(s, 0.75, 1.3, 5.3, 4.9, [
        "**A.** Conventional scheme without DG: pickups by I_p = OLF × I_nom (OLF = 1.25), fuses sized and checked.",
        "**B.** Same settings with the DG connected: classification of all 39 cells.",
        "**C.** R2 as a DSDR: reverse pickup from the reverse load current, forward and reverse dials.",
        "If coordination is lost: revise the time dial; at the dial limit, upgrade the fuse size.",
        "Check: fuse melting time must exceed the recloser fast time, fuse clearing time below the delayed time."],
        size=16, space=7)
    picture(s, "flowchart.png", 6.3, 1.1, 6.0, 5.3)

    s = new_slide(prs, "4. Methodology: Test System in PowerFactory")
    picture(s, "sld.png", 0.4, 1.1, 6.6, 5.3)
    text(s, 7.2, 1.25, 4.9, 5.0, [
        "IEEE 13-node feeder, 4.16 kV, 115 kV grid via 5 MVA transformer.",
        "**DG:** 4.05 MVA synchronous machine at node 692, 0.69/4.16 kV transformer.",
        "**R1:** GE IAC77B801A at the feeder head (RG60–632).",
        "**R2:** CDG34 on line 632–671 (the DSDR).",
        "**Fuses:** A055C (E-rated) on the laterals.",
        "Unbalanced load flow, short-circuit and EMT studies in DIgSILENT PowerFactory 2021."],
        size=15, space=6)

    s = new_slide(prs, "4. Methodology: Protection Settings")
    table(s, [["Device", "Characteristic", "Pickup / plug (fast / delayed)", "Dial (fast / delayed)"],
              ["R1 (feeder head)", "GE IAC extremely inverse", "720 A", "TDS 0.5 / 10"],
              ["R2 forward (grid current)", "CDG34", "300 / 600 A", "TMS 0.1 / 1.0"],
              ["R2 reverse (DG current)", "CDG34, CT 500/5", "150 / 300 A", "TMS 0.1 / 1.0"]],
          0.75, 1.35, 11.4, [3.0, 3.0, 3.2, 2.2], size=15, row_h=0.5)
    text(s, 0.75, 3.65, 11.4, 2.6, [
        "Reverse load current of R2 with the DG: 252 A → reverse pickup 315 A (OLF = 1.25).",
        "Dial revision could not help: R1 and R2 are already at the ends of their dial ranges.",
        "Fuse revision (step 9 of the method): F632 → 500E; F633, F646, F-DL, F671-1 → 400E; F692-R → 250E."],
        size=16, space=8)

    # ---- results ---------------------------------------------------------------------------
    s = new_slide(prs, "5. Results: Without DG and the Effect of the DG")
    text(s, 0.75, 1.3, 5.6, 4.9, [
        "Fault levels agree with the IEEE short-circuit benchmark within about 2 % (feeder head 4.73 kA).",
        "**Without DG:** 35 of 39 cells coordinated with the starting fuses, **39 of 39** after F692-R → 200E.",
        "**With the DG:** the load current at R2 reverses (252 A).",
        "For faults upstream of R2 it carries **1.1 to 2.0 kA in reverse**, and the fuses carry grid + DG current."],
        size=16, space=8)
    picture(s, "fig08.png", 6.6, 1.1, 5.6, 4.95)
    caption(s, 6.6, 6.0, 5.6, "LG fault at 611 without DG: R2 forward with F684 and F671-2")

    s = new_slide(prs, "5. Results: DG Connected, Conventional R2")
    picture(s, "fig14.png", 0.4, 1.15, 7.3, 4.9)
    text(s, 7.9, 1.3, 4.3, 4.9, [
        "Coordination held in **24 of 39** cells.",
        "Lost at 633, 645, 646, DL and 675.",
        "The fuse carries grid + DG current and melts before the fast trip.",
        "For some LG faults the single-setting R2 does not pick up the reverse DG current at all."],
        size=16, space=8)

    s = new_slide(prs, "5. Results: With the DSDR")
    picture(s, "fig17.png", 0.4, 1.15, 7.3, 4.9)
    text(s, 7.9, 1.3, 4.3, 4.9, [
        "Coordination held in **38 of 39** cells.",
        "Same fuses with a single-setting R2: 31 cells.",
        "The dual setting restores **7 cells**: all faults at 633 and the LG faults at 645, 646 and DL.",
        "Still lost: LG fault at 692 – the 400E fuse F671-1 clears after R2's delayed trip (7.6 s vs 4.0 s); the delayed dial is already at its maximum."],
        size=16, space=8)

    s = new_slide(prs, "5. Results: Single vs Dual Setting (3-phase fault near 632)")
    picture(s, "case05.png", 0.4, 1.1, 11.4, 3.55)
    table(s, [["Quantity", "Single setting", "Dual setting (DSDR)"],
              ["Current through R2", "1777 A, reverse (DG contribution)", "1777 A, reverse"],
              ["R2 setting used", "Forward: plug 300/600 A", "Reverse: plug 150/300 A"],
              ["R2 fast trip", "0.121 s", "0.052 s"],
              ["F633 (400E) starts to melt", "0.100 s", "0.100 s"],
              ["Fuse saving", "LOST", "HELD"]],
          1.4, 4.7, 9.4, [3.2, 3.4, 3.0], size=12, row_h=0.28,
          colors={(5, 1): RED, (5, 2): GREEN})

    s = new_slide(prs, "5. Results: Time-Sequence Check of All Faults")
    picture(s, "cd_sequence.png", 0.4, 1.1, 7.6, 5.3)
    text(s, 8.2, 1.3, 4.0, 4.9, [
        "Each fault followed in time: the fuse heats while current flows after each recloser opens.",
        "Above R2: **15 of 18** held with a single setting, **18 of 18** with the DSDR.",
        "Restored: LG faults at 633, 645 and 646.",
        "Below R2 the DG feeds the fault directly: the setting of R2 makes no difference."],
        size=15, space=8)

    s = new_slide(prs, "5. Results: Time-Domain (EMT) Verification")
    picture(s, "fig10.png", 0.4, 1.1, 6.6, 5.3)
    table(s, [["Event", "Without DG", "With DG"],
              ["F671-2 melts", "1.248 s", "0.752 s"],
              ["F671-2 clears", "1.613 s", "1.253 s"]],
          7.2, 1.35, 4.9, [1.8, 1.5, 1.5], size=13, row_h=0.42)
    text(s, 7.2, 2.85, 4.9, 3.4, [
        "LL fault (a–c) at 684 through 0.2 Ω, conventional settings.",
        "Without DG the two fast shots use 45 % of the fuse's melting heat; the fuse then clears the "
        "permanent fault.",
        "With DG the fuse melts during the second fast shot: the DG keeps feeding the fault while R2 is open."],
        size=14, space=6)

    s = new_slide(prs, "5. Results: Effect of the DG Penetration Level")
    picture(s, "pen_ring.png", 0.4, 1.1, 6.0, 5.2)
    text(s, 6.6, 1.3, 5.6, 4.9, [
        "Seven PowerFactory models: DG 0, 10, 25, 37, 50, 75, 100 % of 4.05 MVA; settings of the design "
        "without DG kept.",
        "CTI = t_MMT(fuse) − t_fast(recloser):",
        ("node 633: **+4 ms → −51 ms**", 1),
        ("node 671: **+403 ms → +75 ms**", 1),
        "The fuse carries grid + DG current, the recloser only the grid share: the CTI falls as the DG grows.",
        "Fault level rises by up to 64 %; R2 stops detecting its weakest fault above about 50 %."],
        size=15, space=6)

    s = new_slide(prs, "5. Results: Summary and Verification")
    table(s, [["Stage", "Cells held (of 39)"],
              ["No DG, starting fuse sizes", "35"],
              ["No DG, after the fuse revision", "39"],
              ["DG connected, conventional R2", "24"],
              ["DG connected, no-DG fuses, R2 as DSDR", "25"],
              ["DG connected, revised fuses, conventional R2", "31"],
              ["DG connected, revised fuses, R2 as DSDR", "38"]],
          0.75, 1.35, 7.0, [5.2, 1.8], size=14, row_h=0.45, colors={(6, 1): GREEN})
    text(s, 8.05, 1.3, 4.2, 4.9, [
        "PowerFactory's own relay and fuse models reproduce the calculated operating times within **1.22 %** "
        "(1896 operating times).",
        "With a breaker time of 3 cycles: 31 cells held; with a fuse safety margin as well: 26."],
        size=15, space=10)

    # ---- conclusions -----------------------------------------------------------------------
    s = new_slide(prs, "6. Conclusions and Future Work")
    text(s, 0.75, 1.25, 11.4, 3.5, [
        "The DSDR method was implemented on the IEEE 13-node feeder in DIgSILENT PowerFactory with real relay "
        "and fuse characteristics; the model meets the IEEE benchmark within about 2 %.",
        "The DG breaks coordination: **39 → 24 of 39** cells with a conventional R2.",
        "R2 as a DSDR with the fuse revision restores it: **38 of 39** cells (31 with a single setting).",
        "The DSDR works in the zone between the grid and the DG; it needs the fuse revision, and faults "
        "below R2 (fed directly by the DG) remain a limit.",
        "With fixed settings the CTI falls steadily as the DG penetration rises."], size=16, space=7)
    text(s, 0.75, 4.75, 11.4, 0.45, ["Future work"], bullet=False, size=18, color=NAVY)
    text(s, 0.75, 5.2, 11.4, 1.2, [
        "IEEE 34-node feeder; explicit directional element for R2; practical margins; setting-group change "
        "triggered by the DG state; inverter-based DG; hardware-in-the-loop tests."], size=15)

    # ---- references ------------------------------------------------------------------------
    s = new_slide(prs, "7. References")
    text(s, 0.75, 1.2, 11.4, 5.2, [
        "[1] M. Yousaf, A. Jalilian, K. M. Muttaqi, D. Sutanto, \"An adaptive overcurrent protection scheme for "
        "dual-setting directional recloser and fuse coordination in unbalanced distribution networks with "
        "distributed generation,\" IEEE Trans. Ind. Appl., vol. 58, no. 2, pp. 1831–1842, 2022.",
        "[2] W. H. Kersting, \"Radial distribution test feeders,\" IEEE Trans. Power Syst., vol. 6, no. 3, "
        "pp. 975–985, 1991.",
        "[3] G. Benmouyal et al., \"IEEE standard inverse-time characteristic equations for overcurrent "
        "relays,\" IEEE Trans. Power Del., vol. 14, no. 3, pp. 868–872, 1999.",
        "[4] A. Naiem et al., \"A classification technique for recloser-fuse coordination in distribution "
        "systems with distributed generation,\" IEEE Trans. Power Del., vol. 27, no. 1, pp. 176–185, 2012.",
        "[5] M. Yousaf, K. M. Muttaqi, D. Sutanto, \"Overcurrent protection scheme for the IEEE 13-node "
        "benchmark test feeder with improved selectivity,\" IEEE PES General Meeting, 2020.",
        "[6] W. H. Kersting, G. Shirek, \"Short circuit analysis of IEEE test feeders,\" IEEE PES T&D, 2012.",
        "[7] DIgSILENT GmbH, PowerFactory 2021 User Manual, 2021.",
        "[8] GE Multilin, 735/737 Feeder Protection Relay – Instruction Manual (GEK-106291F), 2010."],
        bullet=False, size=13, space=6)

    # ---- appendix --------------------------------------------------------------------------
    s = new_slide(prs, "Appendix: Comparison with the Reference Paper")
    table(s, [["Aspect", "This project", "Reference paper [1]", "Assessment"],
              ["Rated branch currents", "within 2 %", "Table II", "Very good"],
              ["Fault levels", "IEEE benchmark, 4.73 kA at head", "5.41 kA, some branches higher", "Lower"],
              ["R1 worked example (4219 A)", "0.096 / 1.926 s", "0.097 / 1.932 s", "Very good"],
              ["Coordination with DG, conventional R2", "24 of 39 held", "30 of 39 (Fig. 14)", "Good (29 cells agree)"],
              ["Coordination with the DSDR", "38 of 39 held", "39 of 39 (Fig. 17)", "Good; one cell at dial limit"],
              ["Fuse current, LL at 646", "3.67 kA", "3.64 kA (Fig. 15)", "Very good"],
              ["R2 reverse current, LL at 646", "1.11 kA", "1.54 kA", "Lower"],
              ["EMT: fuse operation", "melts 1.25 s, clears 1.61 s", "1.21 s (Fig. 10)", "Close"],
              ["DG model", "Dynamic synchronous machine", "Synchronous machine", "Same"]],
          0.5, 1.2, 11.2, [3.2, 2.9, 2.8, 2.6], size=12, row_h=0.47)

    s = new_slide(prs, "Appendix: CTI with DG Penetration – Study and Paper")
    picture(s, "pen_ring_vs_paper.png", 0.4, 1.1, 7.6, 5.2)
    text(s, 8.2, 1.3, 4.0, 4.9, [
        "Both show the CTI **decreasing** as the DG penetration rises.",
        "The paper's values are read from its Fig. 7.",
        "Where the sign changes depends on the starting margin, i.e. on fuse sizes and settings that the paper "
        "does not publish.",
        "Central finding reproduced: the DSDR restores coordination between the grid and the DG."],
        size=15, space=8)

    # ---- close -----------------------------------------------------------------------------
    s = new_slide(prs, "Thank You")
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, emu(2.0), emu(2.6), emu(8.33), emu(1.3))
    b.fill.solid()
    b.fill.fore_color.rgb = NAVY
    b.line.fill.background()
    p = b.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "Questions and Discussion"
    r.font.size, r.font.bold, r.font.name = Pt(30), True, "Aptos Display"
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    page_numbers(prs)
    assert len(NOTES) == len(prs.slides), (len(NOTES), len(prs.slides))
    for s, n in zip(prs.slides, NOTES):                   # speaker notes: seen only in Presenter View
        s.notes_slide.notes_text_frame.text = " ".join(n.split())
    try:
        prs.save(OUT)
        out = OUT
    except PermissionError:
        out = OUT.replace(".pptx", "_new.pptx")
        prs.save(out)
    print("PRESENTATION:", out, "(%d slides)" % len(prs.slides))
    return out


if __name__ == "__main__":
    build()
