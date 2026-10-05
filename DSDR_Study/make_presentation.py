"""
Final presentation: keeps the title slide and the design of the earlier presentation (navy bar, Aptos
fonts) and fills it with the results of this study, in the order asked by the department:
Title, Introduction, Objectives, Scope, Methodology, Results, Conclusions, References, Appendix
(comparison with the reference paper).

Input : presentation_template.pptx (design and title slide)
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
SRC = os.path.join(HERE, "presentation_template.pptx")      # title slide and design (copy of the deck)
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
    logo = os.path.join(FIGS, "tu_logo.png")                   # TU logo, small, top right
    if os.path.exists(logo):
        s.shapes.add_picture(logo, W - emu(0.42) - emu(0.35), emu(0.2), width=emu(0.42))
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
    tb.text_frame.word_wrap = True
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
    """In a fuse-saving scheme the recloser trips first on its fast curve, so a temporary fault clears
    and the fuse is saved; for a permanent fault the delayed curve lets the fuse clear its lateral. This works
    only while the recloser and the fuse carry the same current, and a DG changes both the size and the
    direction of the fault current.""",
    # 4 problem
    """With a DG the fuse carries grid plus DG current, while the recloser sees only the grid part, and a
    mid-line recloser can even see reverse current. The fuse may then melt before the fast trip. The solution
    studied is the dual-setting directional recloser, or DSDR: R2 gets separate forward and reverse settings,
    chosen by the current direction.""",
    # 5 objectives
    """The general objective was to build and validate a PowerFactory implementation of the DSDR method on
    the IEEE 13-node feeder, with and without DG. To reach it there are seven specific
    objectives: the model, load flow and short circuit, the settings, coordination without and
    with the DG, the dual setting of R2, a time-domain check, and the effect of DG penetration.""",
    # 6 scope
    """The study covers four fault types at twelve locations, which gives 39 node and fault-type cells,
    plus one EMT simulation and a penetration study. The limitations: the method does not uniquely specify some
    settings, so they were defined in this study and documented; the CDG34 relay model is not directional, so two
    relay units are used; the coordination is classified with a zero margin; and only one DG location is studied.""",
    # 7 method
    """The method has three stages: A, the conventional design without DG, with pickup equal to 1.25 times
    the rated current; B, the same settings with the DG; and C, R2 as a DSDR. If coordination is lost, the
    time dial is revised first, and at the dial limit the fuse is made larger. The fuse must not melt before
    the fast trip, and must clear before the delayed trip.""",
    # 7b equations
    """These are the equations of the method: one inverse-time curve with a fast and a delayed time dial,
    for the forward and the reverse direction; the pickup from the load current; the fuse line on log-log axes;
    and the coordination conditions.""",
    # 7c real curves
    """The method writes the operating time as TDS times a function of M, the fault current over the pickup.
    A, B and n describe only a generic curve, so I kept the structure and used the manufacturer's curve of
    each relay: the GE Multilin equation for R1 and the manufacturer's table for the CDG34. The dial is called TDS
    for the IAC relay and TMS for the CDG34; both scale the curve in the same way. The pickups, dials, limits and
    coordination rules of the method are unchanged. This is checked twice: R1 reproduces the paper's worked
    example within one millisecond, and PowerFactory's own relay models confirm all 1896 times within 1.22
    percent.""",
    # 8 system
    """This is the PowerFactory model: a 4.16 kV feeder fed from a 115 kV grid, a 4.05 MVA synchronous
    generator at node 692, R1 a GE IAC77 relay at the feeder head, R2 a CDG34 relay on line 632 to 671, and
    A055C fuses on the laterals.""",
    # 8b DG parameters
    """These are the parameters of the synchronous DG used in the model, 4.05 MVA at 0.69 kilovolts, connected at
    node 692 through a 0.69 to 4.16 kilovolt transformer.""",
    # 9 settings
    """R1 has a pickup of 720 amperes and dials 0.5 and 10. R2 forward uses plugs of 300 and 600 amperes,
    the new reverse group 150 and 300 amperes. With the DG, the load current through R2 reverses to 252
    amperes, giving a reverse pickup of about 315 amperes. The dials were already at their limits, so the
    fuse sizes were revised as shown.""",
    # 9b branch currents and fault levels
    """The first result is the base case without DG: the rated current of each protected branch from the
    load flow, the minimum fault current, an LG fault through 3 ohm at the farthest node, and the maximum, a
    bolted fault at the nearest node. The feeder head sees 4.73 kiloamperes.""",
    # 9c fuse coefficients
    """With the method's fuse equation, slope a equal to minus 1.8, the coefficient b of every fuse follows from
    the recloser times at the largest fault current below that fuse. The last columns give the installed fuse
    and its melting time.""",
    # 10 without DG
    """Without DG, 35 of 39 cells were coordinated, and all 39 after one fuse change. In both examples,
    an LG fault at 611 and an LLG fault between 692 and 675, R2's fast curve is below the fuses and its
    delayed curve above them.""",
    # 11 conventional
    """With the DG and unchanged settings, coordination holds in only 24 of 39 cells. Losses are at 633,
    645, 646, the distributed load and 675: the fuse melts before the fast trip, and for some LG faults R2
    does not even pick up the reverse current.""",
    # 11b three selected faults
    """Three faults with the DG and the conventional settings. At 646 and 645 through a fault impedance the
    recloser still trips first. For the three-phase fault close to 632, R2 carries 1777 amperes in reverse and
    trips in 0.121 seconds, but fuse F633 melts in 0.039 seconds: coordination is lost.""",
    # 12 dsdr
    """With R2 as a DSDR and revised fuses, 38 of 39 cells are held under the zero-margin criterion. With the
    same revised fuses but a single-setting R2 only 31, so the dual setting itself restores seven cells, at 633,
    645, 646 and the distributed load. The DSDR with the old fuses gives only 25, so it needs the fuse revision.
    Only the LG fault at 692 stays lost, limited by the maximum delayed dial of R2.""",
    # 12b bolted LL at 646
    """A bolted line-to-line fault at 646 with the DSDR. The fuses carry 3.67 kiloamperes. R2 sees the DG share,
    1114 amperes in reverse, and its reverse group trips in 0.086 seconds; R1 sees the grid share and trips in
    0.189 seconds. Both are before F646 starts to melt at 0.415 seconds, so the fuse is saved.""",
    # 12c operating times
    """This table gives the operating times with the DSDR and the DG connected. R2 works in reverse for the
    nodes above it and forward for those below. In every row the fuse starts to melt after the last fast trip;
    the smallest margins are 6 milliseconds at 675 and 15 at the distributed load.""",
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
    """In summary: without DG 35 of 39 cells with the starting fuses and 39 after the fuse revision; 24 with
    the DG and a conventional R2; 25 with the DSDR alone, 31 with the fuse revision alone, and 38 with both.
    These counts use a zero margin. PowerFactory's own relay and fuse models reproduced all 1896 operating times within 1.22
    percent.""",
    # 18 conclusions
    """To conclude: with the DG a conventional R2 keeps only 24 of 39 cells. The combined DSDR and fuse
    revision raises this to 38 of 39 under the zero-margin criterion, and the last cell, the LG fault at 692,
    is limited by R2's maximum delayed dial. The DSDR alone gives only 25, so it is necessary but not
    sufficient, and faults below R2 remain a limit. Future work includes the 34-node feeder, a true directional
    element and inverter-based DG.""",
    # 19 references
    """These are the main references; the method is from Yousaf and co-authors, 2022.""",
    # 20 appendix
    """Compared with the reference paper, load currents agree within 2 percent and the R1 worked example
    almost exactly. My fault levels are lower because I validated against the IEEE benchmark. The paper
    reports 30 and 39 coordinated cells, I obtained 24 and 38. The main finding is reproduced: the DSDR with the
    fuse revision restores the coordination between the grid and the DG.""",
    # 20b fault levels vs benchmark
    """My fault levels are lower than the paper's, so I checked them against the IEEE short-circuit benchmark,
    the source the same authors used in their 2020 paper. My model agrees within 2 percent at ten of eleven
    nodes. The paper's values are up to 151 percent higher, and two of them exceed its own feeder-head value of
    5.41 kiloamperes, which is not possible in a radial feeder without DG.""",
    # 20c operating times vs paper
    """The operating times with the DSDR show the same behaviour as the paper: in every row the fuse melts after
    the fast trip of the recloser that protects it. R1's delayed time is twenty times the fast time in both, which confirms the dials; the
    differences follow the lower fault levels. R2's settings are not published, so its times are compared in
    trend only.""",
    # 21 appendix penetration
    """Both studies show the margin decreasing with DG penetration; where it turns negative depends on
    settings the paper does not publish.""",
    # 22 close
    """Thank you for your attention. I am happy to take your questions.""",
]


def read_csv(name):
    import csv
    return list(csv.DictReader(open(os.path.join(HERE, "results", name))))


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
             "Design the DSDR settings of R2, classify the resulting coordination, find the operating times.",
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
        if sh.text_frame.text.startswith("Jhala Nath Kafle") and "Roll No." not in sh.text_frame.text:
            # roll number as the second line, formatted like the lines below the name
            paras = sh.text_frame.paragraphs
            ref = paras[1]
            new_p = copy.deepcopy(ref._p)
            ref._p.addprevious(new_p)
            runs = new_p.findall(qn("a:r"))
            for extra in runs[1:]:
                new_p.remove(extra)
            runs[0].find(qn("a:t")).text = "Roll No. 081MSPSE009"


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
        "PowerFactory with the manufacturer-based time–current characteristics of commercial relays and fuses."])

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
        "The method does not uniquely specify the R2 settings, fuse sizes or fault type of each operating-time "
        "case; they were defined in this study and documented.",
        "The CDG34 library relay is not directional: two relay units, direction from the fault location.",
        "Zero-margin criterion: CTI = t_MMT − t_F > 0.",
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

    s = new_slide(prs, "4. Methodology: Mathematical Formulation of the Method")
    picture(s, os.path.join(HERE, "results", "figures", "DSDR_equations_method.png"), 0.35, 1.0, 12.6, 6.0)

    s = new_slide(prs, "4. Methodology: Operating Times from the Manufacturers' Curves")
    picture(s, os.path.join(HERE, "results", "figures", "DSDR_equations_impl.png"), 0.6, 0.95, 12.1, 4.0)
    text(s, 0.75, 5.0, 5.9, 0.4, ["Why the manufacturers' curves"], bullet=False, size=16, color=NAVY)
    text(s, 0.75, 5.4, 5.9, 1.3, [
        "The method fixes the structure t = TDS × g(M); A, B and n only describe a generic curve.",
        "R1 (GE IAC, dial called TDS) and R2 (CDG34, dial called TMS) use the curves of their manufacturers; "
        "both dials scale the curve in the same way."], size=13, space=3)
    text(s, 6.85, 5.0, 5.9, 0.4, ["How we know it is right"], bullet=False, size=16, color=NAVY)
    text(s, 6.85, 5.4, 5.9, 1.3, [
        "R1 reproduces the paper's worked example: **0.096 / 1.926 s** against 0.097 / 1.932 s (4219 A).",
        "PowerFactory's own relay models confirm all **1896** operating times within **1.22 %**."],
        size=13, space=3)

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

    s = new_slide(prs, "4. Methodology: Parameters of the Synchronous DG")
    left = [["Parameter", "Symbol", "Value"],
            ["Leakage reactance", "Xl", "0.05 pu"], ["Stator resistance", "Ra", "0.0014 pu"],
            ["d-axis synchronous reactance", "Xd", "1.4 pu"], ["d-axis transient reactance", "X'd", "0.231 pu"],
            ["d-axis subtransient reactance", "X''d", "0.118 pu"], ["d-axis transient OC time const.", "T'd0", "5.5 s"],
            ["d-axis subtransient OC time const.", "T''d0", "0.05 s"], ["q-axis synchronous reactance", "Xq", "1.372 pu"],
            ["q-axis transient reactance", "X'q", "0.8 pu"]]
    right = [["Parameter", "Symbol", "Value"],
             ["q-axis subtransient reactance", "X''q", "0.118 pu"], ["q-axis transient OC time const.", "T'q0", "1.25 s"],
             ["q-axis subtransient OC time const.", "T''q0", "0.19 s"], ["Mechanical starting time", "M = 2H", "1.5 s"],
             ["DG rating", "Sn", "4.05 MVA"], ["DG voltage", "Un", "0.69 kV"],
             ["Step-up transformer", "", "0.69 / 4.16 kV"], ["Transformer leakage reactance", "xT", "0.15 pu"],
             ["Connection node", "", "692"]]
    table(s, left, 0.5, 1.25, 6.0, [3.4, 1.1, 1.5], size=12, row_h=0.42)
    table(s, right, 6.85, 1.25, 6.0, [3.4, 1.1, 1.5], size=12, row_h=0.42)
    caption(s, 0.5, 5.6, 12.35, "Dynamic synchronous machine in PowerFactory, operating point 3.24 MW, voltage control at 1.0 pu")

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
    s = new_slide(prs, "5. Results: Branch Currents and Fault Levels (DG out)")
    t2 = [["Branch", "Rated current Inom (A)", "If,min (kA)  LG 3 Ω, farthest node", "If,max (kA)  bolted, nearest node"]]
    for r in read_csv("Table_II.csv"):
        br = ("%s %s" % (r["From"], r["To"])).replace("XFM1-HV side", "XFM-1 HV side").replace("XFM1-LV side", "XFM-1 LV side") \
            if r["From"].startswith("XFM") else "%s–%s" % (r["From"], r["To"])
        t2.append([br, r["Inom (A)"], r["If,min (kA)"], r["If,max (kA)"]])
    table(s, t2, 1.4, 1.1, 10.5, [2.6, 2.6, 2.7, 2.6], size=12, row_h=0.345, first_col_left=True)
    caption(s, 1.4, 6.25, 10.5, "Unbalanced load flow (largest phase) and short circuit, complete method; XFM-1 LV side at 0.48 kV")

    s = new_slide(prs, "5. Results: Fuse Coefficients (eq. 9, a = −1.8)")
    t3 = [["Fuse", "If (A)", "i / z", "t fast (s)", "t delayed (s)", "t fuse (s)", "b i", "Installed fuse", "t MMT (s)"]]
    for r in read_csv("Table_III.csv"):
        t3.append([r["Fuse"], r["If (A)"], r["i/z"], "%.3f" % float(r["t_fast (s)"]), "%.3f" % float(r["t_delayed (s)"]),
                   "%.3f" % float(r["t_fuse eq.(9) (s)"]), r["b_i (eq. 9, i=1 closest to fault)"],
                   r["installed fuse"].replace("A055C", ""), r["t_MMT of installed fuse at If (s)"]])
    table(s, t3, 0.6, 1.1, 12.1, [1.3, 1.1, 0.9, 1.3, 1.4, 1.3, 1.0, 1.7, 1.3], size=11.5, row_h=0.305)
    caption(s, 0.6, 6.05, 12.1, "If: largest fault current below the fuse, DG out. i / z: position in a series of z fuses (1 = closest to the fault)")

    s = new_slide(prs, "5. Results: Coordination Without DG")
    picture(s, "fig08.png", 0.45, 1.05, 6.1, 4.45)
    picture(s, "fig09.png", 6.75, 1.05, 6.1, 4.45)
    caption(s, 0.45, 5.45, 6.1, "LG fault at 611: R2 fast 0.128 s < F684 melts 0.271 s – held")
    caption(s, 6.75, 5.45, 6.1, "LLG fault mid 692–675, 1 Ω: R2 fast 0.204 s < F692-R melts 0.331 s – held")
    text(s, 0.75, 5.85, 11.8, 0.6, [
        "Fault levels within about 2 % of the IEEE benchmark. **35 of 39** cells held with the starting fuses, "
        "**39 of 39** after F692-R → 200E. R2 fast below the fuses, delayed above them."], bullet=False, size=14)

    s = new_slide(prs, "5. Results: DG Connected, Conventional R2")
    picture(s, "fig14.png", 0.4, 1.15, 7.3, 4.9)
    text(s, 7.9, 1.3, 4.3, 4.9, [
        "Coordination held in **24 of 39** cells.",
        "Lost at 633, 645, 646, DL and 675.",
        "The fuse carries grid + DG current and melts before the fast trip.",
        "For some LG faults the single-setting R2 does not pick up the reverse DG current at all."],
        size=16, space=8)

    s = new_slide(prs, "5. Results: Conventional R2 with DG – Three Faults")
    for k, (pic, head, lines, ok) in enumerate((
            ("fig11.png", "LL fault at 646, 1 Ω",
             ["R1 1899 A: fast 0.395 s", "F646 300E melts 0.595 s", "R1 trips first"], True),
            ("fig12.png", "LL fault at 645, 1.5 Ω",
             ["R2 783 A (reverse): fast 0.605 s", "F632 400E melts 2.649 s", "R2 trips first"], True),
            ("fig13.png", "Three-phase fault at 10 % of 632–633",
             ["R2 1777 A (reverse): fast 0.121 s", "F633 250E melts 0.039 s", "the fuse melts first"], False))):
        x = 0.35 + k * 4.25
        picture(s, pic, x, 1.05, 4.15, 3.05)
        tb = s.shapes.add_textbox(emu(x + 0.1), emu(4.2), emu(3.95), emu(2.1))
        tf = tb.text_frame
        tf.word_wrap = True
        for j, t in enumerate([head] + lines + ["coordination HELD" if ok else "coordination LOST"]):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = t
            r.font.name = "Aptos"
            r.font.size = Pt(15 if j == 0 else 13)
            r.font.bold = j in (0, 4)
            r.font.color.rgb = NAVY if j == 0 else (GREEN if ok else RED) if j == 4 else INK

    s = new_slide(prs, "5. Results: With the DSDR")
    picture(s, "fig17.png", 0.4, 1.15, 7.3, 4.9)
    text(s, 7.9, 1.3, 4.3, 4.9, [
        "Coordination held in **38 of 39** cells (zero margin).",
        "Same revised fuses, single-setting R2: 31 cells; DSDR with the no-DG fuses: 25.",
        "The dual setting restores **7 cells**: all faults at 633 and the LG faults at 645, 646 and DL.",
        "Still lost: LG fault at 692 – the 400E fuse F671-1 clears after R2's delayed trip (7.6 s vs 4.0 s); the delayed dial is already at its maximum."],
        size=16, space=8)

    s = new_slide(prs, "5. Results: Bolted LL Fault at 646 with the DSDR")
    picture(s, "fig15.png", 0.45, 1.05, 6.1, 4.45)
    picture(s, "fig16.png", 6.75, 1.05, 6.1, 4.45)
    caption(s, 0.45, 5.45, 6.1, "R2 reverse (DG share, 1114 A): fast 0.086 s")
    caption(s, 6.75, 5.45, 6.1, "R1 (grid share, 2785 A): fast 0.189 s")
    text(s, 0.75, 5.85, 11.8, 0.6, [
        "The fuses carry 3.67 kA (grid + DG). Both reclosers trip before F646 (400E) starts to melt at **0.415 s**: "
        "R2 removes the DG share, R1 the grid share – fuse saved."], bullet=False, size=14)

    s = new_slide(prs, "5. Results: Operating Times with the DSDR (DG in)")
    t4 = [["Node", "Fault", "I R1 (A)", "R1 fast / delayed (s)", "I R2 (A)", "R2 fast / delayed (s)", "Fuse",
           "I fuse (A)", "Fuse MMT / TCT (s)"]]
    for r in read_csv("Table_IV.csv"):
        t4.append([r["node"], r["fault"], r["I R1 (A)"], "%s / %s" % (r["R1 fast (s)"], r["R1 delayed (s)"]),
                   "%s %s" % (r["I R2 (A)"], "rev" if r["R2 unit"] == "rev" else "fwd"),
                   "%s / %s" % (r["R2 fast (s)"], r["R2 delayed (s)"]), r["fuse"].replace("---", "–"),
                   r["I fuse (A)"] or "–", "–" if r["fuse MMT (s)"] == "---" else "%s / %s" % (r["fuse MMT (s)"], r["fuse TCT (s)"])])
    table(s, t4, 0.45, 1.1, 12.4, [0.9, 0.9, 1.1, 1.9, 1.3, 1.9, 1.2, 1.1, 1.9], size=11.5, row_h=0.355)
    caption(s, 0.45, 5.85, 12.4, "Bolted LLL (LL at two-phase, LG at one-phase nodes). Every fuse starts to melt after the last fast trip; "
            "smallest margins 6 ms (675) and 15 ms (DL)")

    s = new_slide(prs, "5. Results: Single vs Dual Setting (Three-Phase Fault near 632)")
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
        "These counts use the zero-margin criterion, CTI = t_MMT − t_F > 0."],
        size=15, space=10)

    # ---- conclusions -----------------------------------------------------------------------
    s = new_slide(prs, "6. Conclusions and Future Work")
    text(s, 0.75, 1.2, 11.4, 3.55, [
        "The DSDR method was implemented on the IEEE 13-node feeder in DIgSILENT PowerFactory with "
        "manufacturer-based relay and fuse characteristics; the model meets the IEEE benchmark within about 2 %.",
        "Without DG: **35 of 39** cells with the starting fuses, **39 of 39** after the fuse revision.",
        "With the DG and a conventional R2: **24**. DSDR alone: 25; fuse revision alone: 31; combined DSDR and "
        "fuse revision: **38 of 39** (zero margin). The remaining LG fault at 692 is limited by R2's maximum "
        "delayed dial.",
        "The DSDR is necessary but not sufficient: it needs the fuse revision, and faults below R2 remain a limit. "
        "PowerFactory's relay and fuse models confirm the times within 1.22 %."], size=15, space=5)
    text(s, 0.75, 4.75, 11.4, 0.45, ["Future work"], bullet=False, size=18, color=NAVY)
    text(s, 0.75, 5.2, 11.4, 1.2, [
        "IEEE 34-node feeder; explicit directional element for R2; setting-group change "
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

    s = new_slide(prs, "Appendix: Fault Levels – IEEE Benchmark, This Study and the Paper")
    fl = [["Node", "IEEE benchmark (kA)", "This study (kA)", "Study vs benchmark", "Paper, Table II (kA)",
           "Paper vs benchmark"]]
    for r in read_csv("Fault_level_benchmark.csv"):
        fl.append([r["Node"], "%.2f" % float(r["IEEE benchmark (kA)"]), "%.2f" % float(r["This study (kA)"]),
                   "%+.1f %%" % float(r["Study vs benchmark (%)"]), "%.2f" % float(r["Paper Table II If,max of the branch (kA)"]),
                   "%+.1f %%" % float(r["Paper vs benchmark (%)"])])
    table(s, fl, 0.45, 1.15, 8.1, [0.9, 1.45, 1.3, 1.45, 1.45, 1.45], size=11.5, row_h=0.36, first_col_left=False)
    caption(s, 0.45, 5.6, 8.1, "Maximum fault current, DG out. Benchmark: Kersting & Shirek [6], values as quoted in [5]; "
            "paper: If,max of the branch ending at the node")
    text(s, 8.75, 1.25, 3.9, 5.2, [
        "**This study vs IEEE benchmark:** within 2 % at 10 of 11 nodes; largest difference 4.7 % (652, LG).",
        "**Paper vs benchmark:** 4 % to 151 % higher.",
        "The paper's 6.73 kA (632–633) and 7.83 kA (692–675) exceed its own **5.41 kA at the feeder head** – "
        "not possible in a radial feeder without DG.",
        "So the model was validated against the benchmark, not tuned to the paper's Table II."],
        size=14, space=8)

    s = new_slide(prs, "Appendix: DSDR Operating Times – This Study and the Paper")
    op = [["Node", "Fault", "R1 fast (s)", "R1 delayed (s)", "R2 fast (s)", "R2 delayed (s)", "Fuse melts (s)"]]
    for r in read_csv(os.path.join("comparison", "Table_IV_vs_paper.csv")):
        pair = lambda a, b: "–" if a in ("---", "") else "%s / %s" % (a, b)
        op.append([r["node"], r["fault"], pair(r["R1 fast (s)"], r["paper R1 fast"]),
                   pair(r["R1 delayed (s)"], r["paper R1 delayed"]), pair(r["R2 fast (s)"], r["paper R2 fast"]),
                   pair(r["R2 delayed (s)"], r["paper R2 delayed"]), pair(r["fuse MMT (s)"], r["paper fuse MMT"])])
    table(s, op, 0.45, 1.1, 8.3, [0.8, 0.8, 1.35, 1.4, 1.35, 1.4, 1.4], size=11, row_h=0.345, first_col_left=False)
    caption(s, 0.45, 5.65, 8.3, "Each cell: this study / reference paper [1]; DG connected, R2 as DSDR")
    text(s, 8.95, 1.2, 3.85, 5.2, [
        "**Same behaviour:** in every row of both studies the fuse melts after the fast trip of the recloser(s) that protect it (R1 and R2 above R2, R2 below) – coordination held.",
        "**R1:** delayed = 20 × fast in both (dials 0.5 / 10 confirmed). Times differ with the fault current: "
        "lower fault levels give slower R1.",
        "**R2:** reverse group for 632–DL, forward below R2 in both.",
        "R2 settings and fuse sizes are not published in [1], so R2 and fuse times are compared in trend, not row by row."],
        size=13, space=7)

    s = new_slide(prs, "Appendix: CTI with DG Penetration – Study and Paper")
    picture(s, "pen_ring_vs_paper.png", 0.4, 1.1, 7.6, 5.2)
    text(s, 8.2, 1.3, 4.0, 4.9, [
        "Both show the CTI **decreasing** as the DG penetration rises.",
        "The paper's values are read from its Fig. 7.",
        "Where the sign changes depends on the starting margin, i.e. on fuse sizes and settings that the paper "
        "does not publish.",
        "Central finding reproduced: the DSDR with the fuse revision restores coordination between the grid "
        "and the DG (38 of 39 cells)."],
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
    out = None
    for suffix in ("", "_new", "_v2", "_v3", "_v4"):          # a file open in PowerPoint is locked
        try:
            prs.save(OUT.replace(".pptx", suffix + ".pptx"))
            out = OUT.replace(".pptx", suffix + ".pptx")
            break
        except PermissionError:
            continue
    print("PRESENTATION:", out, "(%d slides)" % len(prs.slides))
    return out


if __name__ == "__main__":
    build()
