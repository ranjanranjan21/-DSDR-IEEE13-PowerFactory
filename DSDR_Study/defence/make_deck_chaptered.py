"""
Presentation in the chaptered layout of the department's sample deck: white slides, Times New Roman, navy
"Chapter X: ..." titles with an orange rule, TU title page, roadmap with chapter badges, result slides with a
table and a figure, page number with four dots.

Output: Presentation and report/DSDR_Presentation_Chaptered.pptx
"""

import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
FIGS = os.path.join(STUDY, "report", "figures")
EQ = os.path.join(STUDY, "results", "figures", "DSDR_equations_method.png")
IMPL = os.path.join(STUDY, "results", "figures", "DSDR_equations_impl.png")
OUT = os.path.join(os.path.dirname(STUDY), "Presentation and report", "DSDR_Presentation_Chaptered.pptx")

NAVY, ORANGE, BLUE = RGBColor(0x0B, 0x25, 0x45), RGBColor(0xF4, 0xA1, 0x1A), RGBColor(0x00, 0x67, 0xB1)
INK, GREY, MID = RGBColor(0x11, 0x11, 0x11), RGBColor(0x77, 0x77, 0x77), RGBColor(0x44, 0x44, 0x44)
BOX, BOXLINE, WARM, HEAD = RGBColor(0xF7, 0xF9, 0xFC), RGBColor(0xD9, 0xDE, 0xE5), RGBColor(0xFF, 0xF8, 0xE8), RGBColor(0xE9, 0xEC, 0xEF)
GREEN, RED = RGBColor(0x1E, 0x7B, 0x34), RGBColor(0xC6, 0x28, 0x28)
FONT = "Times New Roman"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
COUNT = [0]


def run(p, text, size=16, bold=False, italic=False, color=INK):
    r = p.add_run()
    r.text = text
    f = r.font
    f.name, f.size, f.bold, f.italic = FONT, Pt(size), bold, italic
    f.color.rgb = color
    return r


def rich(p, text, size, color=INK):
    """**bold** segments"""
    for k, part in enumerate(text.split("**")):
        if part:
            run(p, part, size, bold=(k % 2 == 1), color=color)


def textbox(s, x, y, w, h, lines, size=16, color=INK, align=None, bullet=False, space=6, anchor=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    if anchor:
        tf.vertical_anchor = anchor
    for k, line in enumerate(lines if isinstance(lines, list) else [lines]):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.space_after = Pt(space)
        if align:
            p.alignment = align
        if bullet:
            ppr = p._p.get_or_add_pPr()
            ppr.set("marL", str(Inches(0.3)))
            ppr.set("indent", str(-Inches(0.3)))
            bu = etree.SubElement(ppr, qn("a:buChar"))
            bu.set("char", "•")
        rich(p, line, size, color)
    return tb


def box(s, x, y, w, h, text, size=15, fill=BOX, line=BOXLINE):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = 0.12
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line
    sh.line.width = Pt(1)
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.15)
    rich(tf.paragraphs[0], text, size)
    return sh


def slide(title, note=""):
    s = prs.slides.add_slide(BLANK)
    COUNT[0] += 1
    textbox(s, 0.62, 0.37, 12.0, 0.6, title, size=28, color=NAVY).text_frame.paragraphs[0].runs[0].font.bold = True
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.62), Inches(1.10), Inches(4.07), Inches(1.10))
    ln.line.color.rgb = ORANGE
    ln.line.width = Pt(2)
    footer(s)
    s.notes_slide.notes_text_frame.text = note
    return s


def footer(s):
    textbox(s, 11.9, 6.93, 0.6, 0.3, str(COUNT[0]), size=11, color=GREY, align=PP_ALIGN.RIGHT)
    for k in range(4):
        d = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(12.60 + 0.18 * k), Inches(7.05), Inches(0.07), Inches(0.07))
        d.fill.solid()
        d.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        d.line.color.rgb = BLUE
        d.line.width = Pt(0.75)
        d.shadow.inherit = False


def picture(s, name, x, y, w, h, cap=None, sub=None):
    path = name if os.path.isabs(name) else os.path.join(FIGS, name)
    iw, ih = Image.open(path).size
    k = min(w / iw, h / ih)
    pw, ph = iw * k, ih * k
    top = y if (cap or sub) else y + (h - ph) / 2            # with a caption: picture at the top, caption under it
    s.shapes.add_picture(path, Inches(x + (w - pw) / 2), Inches(top), Inches(pw), Inches(ph))
    if cap:
        textbox(s, x, top + ph + 0.04, w, 0.3, cap, size=12, color=MID, align=PP_ALIGN.CENTER, space=0)
    if sub:
        textbox(s, x, top + ph + 0.32, w, 0.5, sub, size=11, color=RGBColor(0x66, 0x66, 0x66), align=PP_ALIGN.CENTER, space=0)


def _border(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = etree.SubElement(tcPr, qn(tag))
        ln.set("w", "9525")
        fill = etree.SubElement(ln, qn("a:solidFill"))
        etree.SubElement(fill, qn("a:srgbClr")).set("val", "444444")


def table(s, rows, x, y, w, widths, size=13, row_h=0.4, colors=None, center_from=1):
    """first row is the header; colors: {(row, col): RGBColor} for the text"""
    colors = colors or {}
    gt = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    tbl = gt.table
    tblPr = gt._element.graphic.graphicData.tbl.tblPr
    for a in ("firstRow", "bandRow"):
        tblPr.set(a, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None:
        sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"          # no style, table grid
    tot = float(sum(widths))
    for j, cw in enumerate(widths):
        tbl.columns[j].width = Inches(w * cw / tot)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.fill.solid()
            c.fill.fore_color.rgb = HEAD if i == 0 else RGBColor(0xFF, 0xFF, 0xFF)
            c.margin_left = c.margin_right = Inches(0.07)
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]
            if j >= center_from:
                p.alignment = PP_ALIGN.CENTER
            col = colors.get((i, j), INK)
            for k, part in enumerate(str(val).split("**")):
                if part:
                    run(p, part, size, bold=(i == 0 or k % 2 == 1 or (i, j) in colors), color=col)
            _border(c)
    return gt


# ================================================================================================ 1 title
s = prs.slides.add_slide(BLANK)
COUNT[0] += 1
picture(s, "tu_logo.png", 5.89, 0.32, 1.55, 1.55)
textbox(s, 0, 1.98, 13.333, 0.3, "TRIBHUVAN UNIVERSITY", size=14, align=PP_ALIGN.CENTER, space=0)
textbox(s, 0, 2.26, 13.333, 0.6, ["Institute of Engineering", "Pulchowk, Lalitpur"], size=12, align=PP_ALIGN.CENTER, space=0)
textbox(s, 0, 2.85, 13.333, 0.6, ["Project Report Presentation", "on"], size=12, color=MID, align=PP_ALIGN.CENTER, space=0)
textbox(s, 0.75, 3.50, 11.85, 1.6, ["**AN ADAPTIVE OVERCURRENT PROTECTION SCHEME FOR DUAL-SETTING**",
                                    "**DIRECTIONAL RECLOSER AND FUSE COORDINATION IN UNBALANCED**",
                                    "**DISTRIBUTION NETWORKS WITH DISTRIBUTED GENERATION**"],
        size=21, color=RGBColor(0, 0, 0), align=PP_ALIGN.CENTER, space=8)
textbox(s, 1.10, 5.60, 4.1, 1.0, ["Submitted To", "Department of Electrical Engineering", "Pulchowk, Lalitpur"],
        size=14, color=RGBColor(0, 0, 0), align=PP_ALIGN.CENTER, space=4)
textbox(s, 8.9, 5.60, 3.6, 1.0, ["Submitted By", "Jhala Nath Kafle", "081MSPSE009"], size=14,
        color=RGBColor(0, 0, 0), align=PP_ALIGN.CENTER, space=4)
textbox(s, 4.67, 6.95, 4.0, 0.3, "OCTOBER, 2026", size=13, color=RGBColor(0, 0, 0), align=PP_ALIGN.CENTER, space=0)
s.notes_slide.notes_text_frame.text = (
    "Good afternoon. I am Jhala Nath Kafle, roll number 081 MSPSE 009. My project is an adaptive overcurrent "
    "protection scheme for dual-setting directional recloser and fuse coordination in unbalanced distribution "
    "networks with distributed generation.")

# ================================================================================================ 2 abstract
s = slide("Abstract",
          "The study implements a dual-setting directional recloser, or DSDR, on the IEEE 13-node feeder in "
          "PowerFactory. With the DG, a conventional recloser keeps coordination in 24 of 39 fault cells. The DSDR "
          "with a fuse revision raises this to 38 of 39. The core message: the dual setting is necessary, but it "
          "is not sufficient without the fuse revision.")
textbox(s, 0.70, 1.20, 11.8, 0.35, "IEEE 13-node feeder, 4.16 kV, with a 4.05 MVA synchronous DG at node 692, in DIgSILENT PowerFactory",
        size=14, color=MID, space=0)
textbox(s, 0.85, 1.75, 11.6, 3.6, [
    "A DG changes the magnitude and the direction of the fault current, so conventional recloser–fuse (fuse-saving) coordination can be lost.",
    "The study implements a dual-setting directional recloser (DSDR): the mid-line recloser gets independent forward and reverse settings.",
    "The work uses unbalanced load flow, short-circuit studies for LG, LL, LLG and LLL faults, manufacturer-based relay and fuse curves, and an EMT simulation.",
    "With the DG, a conventional recloser keeps coordination in **24 of 39** fault cells; the DSDR alone in 25.",
    "The DSDR with a revision of the fuse sizes keeps **38 of 39** cells; the remaining LG fault at node 692 is limited by the delayed dial range."],
    size=17, bullet=True, space=11)
box(s, 0.95, 5.55, 11.3, 0.75, "**Core message:** the dual setting restores the coordination between the grid and the DG, but only together with the fuse revision.",
    size=16, fill=WARM, line=ORANGE)

# ================================================================================================ 3 roadmap
s = slide("Presentation Roadmap", "I will go through five chapters: introduction, literature, methodology, results and conclusion.")
for k, (ch, txt) in enumerate([
        ("Chapter I", "Introduction, problem statement, objectives and scope"),
        ("Chapter II", "Literature review, research gap and positioning of the project"),
        ("Chapter III", "Methodology: test system, flowchart, formulation and protection settings"),
        ("Chapter IV", "Results and discussion: coordination without DG and with DG; DG penetration; the DSDR; EMT check"),
        ("Chapter V", "Conclusion, recommendation and future scope"),
        ("References", "Method, test feeder and device sources")]):
    y = 1.30 + 0.82 * k
    b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.95), Inches(y), Inches(1.45), Inches(0.40))
    b.fill.solid()
    b.fill.fore_color.rgb = NAVY
    b.line.color.rgb = NAVY
    b.shadow.inherit = False
    b.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = b.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run(p, ch, 15, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    textbox(s, 2.70, y - 0.01, 9.8, 0.42, txt, size=17, space=0, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================================================ 4 background
s = slide("Chapter I: Background and Problem",
          "In a fuse-saving scheme the recloser trips first on its fast curve, so a temporary fault clears and the "
          "fuse is saved. For a permanent fault the delayed curve lets the fuse clear its lateral. This works only "
          "while the recloser and the fuse carry the same current. With a DG, the fuse carries grid plus DG current, "
          "the recloser only the grid part, and a mid-line recloser can see reverse current. The fuse may then melt "
          "before the fast trip.")
textbox(s, 0.81, 1.40, 6.1, 3.9, [
    "Fuse saving: the recloser trips on its fast curve before the lateral fuse melts; its delayed curve lets the fuse clear a permanent fault.",
    "Coordination holds only while the recloser and the fuse carry the **same current**.",
    "With a DG the fuse carries grid + DG current; the recloser only the grid share.",
    "A mid-line recloser can see current in the **reverse** direction.",
    "The fuse can melt before the fast trip: fuse saving is lost."], size=16, bullet=True, space=9)
picture(s, "fig01.png", 7.25, 1.35, 5.3, 3.75, "Conventional recloser–fuse coordination (R1 and fuse F646)",
        "Fast curve below the fuse band, delayed curve above it.")
box(s, 1.05, 5.95, 11.2, 0.75, "**Problem focus:** can independent forward and reverse settings of the mid-line recloser restore the recloser–fuse coordination when a DG is connected?", size=15)

# ================================================================================================ 5 objectives
s = slide("Chapter I: Objectives and Study Scope",
          "The general objective is to build and validate a PowerFactory implementation of the DSDR method on the IEEE "
          "13-node feeder, with and without DG. The specific objectives cover the model, the studies, the settings, "
          "the coordination without and with the DG, the dual setting, the time-domain check and the DG penetration.")
textbox(s, 0.82, 1.22, 11.7, 0.35, "**General Objective**", size=19, color=NAVY, space=0)
box(s, 0.82, 1.62, 11.7, 0.85, "To build and validate a DIgSILENT PowerFactory implementation of the dual-setting directional recloser (DSDR) coordination method on the IEEE 13-node feeder, with and without distributed generation.", size=15)
textbox(s, 0.82, 2.62, 11.7, 0.35, "**Specific Objectives**", size=19, color=NAVY, space=0)
textbox(s, 0.95, 3.02, 11.6, 3.1, [
    "1.  To build and verify the IEEE 13-node feeder with its recloser and fuse protection.",
    "2.  To perform unbalanced load-flow and short-circuit studies for LG, LL, LLG and LLL faults.",
    "3.  To calculate the recloser pickups, time dials and fuse coefficients.",
    "4.  To establish the coordination without DG, and with a 4.05 MVA synchronous DG at node 692.",
    "5.  To design the DSDR settings of R2 and classify the resulting coordination.",
    "6.  To verify the reclosing sequence in the time domain (EMT simulation).",
    "7.  To study the effect of the DG penetration level from 0 to 100 %."], size=15, space=4)
box(s, 1.0, 6.2, 11.5, 0.6, "**Scope:** IEEE 13-node feeder; 12 fault locations × 4 fault types = 39 cells; one DG location (692); zero-margin criterion CTI > 0.",
    size=14, fill=WARM, line=ORANGE)

# ================================================================================================ 6 literature
s = slide("Chapter II: Literature Positioning and Gap",
          "The literature gives four streams: fuse-saving coordination with DG, the dual-setting directional recloser "
          "method that this project implements, the relay characteristics, and the test feeder with its short-circuit "
          "benchmark. The gap is an independent implementation with device-specific curves, dial ranges and fuse sizes.")
table(s, [["Literature stream", "Representative sources", "Relevance and remaining gap"],
          ["Recloser–fuse coordination with DG", "Naiem et al. [3]", "Classifies when coordination holds or is lost with DG; fixed, single settings."],
          ["Dual-setting directional recloser", "Yousaf et al. [1]", "The method implemented here; R2 settings and fuse sizes are not fully specified."],
          ["Relay characteristics", "Benmouyal et al. [2]; GE Multilin [4]", "Inverse-time equations; the method uses a generic curve, real relays have fixed curves and dial ranges."],
          ["Test feeder and benchmark", "Kersting [5]; Kersting & Shirek [7]; Yousaf et al. [6]", "IEEE 13-node data and short-circuit benchmark used to validate the model."]],
      0.9, 1.40, 11.6, [3.0, 3.3, 5.3], size=14, row_h=0.78, center_from=9)
box(s, 0.9, 5.65, 11.6, 0.75, "**Gap addressed:** an independent PowerFactory implementation of the DSDR method with manufacturer-based curves, real dial ranges and standard fuse sizes.",
    size=15, fill=WARM, line=ORANGE)

# ================================================================================================ 7 system
s = slide("Chapter III: Study System and Inputs",
          "This is the PowerFactory model: a 4.16 kV feeder fed from a 115 kV grid, a 4.05 MVA synchronous generator "
          "at node 692, R1 at the feeder head, R2 on line 632 to 671, and fuses on the laterals.")
table(s, [["Item", "Methodological definition"],
          ["Test system", "IEEE 13-node feeder, 4.16 kV, unbalanced"],
          ["Source", "115 kV grid, 5 MVA substation transformer"],
          ["DG", "4.05 MVA synchronous machine at node 692"],
          ["R1 (feeder head)", "GE IAC77B801A, extremely inverse"],
          ["R2 (line 632\u2013671)", "GE/Alstom CDG34 \u2013 becomes the DSDR"],
          ["Fuses", "A055C, E-rated, on the laterals"],
          ["Studies", "Unbalanced load flow, short circuit, EMT"]],
      0.5, 1.30, 6.3, [2.3, 4.0], size=13, row_h=0.37, center_from=9)
textbox(s, 0.5, 4.36, 6.3, 0.3, "**Parameters of the synchronous DG**", size=14, color=NAVY, space=0)
table(s, [["Parameter", "Value", "Parameter", "Value"],
          ["Rating Sn", "4.05 MVA", "Xd", "1.4 pu"],
          ["Voltage Un", "0.69 kV", "X'd", "0.231 pu"],
          ["Step-up transformer", "0.69 / 4.16 kV", "X''d", "0.118 pu"],
          ["Transformer reactance xT", "0.15 pu", "Starting time M = 2H", "1.5 s"],
          ["Operating point", "3.24 MW", "Stator resistance Ra", "0.0014 pu"]],
      0.5, 4.70, 6.3, [2.1, 1.15, 1.9, 1.15], size=11.5, row_h=0.32, center_from=9)
picture(s, "sld.png", 7.0, 1.25, 5.9, 4.5, "IEEE 13-node feeder with reclosers R1, R2, fuses and the DG")

# ================================================================================================ 8 flowchart
s = slide("Chapter III: Overall Methodology Flowchart",
          "The method has three stages: A, the conventional design without DG; B, the same settings with the DG; and "
          "C, R2 as a DSDR. If coordination is lost, the time dial is revised first, and at the dial limit the fuse "
          "is made larger.")
picture(s, "flowchart.png", 6.6, 1.2, 6.2, 5.7)
textbox(s, 0.81, 1.45, 5.6, 4.2, [
    "**Stage A:** conventional scheme without DG; pickup I_p = 1.25 × I_nom; fuses sized and checked.",
    "**Stage B:** the same settings with the DG connected; all 39 cells classified.",
    "**Stage C:** R2 as a DSDR; reverse pickup from the reverse load current; forward and reverse dials.",
    "If coordination is lost: revise the time dial; at the dial limit, upgrade the fuse size."], size=16, bullet=True, space=10)
box(s, 0.9, 5.55, 5.4, 0.9, "**Check:** the fuse must not start to melt before the fast trip, and must clear before the delayed trip.", size=15)

# ================================================================================================ 9 formulation
s = slide("Chapter III: Mathematical Formulation of the Method",
          "These are the equations of the method: the recloser curve with a fast and a delayed time dial, the pickup "
          "from the load current, the fuse line on log-log axes, and the coordination conditions.")
picture(s, EQ, 0.4, 1.2, 12.5, 5.6)

# ================================================================================================ 9b curves used
s = slide("Chapter III: Formulation Used for the Operating Times",
          "The method writes the operating time as the time dial times a function of the current. I kept this "
          "structure and used the manufacturer's curve of each relay: the GE IAC equation for R1 and the "
          "manufacturer's table for the CDG34. As a check, R1 reproduces the worked example of the reference paper.")
picture(s, IMPL, 0.6, 1.2, 12.1, 4.0)
textbox(s, 0.85, 5.25, 11.7, 1.5, [
    "The method fixes the structure **t = TDS × g(M)**, with M = I_f / I_p; the constants A, B and n describe only a generic curve.",
    "So g(M) is taken from the manufacturer of each relay: the IAC extremely inverse equation for R1, the CDG34 table for R2.",
    "Check: R1 gives **0.096 / 1.926 s** at 4219 A, against 0.097 / 1.932 s in the reference paper."],
    size=15, bullet=True, space=6)

# ================================================================================================ 10 settings
s = slide("Chapter III: Protection Settings",
          "R1 has a pickup of 720 amperes. R2 forward uses plugs of 300 and 600 amperes, and the new reverse group "
          "150 and 300 amperes. The dials were already at their limits, so the fuse sizes were revised.")
table(s, [["Device", "Characteristic", "Pickup / plug (fast / delayed)", "Dial (fast / delayed)"],
          ["R1 (feeder head)", "GE IAC extremely inverse", "720 A", "TDS 0.5 / 10"],
          ["R2 forward (grid current)", "CDG34", "300 / 600 A", "TMS 0.1 / 1.0"],
          ["R2 reverse (DG current)", "CDG34, CT 500/5", "150 / 300 A", "TMS 0.1 / 1.0"]],
      0.9, 1.45, 11.5, [3.0, 3.0, 3.2, 2.3], size=15, row_h=0.52)
textbox(s, 0.9, 3.85, 11.5, 2.2, [
    "Load current through R2: **+470 A** without DG, **−252 A** (reversed) with the DG → reverse pickup 1.25 × 252 = **315 A**.",
    "A dial revision could not help: R1 and R2 are already at the ends of their dial ranges.",
    "Fuse revision: F632 → 500E; F633, F646, F-DL, F671-1 → 400E; F692-R → 250E."], size=16, bullet=True, space=10)
box(s, 0.9, 5.85, 11.5, 0.65, "TDS (IAC relay) and TMS (CDG34 relay) are the manufacturers' names for the same thing: the dial that scales the curve.", size=14)

# ================================================================================================ 11 no DG
s = slide("Chapter IV: Base Case Without DG",
          "Without DG, the fault levels agree with the IEEE benchmark within about 2 per cent. 35 of 39 cells are "
          "coordinated with the starting fuses, and all 39 after one fuse change.")
table(s, [["Quantity", "Result"],
          ["Feeder-head fault level", "4.73 kA"],
          ["Agreement with the IEEE benchmark", "within about 2 %"],
          ["Cells held, starting fuse sizes", "35 of 39"],
          ["Cells held, after F692-R → 200E", "**39 of 39**"]],
      0.7, 1.45, 5.6, [3.6, 2.0], size=14, row_h=0.5, colors={(4, 1): GREEN})
textbox(s, 0.7, 4.25, 5.6, 1.8, [
    "R2's fast curve is below the fuses and its delayed curve above them.",
    "Without DG the conventional scheme works."], size=16, bullet=True, space=9)
picture(s, "fig08.png", 6.7, 1.25, 6.1, 4.6, "LG fault at 611: R2 fast 0.128 s < F684 melts 0.271 s – coordination held")

# ================================================================================================ 11b Table II
import csv as _csv
CMP = os.path.join(STUDY, "results", "comparison")
rd = lambda f: list(_csv.DictReader(open(os.path.join(CMP, f), encoding="utf-8")))
s = slide("Chapter IV: Branch Currents and Fault Levels – Side by Side",
          "This compares the base case with Table two of the reference paper and with the IEEE short-circuit "
          "benchmark. The rated currents agree with the paper within 2 per cent. My fault levels are lower than the "
          "paper's, so I checked both against the benchmark: my model agrees within 2 per cent at ten of eleven "
          "nodes, while the paper's values are 4 to 151 per cent higher.")
T2 = rd("Table_II_vs_paper.csv")
FB = {r["Node"]: r for r in _csv.DictReader(open(os.path.join(STUDY, "results", "Fault_level_benchmark.csv"), encoding="utf-8"))}
br = lambda r: ("%s %s" % (r["From"], r["To"])) if r["From"].startswith("XFM") else "%s–%s" % (r["From"], r["To"])
rows = [["Branch", "I nom (A) study", "I nom (A) paper", "If,min (kA) study", "If,min (kA) paper",
         "If,max (kA) IEEE [7]", "If,max (kA) study", "If,max (kA) paper", "Study vs IEEE", "Paper vs IEEE"]]
cols = {}
for k, r in enumerate(T2, 1):
    f = FB.get(r["To"])
    base = [br(r), r["Inom (A)"], r["paper Inom (A)"], "%.2f" % float(r["If,min (kA)"]), "%.2f" % float(r["paper If,min (kA)"])]
    if f:
        ds, dp = float(f["Study vs benchmark (%)"]), float(f["Paper vs benchmark (%)"])
        rows.append(base + ["%.2f" % float(f["IEEE benchmark (kA)"]), "%.2f" % float(f["This study (kA)"]),
                            "%.2f" % float(r["paper If,max (kA)"]), "%+.1f %%" % ds, "%+.1f %%" % dp])
        cols[(k, 8)] = GREEN
        if abs(dp) > 10:
            cols[(k, 9)] = RED
    else:
        rows.append(base + ["\u2013", "%.2f" % float(r["If,max (kA)"]), "%.2f" % float(r["paper If,max (kA)"]), "\u2013", "\u2013"])
table(s, rows, 0.4, 1.25, 12.55, [1.55, 1.05, 1.05, 1.1, 1.1, 1.2, 1.15, 1.15, 1.1, 1.1], size=10.5, row_h=0.30, colors=cols)
textbox(s, 0.4, 5.52, 12.55, 0.3, "IEEE benchmark: [7] W. H. Kersting and G. Shirek, \u201cShort circuit analysis of IEEE test feeders,\u201d IEEE PES T&D, 2012 (maximum fault current, DG out). Paper: reference [1], Table II.",
        size=10.5, color=MID, space=0)
ds_all = [abs(float(f["Study vs benchmark (%)"])) for f in FB.values()]
dp_all = [float(f["Paper vs benchmark (%)"]) for f in FB.values()]
box(s, 0.4, 6.05, 12.55, 0.78, "**Rated currents agree with the paper within 2 %%.** If,max: this study is within 2 %% of the IEEE benchmark at %d of %d nodes (largest %.1f %%); the paper is %.0f %% to %.0f %% higher. If,min on the 4.16 kV lines: 0.64 to 1.07 kA here, 0.59 to 1.24 kA in the paper." % (
    sum(d <= 2.0 for d in ds_all), len(FB), max(ds_all), min(dp_all), max(dp_all)), size=12.5, fill=WARM, line=ORANGE)

# ================================================================================================ 11c Table III
s = slide("Chapter IV: Fuse Coefficients – Side by Side",
          "These are the fuse coefficients b against Table three of the reference paper. They agree within about "
          "0.3 for every fuse; the small differences follow the lower fault currents.")
T3 = rd("Table_III_vs_paper.csv")
rows = [["Fuse", "If (A)", "t fast (s)", "t delayed (s)", "b (this study)", "b (paper, Table III)", "Difference"]]
for r in T3:
    a_, b_ = float(r["b_i (i counted from source)"]), float(r["paper b_i"])
    rows.append([r["Fuse"], r["If (A)"], r["t_fast (s)"], r["t_delayed (s)"], "%.2f" % a_, "%.2f" % b_, "%+.2f" % (a_ - b_)])
table(s, rows, 1.2, 1.3, 10.9, [1.2, 1.3, 1.4, 1.5, 1.8, 2.0, 1.5], size=11, row_h=0.29)
dmax = max(abs(float(r[6])) for r in rows[1:])
box(s, 1.2, 6.1, 10.9, 0.65, "Fuse line: log t = a log I + b, with a = −1.8. The coefficients agree within **%.2f** for all %d fuses." % (dmax, len(rows) - 1),
    size=13, fill=WARM, line=ORANGE)

# ================================================================================================ 12 DG conventional
s = slide("Chapter IV: DG Connected, Conventional R2",
          "With the DG and unchanged settings, coordination holds in only 24 of 39 cells. The fuse melts before the "
          "fast trip, and for some line-to-ground faults R2 does not even pick up the reverse current.")
table(s, [["Metric", "Value"],
          ["Cells held", "**24 of 39**"],
          ["Cells lost", "15"],
          ["Lost at nodes", "633, 645, 646, DL, 675"],
          ["Example: three-phase fault near 632", "R2 trips 0.121 s; fuse melts 0.039 s"]],
      0.6, 1.45, 5.9, [3.0, 2.9], size=14, row_h=0.55, colors={(1, 1): RED})
textbox(s, 0.6, 4.45, 5.9, 1.9, [
    "The fuse carries grid + DG current and melts before the fast trip.",
    "For some LG faults the single-setting R2 does not pick up the reverse DG current."], size=16, bullet=True, space=9)
picture(s, "fig14.png", 6.8, 1.3, 6.0, 4.4, "Coordination status with DG, conventional R2", "Green: held. Red: lost.")

# ================================================================================================ 12b Fig 14 grid
s = slide("Chapter IV: Coordination with DG – Side by Side",
          "This is the coordination status with the DG and a conventional R2, cell by cell: my study above and the "
          "reference paper below. I obtained 24 held cells and the paper 30. We agree in 29 of the 39 cells: 22 held "
          "in both and 7 lost in both. Of the 10 that differ, 8 are lost only in my study, four of them at the "
          "distributed load, and 2 are lost only in the paper.")
G = rd("Fig14_Fig17_vs_paper.csv")
nodes = []
for r in G:
    if r["node"] not in nodes:
        nodes.append(r["node"])
FT = ["LG", "LL", "LLG", "LLL"]
SYM = {"held": "✓", "lost": "×", "n/a": "–"}


def grid(col, y, label):
    look = {(r["node"], r["fault"]): r[col] for r in G}
    rows_ = [["Fault"] + nodes] + [[ft] + [SYM.get(look.get((n, ft), "n/a"), "–") for n in nodes] for ft in FT]
    cols = {}
    for i, ft in enumerate(FT, 1):
        for j, n in enumerate(nodes, 1):
            v = look.get((n, ft), "n/a")
            if v in ("held", "lost"):
                cols[(i, j)] = GREEN if v == "held" else RED
    held = sum(v == "held" for v in look.values())
    tot = sum(v in ("held", "lost") for v in look.values())
    textbox(s, 0.7, y - 0.4, 11.9, 0.35, "**%s** – coordination held in %d of %d cells" % (label, held, tot), size=15, color=NAVY, space=0)
    table(s, rows_, 0.7, y, 11.9, [1.1] + [0.9] * len(nodes), size=13, row_h=0.36, colors=cols)


grid("Fig14 model", 1.65, "This study")
grid("Fig14 paper", 4.05, "Reference paper [1], Fig. 14")
cells = [r for r in G if r["Fig14 model"] in ("held", "lost")]
n_hh = sum(r["Fig14 model"] == "held" and r["Fig14 paper"] == "held" for r in cells)
n_ll = sum(r["Fig14 model"] == "lost" and r["Fig14 paper"] == "lost" for r in cells)
here = [r for r in cells if r["Fig14 model"] == "lost" and r["Fig14 paper"] == "held"]
there = [r for r in cells if r["Fig14 model"] == "held" and r["Fig14 paper"] == "lost"]
box(s, 0.7, 6.0, 11.9, 0.78, "**Agree in %d of %d cells** (%d held in both, %d lost in both). Differ in %d: %d lost only here (%d of them at DL), %d lost only in the paper (%s). With the DSDR: 38 of 39 here, 39 of 39 in the paper." % (
    n_hh + n_ll, len(cells), n_hh, n_ll, len(here) + len(there), len(here), sum(r["node"] == "DL" for r in here),
    len(there), ", ".join(sorted(set(r["node"] for r in there)))), size=13, fill=WARM, line=ORANGE)

# ================================================================================================ 16 penetration
s = slide("Chapter IV: Effect of the DG Penetration Level \u2013 Side by Side",
          "Seven models with the DG from 0 to 100 per cent and the conventional settings show the CTI falling: at 633 from plus 4 to minus 51 "
          "milliseconds, at 671 from 403 to 75 milliseconds. The table gives the share of the CTI at each level "
          "next to the values read from the paper's figure. Both fall steadily as the DG grows. In my study node "
          "633 is negative from 10 per cent, in the paper from 50 per cent, because my starting margin there is "
          "only 4 milliseconds. This is why a setting that adapts to the DG is needed.")
# share of the CTI at each penetration level (ring %): this study and the values read from the paper's Fig. 7
PEN = [("0", "+2.1", "+30", "+26.0", "+36"), ("10", "\u22123.1", "+23", "+21.5", "+22"), ("25", "\u22129.6", "+14", "+16.4", "+12"),
       ("37", "\u221213.9", "+6", "+13.4", "+6"), ("50", "\u221217.9", "\u22124", "+10.7", "0"),
       ("75", "\u221224.2", "\u22129", "+7.1", "\u22128"), ("100", "\u221229.2", "\u221216", "+4.9", "\u221214")]
rows = [["DG (%)", "Node 633 study", "Node 633 paper", "Node 671 study", "Node 671 paper"]] + [list(r) for r in PEN]
cols = {}
for i, r in enumerate(PEN, 1):
    for j in (1, 2, 3, 4):
        if r[j].startswith("\u2212"):
            cols[(i, j)] = RED
table(s, rows, 0.5, 1.35, 6.2, [0.9, 1.35, 1.35, 1.35, 1.35], size=12.5, row_h=0.37, colors=cols, center_from=0)
textbox(s, 0.5, 4.40, 6.2, 0.3, "Share of the CTI at each penetration level (%). Paper: values read from Fig. 7 of [1].", size=10.5, color=MID, space=0)
textbox(s, 0.5, 4.78, 6.2, 1.2, [
    "This study, in time: CTI at 633 from **+4 ms to \u221251 ms**; at 671 from **+403 ms to +75 ms**.",
    "The fuse carries grid + DG current, the recloser only the grid share."], size=14, bullet=True, space=5)
picture(s, "pen_ring_vs_paper.png", 6.95, 1.3, 6.0, 4.2, "This study (left) and the reference paper (right)", "Outer ring: node 671. Inner ring: node 633.")
box(s, 0.5, 6.05, 12.4, 0.75, "**Same trend in both:** the CTI falls steadily as the DG penetration rises. Node 633 turns negative from 10 % here and from 50 % in the paper, because the starting margin here is only +4 ms.",
    size=13, fill=WARM, line=ORANGE)

# ================================================================================================ 13 DSDR
s = slide("Chapter IV: With the DSDR",
          "With R2 as a DSDR and revised fuses, 38 of 39 cells are held. With the same revised fuses but a "
          "single-setting R2, only 31, so the dual setting itself restores seven cells. The DSDR with the old fuses "
          "gives only 25, so it needs the fuse revision. Only the line-to-ground fault at 692 stays lost, limited by "
          "the maximum delayed dial of R2.")
table(s, [["Scheme (DG connected)", "Cells held"],
          ["Conventional R2, original fuses", "24"],
          ["DSDR, original fuses", "25"],
          ["Conventional R2, revised fuses", "31"],
          ["DSDR, revised fuses", "**38 of 39**"]],
      0.6, 1.45, 5.9, [4.0, 1.9], size=14, row_h=0.5, colors={(4, 1): GREEN})
textbox(s, 0.6, 4.2, 5.9, 2.3, [
    "The dual setting itself restores **7 cells**: all faults at 633 and the LG faults at 645, 646 and DL.",
    "Still lost: LG fault at 692 – R2's delayed dial is already at its maximum."], size=16, bullet=True, space=9)
picture(s, "fig17.png", 6.8, 1.3, 6.0, 4.4, "Coordination status with the DSDR and revised fuses", "Only one cell remains lost.")

# ================================================================================================ 13a TCC with the DSDR
s = slide("Chapter IV: TCC with the DSDR \u2013 Bolted LL Fault at 646",
          "This is the time-current plot of one fault with the DSDR: a bolted line-to-line fault at 646. The fuses "
          "carry 3.67 kiloamperes, the grid plus the DG current. R2 sees the DG share, 1114 amperes in reverse, and "
          "its reverse group trips in 0.086 seconds. R1 sees the grid share and trips in 0.189 seconds. Both are "
          "before the fuse starts to melt at 0.415 seconds, so the fuse is saved.")
picture(s, "fig15.png", 0.35, 1.2, 6.25, 3.75, "R2 reverse group (DG share, 1114 A): fast trip 0.086 s")
picture(s, "fig16.png", 6.75, 1.2, 6.25, 3.75, "R1 (grid share, 2785 A): fast trip 0.189 s")
table(s, [["Device", "Current", "Operates at", "Result"],
          ["R2, reverse group", "1114 A (DG share)", "0.086 s", "trips first"],
          ["R1", "2785 A (grid share)", "0.189 s", "trips second"],
          ["Fuse F646 (400E)", "3672 A (grid + DG)", "starts to melt at 0.415 s", "**saved**, CTI = +226 ms"]],
      0.9, 5.42, 11.5, [2.6, 2.8, 3.2, 2.9], size=12.5, row_h=0.33, colors={(3, 3): GREEN})

# ================================================================================================ 13b Table IV
s = slide("Chapter IV: Operating Times with the DSDR – Side by Side",
          "This is the table of operating times with the DSDR, my study on the left and Table four of the "
          "reference paper on the right. In every row of both, the fuse melts after the fast trip of the recloser "
          "that protects it. R1's delayed time is twenty times its fast time in both, which confirms the dials. My "
          "R1 times are mostly slower because my fault levels follow the IEEE benchmark and are lower.")
import csv
T4 = list(csv.DictReader(open(os.path.join(STUDY, "results", "comparison", "Table_IV_vs_paper.csv"))))
dash = lambda v: "–" if v in ("---", "") else v
HD = ["Node", "Fault", "R1 fast", "R1 delayed", "R2 fast", "R2 delayed", "Fuse melts"]
mine = [HD] + [[r["node"], r["fault"], dash(r["R1 fast (s)"]), dash(r["R1 delayed (s)"]), dash(r["R2 fast (s)"]),
                dash(r["R2 delayed (s)"]), dash(r["fuse MMT (s)"])] for r in T4]
paper = [HD] + [[r["node"], r["fault"], dash(r["paper R1 fast"]), dash(r["paper R1 delayed"]), dash(r["paper R2 fast"]),
                 dash(r["paper R2 delayed"]), dash(r["paper fuse MMT"])] for r in T4]
W = [0.7, 0.7, 0.95, 1.15, 0.95, 1.15, 1.15]
textbox(s, 0.35, 1.22, 6.2, 0.35, "**This study** (times in s)", size=15, color=NAVY, align=PP_ALIGN.CENTER, space=0)
textbox(s, 6.78, 1.22, 6.2, 0.35, "**Reference paper [1], Table IV** (times in s)", size=15, color=NAVY, align=PP_ALIGN.CENTER, space=0)
table(s, mine, 0.35, 1.62, 6.2, W, size=11, row_h=0.33)
table(s, paper, 6.78, 1.62, 6.2, W, size=11, row_h=0.33)
box(s, 0.35, 6.05, 12.63, 0.72, "**Same behaviour in both:** the fuse melts after the fast trip; R1 delayed = 20 × R1 fast (dials 0.5 / 10). R1 is slower here in most rows because the fault levels follow the IEEE benchmark; R2's settings are not published in the paper.",
    size=13, fill=WARM, line=ORANGE)

# ================================================================================================ 14 single vs dual
s = slide("Chapter IV: Single versus Dual Setting", "")
picture(s, "case05.png", 0.5, 1.2, 12.3, 3.3)
table(s, [["Quantity", "Single setting", "Dual setting (DSDR)"],
          ["Current through R2", "1777 A, reverse", "1777 A, reverse"],
          ["R2 setting used", "Forward: plug 300 / 600 A", "Reverse: plug 150 / 300 A"],
          ["R2 fast trip", "0.121 s", "0.052 s"],
          ["F633 (400E) starts to melt", "0.100 s", "0.100 s"],
          ["Fuse saving", "LOST", "HELD"]],
      1.9, 4.6, 9.5, [3.2, 3.2, 3.1], size=13, row_h=0.34, colors={(5, 1): RED, (5, 2): GREEN})

# ================================================================================================ 15 EMT
s = slide("Chapter IV: Time-Domain (EMT) Verification",
          "This EMT simulation is a line-to-line fault at 684. Without DG, the two fast shots use only 45 per cent of "
          "the fuse's melting heat, and the fuse then clears the permanent fault. With the DG, current keeps flowing "
          "while R2 is open, and the fuse melts at 0.75 seconds, during the second fast shot.")
table(s, [["Event", "Without DG", "With DG"],
          ["Fuse heat after two fast shots", "45 %", "105 %"],
          ["Fuse F671-2 melts", "1.248 s", "0.752 s"],
          ["Fuse F671-2 clears", "1.613 s", "1.253 s"],
          ["Fuse saving", "works", "lost"]],
      0.6, 1.45, 5.9, [3.1, 1.4, 1.4], size=14, row_h=0.5, colors={(4, 1): GREEN, (4, 2): RED})
textbox(s, 0.6, 4.2, 5.9, 2.4, [
    "LL fault (a–c) at 684 through 0.2 Ω, conventional settings.",
    "With the DG the fuse carries more current, and the DG keeps feeding the fault while R2 is open."], size=16, bullet=True, space=9)
picture(s, "fig10.png", 6.8, 1.2, 6.0, 5.0, "Current at node 632: without DG (top), with DG (bottom)")

# ================================================================================================ 17 summary
s = slide("Chapter IV: Summary and Comparison",
          "In summary: without DG, 35 cells and 39 after the fuse revision; 24 with the DG and a conventional R2; 25 "
          "with the DSDR alone, 31 with the fuse revision alone, and 38 with both. The reference paper reports 30 and "
          "39; I obtained 24 and 38. The trend is the same, and my fault levels follow the IEEE benchmark.")
table(s, [["Stage", "This study (of 39)", "Reference paper [1]"],
          ["No DG, starting fuse sizes", "35", "–"],
          ["No DG, after the fuse revision", "39", "–"],
          ["DG connected, conventional R2", "24", "30"],
          ["DG connected, original fuses, R2 as DSDR", "25", "–"],
          ["DG connected, revised fuses, conventional R2", "31", "–"],
          ["DG connected, revised fuses, R2 as DSDR", "**38**", "39"]],
      0.9, 1.45, 11.5, [5.6, 2.9, 3.0], size=15, row_h=0.50, colors={(6, 1): GREEN})
box(s, 0.9, 5.25, 11.5, 0.85, "Same trend as the reference paper. The counts differ because the model is validated against the IEEE short-circuit benchmark (feeder head 4.73 kA) and uses real dial ranges.",
    size=15, fill=WARM, line=ORANGE)

# ================================================================================================ 18 conclusion and future scope
s = slide("Chapter V: Conclusion and Future Scope", "")
textbox(s, 0.82, 1.22, 11.7, 0.35, "**Conclusion**", size=19, color=NAVY, space=0)
textbox(s, 0.85, 1.62, 11.8, 3.0, [
    "The DSDR method was implemented on the IEEE 13-node feeder in DIgSILENT PowerFactory; the model meets the IEEE benchmark within about 2 %.",
    "Without DG: **35 of 39** cells with the starting fuses, **39 of 39** after the fuse revision.",
    "With the DG, a conventional R2 keeps only **24 of 39** cells: the fuse carries grid + DG current and melts before the fast trip.",
    "DSDR alone: 25; fuse revision alone: 31; DSDR with the fuse revision: **38 of 39** (zero-margin criterion).",
    "The DSDR is **necessary but not sufficient**: it needs the fuse revision; the LG fault at 692 is limited by R2's delayed dial."],
    size=15, bullet=True, space=5)
textbox(s, 0.82, 4.72, 11.7, 0.35, "**Recommendation and Future Scope**", size=19, color=NAVY, space=0)
textbox(s, 0.85, 5.12, 11.8, 1.7, [
    "Extend the study to the IEEE 34-node feeder and to inverter-based DG.",
    "Model an explicit directional element for R2, and change the setting group with the state of the DG.",
    "Use a recloser with a wider dial range to recover the remaining cell; validate with hardware-in-the-loop tests."],
    size=15, bullet=True, space=5)

# ================================================================================================ 20 references
s = slide("References", "These are the main references.")
textbox(s, 0.75, 1.35, 11.9, 5.4, [
    "[1] M. Yousaf, A. Jalilian, K. M. Muttaqi, and D. Sutanto, “An adaptive overcurrent protection scheme for dual-setting directional recloser and fuse coordination in unbalanced distribution networks with distributed generation,” IEEE Trans. Ind. Appl., vol. 58, no. 2, pp. 1831–1842, 2022.",
    "[2] G. Benmouyal et al., “IEEE standard inverse-time characteristic equations for overcurrent relays,” IEEE Trans. Power Del., vol. 14, no. 3, pp. 868–872, 1999.",
    "[3] A. Naiem, Y. Hegazy, A. Abdelaziz, and M. Elsharkawy, “A classification technique for recloser-fuse coordination in distribution systems with distributed generation,” IEEE Trans. Power Del., vol. 27, no. 1, pp. 176–185, 2012.",
    "[4] GE Multilin, 735/737 Feeder Protection Relay – Instruction Manual (GEK-106291F), 2010.",
    "[5] W. H. Kersting, “Radial distribution test feeders,” IEEE Trans. Power Syst., vol. 6, no. 3, pp. 975–985, 1991.",
    "[6] M. Yousaf, K. M. Muttaqi, and D. Sutanto, “Overcurrent protection scheme for the IEEE 13-node benchmark test feeder with improved selectivity,” in Proc. IEEE PES General Meeting, 2020.",
    "[7] W. H. Kersting and G. Shirek, “Short circuit analysis of IEEE test feeders,” in Proc. IEEE PES T&D, 2012.",
    "[8] DIgSILENT GmbH, PowerFactory 2021 User Manual, Gomaringen, Germany, 2021."], size=13, space=7)

# ================================================================================================ 21 thank you
s = prs.slides.add_slide(BLANK)
COUNT[0] += 1
textbox(s, 0, 2.7, 13.333, 0.9, "**Thank You**", size=40, color=NAVY, align=PP_ALIGN.CENTER, space=0)
ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(4.9), Inches(3.75), Inches(8.43), Inches(3.75))
ln.line.color.rgb = ORANGE
ln.line.width = Pt(2)
textbox(s, 0, 3.95, 13.333, 0.6, "Questions and Discussion", size=22, color=MID, align=PP_ALIGN.CENTER, space=0)
footer(s)
s.notes_slide.notes_text_frame.text = "Thank you for your attention. I am happy to take your questions."

# ---- speaker notes: short, one point per slide (keyed by the start of the slide title; "" = title page)
SHORT = [
    ("", "Good afternoon. I am Jhala Nath Kafle, roll number 081 MSPSE 009. My project is on dual-setting "
         "directional recloser and fuse coordination in distribution networks with distributed generation."),
    ("Abstract", "A DG can break recloser-fuse coordination. I implemented a dual-setting directional recloser on the "
                 "IEEE 13-node feeder. With the DG, coordination holds in 24 of 39 cells; with the DSDR and revised "
                 "fuses, in 38 of 39."),
    ("Presentation Roadmap", "I will go through the introduction, literature, methodology, results and conclusion."),
    ("Chapter I: Background", "The recloser trips fast to save the fuse on a temporary fault. That works only while both "
                              "carry the same current. With a DG the fuse carries more current than the recloser, and "
                              "it can melt first."),
    ("Chapter I: Objectives", "The general objective is to build and validate the DSDR method on the IEEE 13-node feeder "
                              "in PowerFactory. There are seven specific objectives, from building the model to the DG "
                              "penetration study."),
    ("Chapter II:", "The literature covers coordination with DG, the DSDR method, relay curves and the test feeder. The gap "
                   "is an independent implementation with real relay curves, dial ranges and fuse sizes."),
    ("Chapter III: Study System", "A 4.16 kV feeder with a 4.05 MVA synchronous DG at node 692. R1 is at the feeder head, "
                                  "R2 is on line 632 to 671, and fuses protect the laterals."),
    ("Chapter III: Overall Methodology", "This flowchart is the method. First, a load flow gives the rated current of every branch, and the pickup of each recloser is set to 1.25 times that current. For R2 this is done twice: once for the forward current from the grid, and once for the reverse current from the DG. Then the fuses are sized, and a fault at every location is checked. If the fuse melts before the recloser's fast trip, coordination is lost. In that case the time dial is revised first. If the dial is already at its limit, the fuse is made larger, and the check is repeated until coordination holds."),
    ("Chapter III: Mathematical Formulation", "These are the method's equations: the recloser curve, the pickup, the fuse "
                                              "line and the coordination conditions."),
    ("Chapter III: Formulation Used", "I kept the method's structure and used each manufacturer's curve: the GE IAC "
                                      "equation for R1 and the CDG34 table for R2. R1 reproduces the paper's worked "
                                      "example."),
    ("Chapter III: Protection Settings", "R1 picks up at 720 amperes. R2 has a forward group of 300 and 600 amperes and "
                                         "a new reverse group of 150 and 300. The dials were at their limits, so the "
                                         "fuses were revised."),
    ("Chapter IV: Base Case", "Without DG, 35 of 39 cells are coordinated, and all 39 after one fuse change."),
    ("Chapter IV: Branch Currents", "Rated currents agree with the paper within 2 per cent. My fault levels match the IEEE "
                                    "benchmark within 2 per cent; the paper's are higher."),
    ("Chapter IV: Fuse Coefficients", "The fuse coefficients agree with the paper's Table three within 0.33."),
    ("Chapter IV: DG Connected", "With the DG and the same settings, only 24 of 39 cells hold. The fuse melts before the "
                                 "fast trip."),
    ("Chapter IV: Coordination with DG", "Cell by cell, I hold 24 and the paper 30. We agree in 29 of 39 cells."),
    ("Chapter IV: Effect of the DG Penetration", "As the DG grows from 0 to 100 per cent, the CTI falls: at 633 from plus "
                                                 "4 to minus 51 milliseconds. The paper shows the same trend. This is "
                                                 "why an adaptive setting is needed."),
    ("Chapter IV: With the DSDR", "With the DSDR and revised fuses, 38 of 39 cells hold. The dual setting alone restores "
                                  "seven cells. Only the LG fault at 692 stays lost, at R2's dial limit."),
    ("Chapter IV: TCC with the DSDR", "For a line-to-line fault at 646, R2 trips in 0.086 seconds on its reverse group "
                                      "and R1 in 0.189. The fuse would melt at 0.415, so it is saved."),
    ("Chapter IV: Operating Times", "My operating times next to the paper's Table four. In both, the fuse melts after "
                                    "the fast trip in every row."),
    ("Chapter IV: Single versus Dual", "Same fault, same current. With the single setting R2 trips in 0.121 seconds: "
                                       "lost. With the reverse group, 0.052 seconds: held."),
    ("Chapter IV: Time-Domain", "The EMT run confirms it in time. Without DG the fuse survives the two fast shots at 45 "
                                "per cent heat. With DG it melts during the second shot."),
    ("Chapter IV: Summary", "In summary: 24 cells with a conventional recloser, 25 with the DSDR alone, 31 with the fuse "
                            "revision alone, and 38 with both. The paper reports 30 and 39."),
    ("Chapter V: Conclusion", "To conclude: the DSDR with the fuse revision raises coordination from 24 to 38 of 39 cells. "
                              "It is necessary but not sufficient: it needs the fuse revision. Future work includes the "
                              "34-node feeder, a true directional element and inverter-based DG."),
    ("References", "These are the main references."),
    ("Thank You", "Thank you. I am happy to take your questions."),
]
for sl in prs.slides:
    title = next((sh.text_frame.text.strip() for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text.strip()), "")
    key = "" if title.startswith("TRIBHUVAN") else title
    hit = [t for k, t in SHORT if (k == "" and key == "") or (k and key.startswith(k))]
    assert len(hit) == 1, (title, len(hit))
    sl.notes_slide.notes_text_frame.text = hit[0]

out = None
for suffix in ("", "_new", "_v2", "_v3", "_v4", "_v5", "_v6"):          # a file open in PowerPoint is locked
    try:
        cand = OUT.replace(".pptx", suffix + ".pptx")
        prs.save(cand)
        out = cand
        break
    except PermissionError:
        continue
assert out, "every file name is locked: close the presentation in PowerPoint"
import re
words = sum(len(re.findall(r"[\w.']+", sl.notes_slide.notes_text_frame.text)) for sl in prs.slides)
print("saved", out, "-", len(prs.slides), "slides; notes %d words, about %.1f minutes" % (words, words / 125.0))
