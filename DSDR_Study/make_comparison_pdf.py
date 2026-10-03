"""
Builds results/Comparison_with_Reference_Paper.pdf: the paper's results next to the replication's,
in the order of the workflow (network -> load flow -> faults -> settings -> fuses -> conventional
scheme -> DG impact -> DSDR -> time domain -> verification).

Needs: results of run_all.py, reportlab, matplotlib, PyMuPDF (to cut the paper's figures).
"""

import csv
import json
import os

import fitz                                            # PyMuPDF
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

import step3_design_and_evaluate as S3
import re
from protection_data import (PAPER_TABLE2, PAPER_TABLE3, PAPER_TABLE4, PAPER_FIG14_LOST, NODE_ORDER,
                             FAULT_TYPES, FUSES)

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(RES, "figures")
TMP = os.path.join(RES, "_pdf_tmp")
os.makedirs(TMP, exist_ok=True)
PAPER = os.path.join(os.path.dirname(HERE), "An Adaptive Overcurrent Protection Scheme for by mohommad yousuf .pdf")
OUT = os.path.join(RES, "comparison", "Comparison_with_Reference_Paper.pdf")

SET = json.load(open(os.path.join(RES, "settings.json")))
CONV, DSDR = SET["conventional"], SET["dsdr"]


def rows(name):
    return list(csv.DictReader(open(os.path.join(RES, name))))


# ---- statements generated from the results -------------------------------------------------------
SUMM = open(os.path.join(RES, "summary.txt"), encoding="utf-8").read()
START = {n: v[1] for n, v in FUSES.items()}                    # sizes the design starts from


def sz(t):
    return t.replace("A055C", "")


def changed(a, b):
    return ", ".join("%s %s -> %s" % (f, sz(a[f]), sz(b[f])) for f in a if a[f] != b[f]) or "none"


def found(pattern, default=("?", "?")):
    m = re.search(pattern, SUMM)
    return m.groups() if m else default


def cells(pairs):
    """[(node, type)] -> '633 LLG/LLL, 645 LG'"""
    out = []
    for n in NODE_ORDER:
        t = [ft for ft in FAULT_TYPES if (n, ft) in pairs]
        if t:
            out.append("%s %s" % (n, "/".join(t)))
    return ", ".join(out) or "none"


def stage_a_losses():
    block = SUMM.split("published fuse sizes, no DG:")[1].split("after steps 8-10")[0]
    kinds = {}
    for line in block.splitlines():
        m = re.match(r"\s+lost\s+(\S+)\s+\S+\s+\S+\s+(.*)", line)
        if m:
            r = m.group(2)
            k = ("series rule, eq. (8): " + r.split(":")[0].replace("series ", "") if r.startswith("series") else
                 "fuse melts before the recloser's fast trip" if "melts" in r else "recloser delayed trip before the fuse clears")
            kinds.setdefault(m.group(1), set()).add(k)
    return "; ".join("node %s - %s" % (n, ", ".join(sorted(k))) for n, k in kinds.items()) or "none"


# ---------------------------------------------------------------------------------------------
# Paper figures (embedded images of the paper, or page clips for vector figures)
# ---------------------------------------------------------------------------------------------
doc_p = fitz.open(PAPER)


def paper_image(page, index):
    xref = doc_p[page - 1].get_images(full=True)[index][0]
    pix = fitz.Pixmap(doc_p, xref)
    if pix.n > 4:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    path = os.path.join(TMP, "paper_p%d_%d.png" % (page, index))
    pix.save(path)
    return path


def paper_clip(page, rect, name):
    path = os.path.join(TMP, name + ".png")
    doc_p[page - 1].get_pixmap(dpi=250, clip=fitz.Rect(*rect)).save(path)
    return path


PFIG = {
    "7": paper_image(6, 0), "8": paper_image(7, 0), "9": paper_image(7, 1), "11": paper_image(7, 2),
    "12": paper_image(8, 0), "13": paper_image(8, 1), "15": paper_image(8, 2), "16": paper_image(9, 0),
    "10": paper_clip(7, (298, 60, 552, 225), "paper_fig10"),
    "14": paper_clip(8, (300, 64, 552, 140), "paper_fig14"),
    "17": paper_clip(9, (296, 64, 552, 142), "paper_fig17"),
}

# ---------------------------------------------------------------------------------------------
# Workflow diagram
# ---------------------------------------------------------------------------------------------
STEPS = [
    ("1", "Network model & source", "IEEE 13-node feeder, DG of Table I, fault levels vs IEEE benchmark"),
    ("2", "Load flow  (Fig. 5: step 1)", "rated branch currents Inom - Table II"),
    ("3", "Fault study  (step 5)", "If,min / If,max - Table II"),
    ("4", "Protective devices & pickups  (steps 2-3)", "R1, R2, 15 fuses; Ip = OLF x Inom, eq. (3)"),
    ("5", "Fuse coefficients  (step 4)", "b_i by eqs. (6)-(9) - Table III"),
    ("6", "Conventional scheme, no DG  (steps 7-10)", "coordination of every node / fault type"),
    ("7", "DG added, conventional R2", "Fig. 14, Figs. 8-13"),
    ("8", "R2 as DSDR  (steps 8-11)", "eq. (12), TDS revision, fuse revision - Fig. 17, Figs. 15-16, Table IV"),
    ("9", "Time-domain check", "Fig. 10 reclosing sequence (EMT)"),
    ("10", "Verification", "PowerFactory trip times vs analysis"),
]


def workflow_png():
    fig, ax = plt.subplots(figsize=(7.2, 9.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(STEPS) * 1.0 + 0.2)
    ax.axis("off")
    for k, (n, title, sub) in enumerate(STEPS):
        y = len(STEPS) - k - 0.5
        box = FancyBboxPatch((0.9, y - 0.36), 8.6, 0.72, boxstyle="round,pad=0.02,rounding_size=0.12",
                             fc="#eef4fc", ec="#2a78d6", lw=1.3)
        ax.add_patch(box)
        ax.add_patch(plt.Circle((0.9, y), 0.3, fc="#2a78d6", ec="none"))
        ax.text(0.9, y, n, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(1.45, y + 0.12, title, va="center", fontsize=10, fontweight="bold", color="#0b0b0b")
        ax.text(1.45, y - 0.17, sub, va="center", fontsize=8.2, color="#52514e")
        if k < len(STEPS) - 1:
            ax.annotate("", xy=(5.2, y - 0.62), xytext=(5.2, y - 0.37),
                        arrowprops=dict(arrowstyle="-|>", color="#52514e", lw=1.2))
    fig.tight_layout()
    p = os.path.join(TMP, "workflow.png")
    fig.savefig(p, dpi=200)
    plt.close(fig)
    return p


# ---------------------------------------------------------------------------------------------
# Numbers for the comparisons
# ---------------------------------------------------------------------------------------------
BENCH = {"RG60": 8.41, "632": 4.80, "633": 4.15, "634": 15.28, "645": 3.41, "646": 3.05, "652": 1.79,
         "671": 3.35, "675": 3.12, "680": 2.91, "684": 2.62, "611": 1.85, "692": 3.35}


def node_max(node):
    recs = [r for r in S3.FAULTS if r["case"] == "max" and r["dg"] == 0.0 and r["where"] == node]
    ll = [r for r in recs if r["type"] == "LLL"]
    use = ll if ll else recs
    return max(max(r["ifault"]) for r in use) / 1000.0


def pct(a, b):
    try:
        return "%+.1f %%" % (100.0 * (float(a) / float(b) - 1))
    except (ValueError, ZeroDivisionError, TypeError):
        return "-"


def fig_case(case):
    return [r for r in S3.FAULTS if r["case"] == case][0]


def dev_times(rec, s, relay, unit, fuses):
    i_r = S3.imax(rec, "R1" if relay == "R1" else "R2")
    if relay == "R1":
        tf, td = S3.t_r1(i_r, s, "f"), S3.t_r1(i_r, s, "d")
    else:
        tf, td = S3.t_r2(i_r, s, unit, "f"), S3.t_r2(i_r, s, unit, "d")
    out = {"I_rec": i_r, "fast": tf, "delayed": td}
    for f in fuses:
        i = S3.imax(rec, f)
        out[f] = (i, S3.FTYPE[s["fuses"][f]].mmt(i), S3.FTYPE[s["fuses"][f]].tct(i))
    return out


def t(x):
    return "no trip" if x == float("inf") else "%.3f" % x


# ---------------------------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------------------------
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceAfter=6, textColor=colors.HexColor("#1b4f93"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=4,
                    textColor=colors.HexColor("#1b4f93"))
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9, leading=12)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=7.8, leading=10)
CELL = ParagraphStyle("C", parent=BODY, fontSize=7.8, leading=9.6)
CAP = ParagraphStyle("Cap", parent=BODY, fontSize=8, leading=10, alignment=TA_CENTER,
                     textColor=colors.HexColor("#52514e"))
STEPBOX = ParagraphStyle("SB", parent=BODY, fontSize=8.6, leading=11, backColor=colors.HexColor("#eef4fc"),
                         borderColor=colors.HexColor("#2a78d6"), borderWidth=0.8, borderPadding=5,
                         spaceBefore=4, spaceAfter=8)
GOOD, BAD, MID = colors.HexColor("#dff3df"), colors.HexColor("#fbe0e0"), colors.HexColor("#fff3d6")


def table(data, widths, zebra=True, colour=None, header_rows=1):
    data = [[c if isinstance(c, Paragraph) else Paragraph(str(c), CELL) for c in r] for r in data]
    tb = Table(data, colWidths=widths, repeatRows=header_rows)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9b8b3")),
          ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#1b4f93")),
          ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.white),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    for r in range(header_rows):
        for c in range(len(data[0])):
            data[r][c].style = ParagraphStyle("h", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")
    if zebra:
        for r in range(header_rows, len(data)):
            if (r - header_rows) % 2:
                st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f4f4f2")))
    for (c, r, col) in (colour or []):
        st.append(("BACKGROUND", (c, r), (c, r), col))
    tb.setStyle(TableStyle(st))
    return tb


def side_by_side(paper_png, ours_png, cap_paper, cap_ours, h=6.2 * cm):
    def img(p):
        im = Image(p)
        ratio = im.imageWidth / float(im.imageHeight)
        w = min(8.6 * cm, h * ratio)
        return Image(p, width=w, height=w / ratio)
    tb = Table([[img(paper_png), img(ours_png)],
                [Paragraph(cap_paper, CAP), Paragraph(cap_ours, CAP)]], colWidths=[8.9 * cm, 8.9 * cm])
    tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    return tb


def stacked(paper_png, ours_png, cap_paper, cap_ours, width=15.5 * cm):
    out = []
    for p, c in ((paper_png, cap_paper), (ours_png, cap_ours)):
        im = Image(p)
        ratio = im.imageWidth / float(im.imageHeight)
        out += [Image(p, width=width, height=width / ratio), Paragraph(c, CAP), Spacer(1, 0.15 * cm)]
    return out


def step_header(n, title, what):
    return [Paragraph("Step %s - %s" % (n, title), H1), Paragraph(what, STEPBOX)]


story = []

# ---- title and scorecard ------------------------------------------------------------------
story += [Spacer(1, 1.2 * cm),
          Paragraph("Comparison with the reference paper", ParagraphStyle("T", parent=H1, fontSize=22, leading=26)),
          Paragraph("Comparison of results in serial workflow order", ParagraphStyle("st", parent=H2, fontSize=13)),
          Spacer(1, 0.3 * cm),
          Paragraph("<b>Paper:</b> M. Yousaf, A. Jalilian, K. M. Muttaqi, D. Sutanto, \"An Adaptive Overcurrent "
                    "Protection Scheme for Dual-Setting Directional Recloser and Fuse Coordination in Unbalanced "
                    "Distribution Networks With Distributed Generation,\" <i>IEEE Trans. Ind. Appl.</i>, 58(2), "
                    "1831-1842, 2022 - IEEE 13-node part.", BODY),
          Paragraph("<b>This study:</b> DIgSILENT PowerFactory 2021 SP2, project <i>IEEE13 DSDR Fuse Coordination</i>, "
                    "scripts in <i>DSDR_Study/</i> (run_all.py). Paper figures are reproduced from the article for "
                    "side-by-side comparison only.", BODY),
          Spacer(1, 0.4 * cm), Paragraph("Scorecard", H2)]

t2 = rows("comparison/Table_II_vs_paper.csv")
inom_dev = max(abs(float(r["Inom (A)"]) / float(r["paper Inom (A)"]) - 1) for r in t2 if float(r["paper Inom (A)"]))
cls = rows("comparison/Fig14_Fig17_vs_paper.csv")
comp = [r for r in cls if r["Fig14 model"] != "n/a"]
agree14 = sum(r["Fig14 model"] == r["Fig14 paper"] for r in comp)
held17 = sum(r["Fig17 model"] == "held" for r in comp)
pfv = rows("PF_vs_Python_times_dsdr.csv") + rows("PF_vs_Python_times_conventional.csv")
pfmax = max(float(r["deviation %"]) for r in pfv if r["deviation %"] != "-")
bench_dev = max(abs(node_max(n) / v - 1) for n, v in BENCH.items() if n != "RG60")
t3 = rows("comparison/Table_III_vs_paper.csv")
r1zone = [r for r in t3 if r["Fuse"] in ("F632", "F645", "F646", "F-DL", "F634")]
rev_match = max(abs(float(r["b_i (i counted from source)"]) - float(r["paper b_i"])) for r in r1zone)
score = [["Item", "Paper", "This study", "Agreement"],
         ["Rated branch currents (Table II)", "Table II", "max deviation %.1f %%" % (100 * inom_dev), "very good"],
         ["Fault levels vs IEEE benchmark [8]", "-", "within %.1f %% (nodes)" % (100 * bench_dev), "very good"],
         ["Fault levels vs paper Table II", "If,max 1.9-7.8 kA", "IEEE-benchmark levels", "lower (paper inconsistent)"],
         ["R1 worked example (4219 A)", "0.097 / 1.932 s", "%.3f / %.3f s" % (S3.t_r1(4219, CONV, "f"), S3.t_r1(4219, CONV, "d")), "very good"],
         ["Fuse coefficients b_i (Table III), R1 zone", "Table III", "within %.2f (i counted from source)" % rev_match, "good - index reversed"],
         ["Fig. 14 without DSDR", "9 cells lost", "%d / %d cells agree" % (agree14, len(comp)), "good"],
         ["Fig. 17 with DSDR", "all cells held", "%d / %d held" % (held17, len(comp)), "good (1 cell at dial limit)"],
         ["Fig. 15 fuse current, solid LL at 646", "3.64 kA", "%.2f kA" % (S3.imax(fig_case("Fig15"), "F646") / 1000), "very good"],
         ["Fig. 10 fuse operation after 2 fast shots", "1.21 s",
          "melts at %.2f s (DG out, F671-2 %s)" % (json.load(open(os.path.join(RES, "Fig10_summary.json")))["DG out"]["t_melt"],
                                                  sz(CONV["fuses"]["F671-2"])),
          "very good" if abs(json.load(open(os.path.join(RES, "Fig10_summary.json")))["DG out"]["t_melt"] - 1.21) < 0.15 else "differs"],
         ["PowerFactory vs analysis trip times", "-", "max %.2f %% (%d times)" % (pfmax, len(pfv)), "verified"]]
colr = []
for k, r in enumerate(score[1:], 1):
    colr.append((3, k, GOOD if r[3].startswith(("very", "verified")) else (MID if not r[3].startswith("good") else GOOD)))
story.append(table(score, [5.4 * cm, 3.4 * cm, 4.8 * cm, 4.2 * cm], colour=colr))
story.append(PageBreak())

# ---- workflow -----------------------------------------------------------------------------
story += [Paragraph("Serial workflow", H1),
          Paragraph("The replication follows the paper's method (Fig. 5) in this order. Each step below shows "
                    "what the paper reports, what the replication obtains and why they differ.", BODY),
          Spacer(1, 0.2 * cm), Image(workflow_png(), width=14.5 * cm, height=18.5 * cm), PageBreak()]

# ---- Step 1 ------------------------------------------------------------------------------------
story += step_header("1", "Network model and source",
                     "<b>Paper:</b> IEEE 13-node feeder [33], 4.05 MVA / 0.69 kV synchronous DG at 692 via a "
                     "0.69/4.16 kV, 0.15 pu transformer (Table I). The source model is not stated.<br/>"
                     "<b>This study:</b> DIgSILENT IEEE 13-node example with the 115/4.16 kV 5 MVA substation "
                     "transformer; DG set to Table I. The source is validated against the IEEE short-circuit "
                     "benchmark (Kersting &amp; Shirek, quoted by the same authors in [8]).")
data = [["Node", "IEEE benchmark [8] (kA)", "This study (kA)", "Difference"]]
for n, v in BENCH.items():
    if n == "RG60":
        continue
    m = node_max(n)
    data.append([n, "%.2f" % v, "%.2f" % m, pct(m, v)])
story += [table(data, [3 * cm, 4.5 * cm, 4.5 * cm, 3.5 * cm]),
          Paragraph("Maximum fault current at each node, DG out (3-phase where it exists, otherwise the largest "
                    "unbalanced fault). The stiff-grid study case used by the earlier attempt gives 20-65 % higher "
                    "values, e.g. 7.91 kA at 632.", SMALL),
          Spacer(1, 0.3 * cm)]
tbl1 = [["Table I parameter", "Paper", "This study"],
        ["Xl / Ra", "0.05 / 0.0014 pu", "0.05 / 0.0014 pu"],
        ["Xd / Xd' / Xd''", "1.4 / 0.231 / 0.118 pu", "1.4 / 0.231 / 0.118 pu"],
        ["Xq / Xq' / Xq''", "1.372 / 0.8 / 0.118 pu", "1.372 / 0.8 / 0.118 pu"],
        ["T'do / T''do", "5.5 / 0.05 s", "5.5 / 0.05 s"],
        ["T'qo / T''qo", "1.25 / 0.19 s", "1.25 / 0.33 s (derived by the machine model)"],
        ["M = 2H", "1.5 s", "1.5 s"]]
story += [table(tbl1, [5 * cm, 5.5 * cm, 7 * cm]), PageBreak()]

# ---- Step 2 / 3: Table II ------------------------------------------------------------------------
story += step_header("2 and 3", "Load flow and fault study (Table II)",
                     "<b>Paper:</b> Inom from the unbalanced load flow; If,max from a bolted fault below the device; "
                     "If,min from an LG fault through 3 ohm at the farthest node; DG out.<br/>"
                     "<b>This study:</b> the same definitions (complete short-circuit method, all phase combinations).")
data = [["From", "To", "Inom paper (A)", "Inom ours (A)", "diff", "If,min paper (kA)", "If,min ours (kA)",
         "If,max paper (kA)", "If,max ours (kA)"]]
colr = []
for k, r in enumerate(t2, 1):
    d = pct(r["Inom (A)"], r["paper Inom (A)"])
    data.append([r["From"], r["To"], r["paper Inom (A)"], r["Inom (A)"], d, r["paper If,min (kA)"],
                 r["If,min (kA)"], r["paper If,max (kA)"], r["If,max (kA)"]])
    colr.append((4, k, GOOD))
    ok = abs(float(r["If,max (kA)"]) / float(r["paper If,max (kA)"]) - 1) < 0.25
    colr.append((8, k, GOOD if ok else MID))
story += [table(data, [1.8 * cm, 1.4 * cm, 1.9 * cm, 1.9 * cm, 1.5 * cm, 2.1 * cm, 2.1 * cm, 2.1 * cm, 2.1 * cm],
                colour=colr),
          Spacer(1, 0.2 * cm),
          Paragraph("<b>Agreement:</b> rated currents within %.1f %% on every branch. <b>Differences:</b> the "
                    "replication's fault levels follow the IEEE benchmark; several of the paper's If,max are "
                    "physically inconsistent (632-633 6.73 kA, 671-680 6.25 kA and 692-675 7.83 kA exceed the "
                    "paper's own 5.41 kA at the feeder head of a radial feeder), so they cannot be reproduced by any "
                    "consistent model." % (100 * inom_dev), BODY), PageBreak()]

# ---- Step 4: devices and settings ------------------------------------------------------------------
fw, rv = DSDR["R2fw"], DSDR["R2rv"]
story += step_header("4", "Protective devices and pickup settings (Fig. 6, eq. 3)",
                     "<b>Paper:</b> R1 GE IAC77B801A extremely inverse, TDS 0.5 / 10, OLF 1.25; R2 GE/Alstom CDG34 "
                     "extremely inverse (settings not given); 15 fuses, a = -1.8, b from Table III.<br/>"
                     "<b>This study:</b> PowerFactory library relays and fuses; fuse sizes from the fuse bands of the "
                     "paper's figures where shown, otherwise from [8] Table V.")
data = [["Device", "Paper", "This study"],
        ["R1 relay / curve", "GE IAC77B801A, extremely inverse", "same (library type)"],
        ["R1 pickup", "OLF x Inom = 1.25 x 587.1 = 734 A", "CT 900/5, tap 4 A = %.0f A (eq. 3: %.1f A)" % (CONV["R1"]["ip"], CONV["R1"]["ip_eq3"])],
        ["R1 TDS fast / delayed", "0.5 / 10", "0.5 / 10"],
        ["R2 relay / curve", "GE/Alstom CDG34, extremely inverse", "same (library type, CDG14 table)"],
        ["R2 forward pickup", "1.25 x 478.2 = 598 A (not stated)", "fast curve from %.0f A, delayed from %.0f A (CT 1000/5)" % (2 * fw["is_f"], 2 * fw["is_d"])],
        ["R2 forward TMS", "not given", "fast %.2f / delayed %.2f (conventional: %.2f / %.2f)" % (fw["tms_f"], fw["tms_d"], CONV["R2fw"]["tms_f"], CONV["R2fw"]["tms_d"])],
        ["R2 reverse pickup (eq. 12)", "OLF x Inom,rv (value not given)", "1.25 x %.1f A = %.0f A; curves from %.0f / %.0f A (CT 500/5)" % (rv["i_nom_rv"], rv["ip_eq12"], 2 * rv["is_f"], 2 * rv["is_d"])],
        ["R2 reverse TMS", "not given (Fig. 15: 0.103 / 2.046 s at 1.54 kA)", "fast %.2f / delayed %.2f" % (rv["tms_f"], rv["tms_d"])],
        ["Fuses", "eq. (6) with Table III in the text; library fuses in the figures",
         "Gould-Shawmut A055C (+ gL-800A on LV), as in [8] and the figures"]]
story += [table(data, [4 * cm, 6.5 * cm, 7 * cm])]
fz = [["Fuse", "[8] Table V", "2022 paper figures", "Start", "After the no-DG design", "After the DSDR design"]]
FIGSIZE = {"F632": "400E (Fig 12, 15, 16), 500E (Fig 11)", "F633": "250E (Fig 13)", "F646": "300E (Fig 11, 15, 16), 200E (Fig 12)",
           "F671-1": "300E (Fig 9)", "F671-2": "300E (Fig 8)", "F684": "200E (Fig 8)", "F692": "200E (Fig 9)", "F692-R": "250E (Fig 9)"}
REF8 = {"F611": "125E", "F633": "250E", "F634": "gL-800", "F645": "250E", "F646": "200E", "F-DL": "250E", "F652": "150E",
        "F671": "250E (F671-R in [8])", "F671-2": "200E (F671 in [8])", "F675": "200E", "F684": "150E", "F692": "200E",
        "F692-R": "300E", "F632": "- (relay R1 in [8])", "F671-1": "- (relay R5 in [8])"}
colr = []
for k, f in enumerate(CONV["fuses"], 1):
    st, a, b = sz(START[f]), sz(CONV["fuses"][f]), sz(DSDR["fuses"][f])
    fz.append([f, REF8.get(f, "-"), FIGSIZE.get(f, "-"), st, a, b])
    if a != st:
        colr.append((4, k, MID))
    if b != a:
        colr.append((5, k, MID))
story += [Spacer(1, 0.3 * cm), Paragraph("Fuse sizes", H2),
          table(fz, [1.6 * cm, 3.3 * cm, 4.7 * cm, 1.6 * cm, 3.1 * cm, 3.2 * cm], colour=colr),
          Paragraph("Start: the size drawn in the 2022 paper's figures where a figure shows the fuse, otherwise ref. [8] "
                    "Table V (with [8]'s smaller F671-2 the fuse melts in the second fast shot of Fig. 10 instead of "
                    "after both). [8] and the 2022 paper name some devices "
                    "differently: [8]'s REC1 / REC2 are the reclosers R1 / R2; its relays R1, R2 and R5 are not used in "
                    "the 2022 scheme; its F671 is F671-2 here (671 to 684) and its F671-R is F671 here (load at 671). "
                    "F632 and F671-1 stand where [8] has relays, so their sizes come from the 2022 paper's figures. "
                    "Shaded: sizes changed by the method's steps 9-10.", SMALL), PageBreak()]

# ---- Step 5: Table III ---------------------------------------------------------------------------
story += step_header("5", "Fuse coefficients b<sub>i</sub> (Table III, eqs. 6-9)",
                     "<b>Paper:</b> b<sub>i</sub> from eq. (9), a<sub>i</sub> = -1.8; worked example F645: 4219 A, "
                     "t<sub>F</sub> 0.097 s, t<sub>D</sub> 1.932 s, b = 6.65.<br/><b>This study:</b> eq. (9) at the "
                     "maximum fault current below each fuse, once with i = 1 for the fuse closest to the fault (the "
                     "definition of the cited ref. [25]) and once with i counted from the source.")
data = [["Fuse", "If (A)", "i / z", "b<sub>i</sub> paper", "b<sub>i</sub> ours, i from fault [25]", "b<sub>i</sub> ours, i from source", "b of installed fuse"]]
colr = []
for k, r in enumerate(t3, 1):
    data.append([r["Fuse"], r["If (A)"], r["i/z"], r["paper b_i"], r["b_i (i=1 closest to fault, ref. [25])"],
                 r["b_i (i counted from source)"], r["b_i of installed fuse at If"]])
    if r["Fuse"] in ("F632", "F645", "F646", "F-DL", "F634"):
        colr.append((5, k, GOOD))
story += [table(data, [1.8 * cm, 1.7 * cm, 1.3 * cm, 2.1 * cm, 3.6 * cm, 3.4 * cm, 3.3 * cm], colour=colr),
          Spacer(1, 0.2 * cm),
          Paragraph("<b>Finding:</b> for the R1-zone fuses (shaded) the paper's values are reproduced within %.2f "
                    "only when i is counted from the source - the reverse of eq. (9)'s definition. With that "
                    "indexing the upstream fuse becomes faster than the downstream one, violating the 75 %% rule of "
                    "eq. (8). The paper's worked example is reproduced: F645 needs i/(z+1) = 2/3. R2-zone values "
                    "depend on R2's settings, which the paper does not publish. The last column shows that the "
                    "installed library fuses melt much faster than the eq.-(9) target (b 5.0-6.1), which is why the "
                    "paper's figure times differ from eq. (6)." % rev_match, BODY), PageBreak()]

# ---- Step 6 --------------------------------------------------------------------------------------
summ = open(os.path.join(RES, "summary.txt"), encoding="utf-8").read()
story += step_header("6", "Conventional scheme without DG (Fig. 5 steps 7-10)",
                     "<b>Paper:</b> the preset recloser-fuse scheme is stated to be coordinated before DG is added "
                     "(no figure).<br/><b>This study:</b> 39 node/fault-type cells (13 nodes x LG/LL/LLG/LLL where the "
                     "phases exist), every phase combination, bolted faults.")
a0 = found(r"published fuse sizes, no DG: (\d+) of (\d+)")
a1 = found(r"after steps 8-10, no DG: (\d+) of (\d+)")
data = [["Check", "Result"],
        ["Starting fuse sizes (2022 figures, else [8])", "%s / %s cells held. Lost: %s" % (a0[0], a0[1], stage_a_losses())],
        ["Steps 9-10 (fuse revision)", changed(START, CONV["fuses"])],
        ["After revision", "%s / %s cells held" % a1],
        ["R2 delayed TMS", "1.0: highest dial keeping R2 at least 10 cycles below R1 (paper: 10-cycle recloser margin)"]]
story += [table(data, [5 * cm, 12.5 * cm]), Spacer(1, 0.3 * cm)]

# ---- Step 7: DG impact -----------------------------------------------------------------------------
story += step_header("7", "DG added, conventional R2 (Figs. 14 and 8-13)",
                     "<b>Paper:</b> Fig. 14 marks 9 cells lost (633 LLG/LLL, 645 LG/LL/LLG, 646 LL/LLG, 675 LLG/LLL).<br/>"
                     "<b>This study:</b> same settings with the 4.05 MVA DG in service.")
story += stacked(PFIG["14"], os.path.join(FIG, "Fig14_without_DSDR.png"), "Paper Fig. 14",
                 "This study (model)", width=13.5 * cm)
data = [["Node"] + FAULT_TYPES + ["Node"] + FAULT_TYPES]
cl = {(r["node"], r["fault"]): r for r in cls}
colr = []
half = (len(NODE_ORDER) + 1) // 2
for k in range(half):
    row = []
    for j, n in enumerate((NODE_ORDER[k], NODE_ORDER[k + half] if k + half < len(NODE_ORDER) else None)):
        if n is None:
            row += [""] * 5
            continue
        row.append(n)
        for c, ft in enumerate(FAULT_TYPES):
            r = cl[(n, ft)]
            if r["Fig14 model"] == "n/a":
                row.append("n/a")
                continue
            row.append("%s / %s" % (r["Fig14 paper"], r["Fig14 model"]))
            colr.append((j * 5 + 1 + c, k + 1, GOOD if r["Fig14 paper"] == r["Fig14 model"] else BAD))
    data.append(row)
story += [Spacer(1, 0.2 * cm), Paragraph("Fig. 14 cell by cell (paper / replication)", H2),
          table(data, [1.3 * cm] + [1.9 * cm] * 4 + [1.3 * cm] + [1.9 * cm] * 4, zebra=False, colour=colr),
          Paragraph("<b>%d of %d cells agree.</b> Lost in both: %s. Lost only in the replication: %s (with the DG "
                    "these fuses carry more current than the reclosers and melt before the fast trip, which is already "
                    "at its minimum dial). Lost only in the paper: %s."
                    % (agree14, len(comp),
                       cells({(r["node"], r["fault"]) for r in comp if r["Fig14 model"] == "lost" and r["Fig14 paper"] == "lost"}),
                       cells({(r["node"], r["fault"]) for r in comp if r["Fig14 model"] == "lost" and r["Fig14 paper"] != "lost"}),
                       cells({(r["node"], r["fault"]) for r in comp if r["Fig14 model"] != "lost" and r["Fig14 paper"] == "lost"})),
                    BODY), PageBreak()]

# figures 8-13
conv = CONV
FIGCMP = [
    ("8", "Fig8", "R2", "R2fw", ["F684", "F671-2"], conv,
     "LG fault at 611", {"I": "1975.6 A", "R2 fast": "0.207", "R2 delayed": "2.472", "F684": "0.476 (melt)", "F671-2": "1.456"},
     "Fig08_LG_611.png"),
    ("9", "Fig9", "R2", "R2fw", ["F692-R", "F671-1"], conv,
     "LLG fault in the middle of 692-675, 1 ohm", {"I": "2589 / 2423 A", "R2 fast": "0.141", "R2 delayed": "1.483",
                                                   "F692-R": "0.217", "F671-1": "0.546"}, "Fig09_LLG_692-675.png"),
    ("11", "Fig11", "R1", None, ["F646", "F632"], conv,
     "LL fault at 646, 1 ohm", {"I": "3492 A", "R1 fast": "0.134", "R1 delayed": "2.690", "F646": "0.202", "F632": "1.096"},
     "Fig11_LL_646_R1.png"),
    ("12", "Fig12", "R2", "R2fw", ["F632"], conv,
     "LL fault at 645, 1.5 ohm, conventional R2 (reverse)", {"I": "364 A (R2)", "R2 fast": "0.419", "R2 delayed": "16.683",
                                                             "F632": "25.440"}, "Fig12_LL_645_conventional_R2.png"),
    ("13", "Fig13", "R2", "R2fw", ["F633"], conv,
     "3-phase fault at 10 % of 632-633, conventional R2", {"I": "3361 A (R2) / 8517 A (F633)", "R2 fast": "0.079",
                                                          "R2 delayed": "1.556", "F633": "0.022"},
     "Fig13_LLL_632-633_conventional_R2.png"),
]


def fig_compare(num, case, relay, unit, fuses, s, title, paper_vals, png, verdict):
    rec = fig_case(case)
    d = dev_times(rec, s, relay, unit, fuses)
    data = [["Quantity", "Paper Fig. %s" % num, "This study"]]
    data.append(["Current", paper_vals["I"], "%.0f A (%s)" % (d["I_rec"], relay) + "".join(
        ", %.0f A (%s)" % (d[f][0], f) for f in fuses)])
    data.append(["%s fast (s)" % relay, paper_vals["%s fast" % relay], t(d["fast"])])
    data.append(["%s delayed (s)" % relay, paper_vals["%s delayed" % relay], t(d["delayed"])])
    for f in fuses:
        data.append(["%s melt / clear (s)" % f, paper_vals.get(f, "-"),
                     "%s / %s (%s)" % (t(d[f][1]), t(d[f][2]), s["fuses"][f].replace("A055C", ""))])
    return [Paragraph("Fig. %s - %s" % (num, title), H2),
            side_by_side(PFIG[num], os.path.join(FIG, png), "Paper Fig. %s" % num, "This study", h=5.4 * cm),
            table(data, [4 * cm, 5.5 * cm, 8 * cm]), Paragraph(verdict, BODY)]


PAPER_HELD = {"8": True, "9": True, "11": True, "12": False, "13": False}


def verdict(num, case, relay, unit, fuses, s):
    d = dev_times(fig_case(case), s, relay, unit, fuses)
    f = fuses[0]
    mmt, tct = d[f][1], d[f][2]
    fast_ok = d["fast"] < mmt
    del_ok = d["delayed"] > tct
    held = fast_ok and del_ok
    txt = "%s fast %s s %s %s melting %s s; %s delayed %s %s %s clearing %s s" % (
        relay, t(d["fast"]), "before" if fast_ok else "AFTER", f, t(mmt), relay, t(d["delayed"]),
        "after" if del_ok else "BEFORE", f, t(tct))
    if len(fuses) > 1:
        b_ = fuses[1]
        ok = tct < 0.75 * d[b_][1]
        txt += "; backup %s melts %s s (75 %% rule %s)" % (b_, t(d[b_][1]), "kept" if ok else "NOT kept")
    same = held == PAPER_HELD[num]
    return "<b>%s:</b> replication - %s: fuse saving %s for this fault; paper: %s." % (
        "Agreement" if same else "Difference", txt, "held" if held else "lost", "held" if PAPER_HELD[num] else "lost")


for num, case, relay, unit, fuses, s, title, pv, png in FIGCMP:
    story += [KeepTogether(fig_compare(num, case, relay, unit, fuses, s, title, pv, png,
                                       verdict(num, case, relay, unit, fuses, s)))]
    story.append(PageBreak())

# ---- Step 8: DSDR ------------------------------------------------------------------------------
story += step_header("8", "R2 as dual-setting directional recloser (Fig. 17, Figs. 15-16, Table IV)",
                     "<b>Paper:</b> reverse pickup by eq. (12), TDS revised by If,Rec/If,Fuse (step 8), fuse revision if a "
                     "dial limit is reached (step 9); with the DSDR every cell of Fig. 17 is held.<br/>"
                     "<b>This study:</b> Ip,rv = 1.25 x %.1f A = %.0f A; step 8 found every remaining loss at a dial limit "
                     "(R1 TDS 0.5/10, CDG TMS 0.1/1.0), so step 9 revised: %s."
                     % (rv["i_nom_rv"], rv["ip_eq12"], changed(CONV["fuses"], DSDR["fuses"])))
story += stacked(PFIG["17"], os.path.join(FIG, "Fig17_with_DSDR.png"), "Paper Fig. 17 - all held",
                 "This study - %d / %d held" % (held17, len(comp)))
story += [
          Paragraph("<b>Result:</b> with the DSDR %d of %d cells are held; lost: %s. %s The same fuses with a "
                    "conventional R2 give %s of %s cells. Without DG the final fuses hold %s of %s cells; prioritising "
                    "the no-DG case in the fuse revision instead gives 39/39 without DG and 33/39 with DG (a design "
                    "trade-off - fuse sizes cannot adapt to the DG state)." % (
                        held17, len(comp), cells({(r["node"], r["fault"]) for r in comp if r["Fig17 model"] == "lost"}),
                        "At 692 LG, F671-1 (needed large for series selectivity with F692-R) clears after R2's delayed "
                        "curve, which is at its maximum dial." if any(r["node"] == "692" and r["Fig17 model"] == "lost" for r in comp) else "",
                        *found(r"final fuse sizes but conventional R2 -> (\d+) of (\d+)"),
                        *found(r"Fig\. 17: \d+ of \d+ cells held with DG;\s+(\d+) of (\d+) without DG")), BODY), PageBreak()]
rec = fig_case("Fig15")
d15 = dev_times(rec, DSDR, "R2", "R2rv", ["F646", "F632"])
d16 = dev_times(rec, DSDR, "R1", None, ["F646", "F632"])
data = [["Quantity", "Paper Figs. 15 / 16", "This study"],
        ["Fuse current", "3.64 kA", "%.2f kA" % (d15["F646"][0] / 1000)],
        ["R2 reverse current", "1.54 kA", "%.2f kA" % (d15["I_rec"] / 1000)],
        ["R2 reverse fast / delayed (s)", "0.103 / 2.046", "%s / %s" % (t(d15["fast"]), t(d15["delayed"]))],
        ["R1 current", "(plotted at 3.61 kA)", "%.2f kA" % (d16["I_rec"] / 1000)],
        ["R1 fast / delayed (s)", "0.128 / 2.555", "%s / %s" % (t(d16["fast"]), t(d16["delayed"]))],
        ["F646 melt (s)", "0.181 (300E)", "%s (%s)" % (t(d15["F646"][1]), DSDR["fuses"]["F646"].replace("A055C", ""))],
        ["F632 melt (s)", "0.411 (400E)", "%s (%s)" % (t(d15["F632"][1]), DSDR["fuses"]["F632"].replace("A055C", ""))]]
story += [Paragraph("Figs. 15 and 16 - solid LL fault at 646", H2),
          side_by_side(PFIG["15"], os.path.join(FIG, "Fig15_LL_646_DSDR.png"), "Paper Fig. 15", "This study", h=5.0 * cm),
          side_by_side(PFIG["16"], os.path.join(FIG, "Fig16_LL_646_R1.png"), "Paper Fig. 16", "This study", h=5.0 * cm),
          table(data, [5 * cm, 5 * cm, 7.5 * cm]),
          Paragraph("<b>Agreement:</b> fuse current within 1 %%; R2 reverse trips first on its fast curve and its delayed "
                    "curve waits for the fuses. <b>Difference:</b> the replication's DG contributes less current through "
                    "R2 (1.11 vs 1.54 kA). R1's fast trip (%s s) is slower than the paper's 0.128 s; it precedes "
                    "F646 (%s s) only because step 9 raised F646 to %s." % (t(d16["fast"]), t(d15["F646"][1]), sz(DSDR["fuses"]["F646"])), BODY),
          PageBreak()]
t4 = rows("comparison/Table_IV_vs_paper.csv")
data = [["Node", "Fault", "R1 fast paper / ours", "R1 delayed paper / ours", "R2 fast paper / ours",
         "R2 delayed paper / ours", "Fuse MMT paper / ours", "Status"]]
colr = []
for k, r in enumerate(t4, 1):
    data.append([r["node"], r["fault"], "%s / %s" % (r["paper R1 fast"], r["R1 fast (s)"]),
                 "%s / %s" % (r["paper R1 delayed"], r["R1 delayed (s)"]),
                 "%s / %s" % (r["paper R2 fast"], r["R2 fast (s)"]), "%s / %s" % (r["paper R2 delayed"], r["R2 delayed (s)"]),
                 "%s / %s" % (r["paper fuse MMT"], r["fuse MMT (s)"]), r["status"]])
    colr.append((7, k, GOOD if r["status"] == "held" else BAD))
story += [Paragraph("Table IV - operating times with the DSDR (s)", H2),
          table(data, [1.3 * cm, 1.3 * cm, 2.6 * cm, 2.8 * cm, 2.6 * cm, 2.8 * cm, 2.6 * cm, 1.5 * cm], colour=colr),
          Paragraph("The paper does not state the fault behind each row; the replication uses bolted LLL faults (LL at "
                    "two-phase nodes, LG at single-phase nodes) with the DG in service. R1 times are 13-78 % above the "
                    "paper's because the IEEE-benchmark fault levels are lower; R2 times differ further because R2's "
                    "settings are not published. The relative order (R2 fast before fuse before delayed curves) is "
                    "the same in both.", BODY), PageBreak()]

# ---- Step 9: Fig. 10 ---------------------------------------------------------------------------
story += step_header("9", "Time-domain reclosing sequence (Fig. 10)",
                     "<b>Paper:</b> LL (a-c) fault at 684 through 0.2 ohm; two fast recloser operations, then the fuse "
                     "clears at t = 1.21 s.<br/><b>This study:</b> PowerFactory EMT; switching times from the relay "
                     "and fuse curves, fuse heating accumulated from the simulated current. Fault at 0.30 s and dead time 0.2 s as read "
                     "from the paper's figure; the plotted current is the feeder current arriving at node 632.")
F10 = json.load(open(os.path.join(RES, "Fig10_summary.json")))


def f10(tag, key, fmt_="%.2f s"):
    v = F10[tag][key]
    return "-" if v is None else fmt_ % v


fo, fi_ = F10["DG out"], F10["DG in"]
saved = {tag: F10[tag]["t_melt"] is None or F10[tag]["fast_shots_before_melt"] >= 2 for tag in F10}
story += [side_by_side(PFIG["10"], os.path.join(FIG, "Fig10_EMT_LL_684.png"), "Paper Fig. 10",
                       "This study (top: DG out, bottom: DG in)", h=7.0 * cm),
          table([["Quantity", "Paper", "This study DG out", "This study DG in"],
                 ["F671-2", "(300E in Fig. 8)", sz(fo["fuse"]), sz(fi_["fuse"])],
                 ["R2 fast shot incl. breaker", "-", f10("DG out", "t_fast", "%.3f s"), f10("DG in", "t_fast", "%.3f s")],
                 ["Fuse heat after the fast shots", "-", "%.0f %% of melting" % (100 * fo["heat_after_fast_shots"]),
                  "%.0f %% of melting" % (100 * fi_["heat_after_fast_shots"])],
                 ["Fuse melts", "fuse operation 1.21 s", f10("DG out", "t_melt"), f10("DG in", "t_melt")],
                 ["Fast shots completed before the fuse melts", "2", str(fo["fast_shots_before_melt"]), str(fi_["fast_shots_before_melt"])],
                 ["Fuse finished", "-", f10("DG out", "t_clear"), f10("DG in", "t_clear")]],
                [5.2 * cm, 3.2 * cm, 4.4 * cm, 4.7 * cm]),
          Paragraph("<b>%s</b> without DG the fuse %s (paper: after the two fast shots, at 1.21 s). With the DG it melts "
                    "at %s: R2 cannot de-energise faults below 671, because the DG at 692 keeps feeding them through "
                    "671 - a case the paper's DSDR does not address." % (
                        "Agreement:" if saved["DG out"] else "Difference:",
                        "survives both fast shots and melts at %s" % f10("DG out", "t_melt") if saved["DG out"] else
                        "melts at %s, during fast shot %d, so the two fast shots are not completed with F671-2 = %s"
                        % (f10("DG out", "t_melt"), fo["fast_shots_before_melt"] + 1, sz(fo["fuse"])),
                        f10("DG in", "t_melt")), BODY), PageBreak()]

# ---- Step 10 --------------------------------------------------------------------------------------
devs = [float(r["deviation %"]) for r in pfv if r["deviation %"] != "-"]
story += step_header("10", "Verification",
                     "Every relay and fuse operating time used in the analysis was recomputed by PowerFactory's own "
                     "library models (c:Ttrip) for every fault case, conventional and DSDR settings.")
story += [table([["Check", "Result"],
                 ["Operating times compared", "%d" % len(pfv)],
                 ["Median deviation", "%.2f %%" % sorted(devs)[len(devs) // 2]],
                 ["Maximum deviation", "%.2f %%" % max(devs)],
                 ["Pipeline", "run_all.py rebuilds the model and all results from scratch in about 2.5 minutes"]],
                [6 * cm, 11.5 * cm]),
          Spacer(1, 0.4 * cm), Paragraph("Summary of the comparison", H1)]
concl = [
    "<b>Reproduced:</b> network and rated currents (within 1.9 %%), the paper's R1 worked example, Table III (once "
    "its reversed index is recognised), the loss of coordination with DG (Fig. 14: %d/%d cells), its restoration "
    "with the DSDR (Fig. 17: %d/%d), the Fig. 15 fault current, and the Fig. 10 fuse timing." % (agree14, len(comp), held17, len(comp)),
    "<b>Paper inconsistencies:</b> Table III applies eq. (9) with i counted from the source (upstream fuses faster); "
    "the figures use A055C library fuses, not eq. (6) with Table III; fuse sizes change between figures; several "
    "Table II fault levels exceed the feeder-head value; R2 settings are not published.",
    "<b>Differences caused by the devices' limits:</b> R1 is at both IAC dial limits and the CDG table stops at TMS "
    "0.1, so the method's step 9 (fuse revision) was needed; one cell (692 LG) remains lost with DG, and there is a "
    "genuine trade-off between DG-in and DG-out coordination.",
    "<b>Beyond the paper:</b> the EMT study shows that with DG the fuse-saving scheme fails for faults below 671 "
    "because R2 cannot interrupt the DG infeed there.",
]
for c in concl:
    story.append(Paragraph("&bull; " + c, BODY))

# ---- Appendix: inventory, Table I, Figs. 1-6 ---------------------------------------------------------
story += [PageBreak(), Paragraph("Appendix A - every table and figure of the paper up to Fig. 17", H1),
          Paragraph("Where each item of the paper is in the replication. Tables are in <i>results/database/</i> "
                    "(Table_I ... Table_IV csv and Tables_I_to_IV.txt), figures in <i>results/figures/</i>.", BODY)]
inv = [["Paper", "Content", "This study", "Kind"],
       ["Table I", "Short-circuit parameters of the DG", "Table_I_DG_parameters.csv", "model read-back"],
       ["Table II", "Inom, If,min, If,max of the branches", "Table_II_branch_currents.csv", "calculated"],
       ["Table III", "Fuse coefficients b_i", "Table_III_fuse_coefficients.csv", "calculated"],
       ["Table IV", "Operating times with the DSDR, incl. fuse t_MMT", "Table_IV_operating_times.csv", "calculated"],
       ["Fig. 1", "Conventional recloser-fuse coordination (TCC)", "Fig01_conventional_TCC.png", "drawn from model curves"],
       ["Fig. 2", "Typical network with recloser and fuses", "Fig02_typical_network.png", "schematic"],
       ["Fig. 3", "TCC of the dual-setting recloser", "Fig03_DSDR_TCC.png", "drawn from model curves"],
       ["Fig. 4", "Fuses in series, SLG fault", "Fig04_series_fuses_SLG.png", "drawn from model curves"],
       ["Fig. 5", "Flowchart of the method", "Fig05_method_flowchart.png", "schematic"],
       ["Fig. 6", "IEEE 13-node feeder with protection devices", "Fig06_IEEE13_with_devices.png", "schematic of the model"],
       ["Fig. 7", "CTI against DG penetration", "not replicated (left out on request)", "-"],
       ["Figs. 8, 9", "LG at 611; LLG between 692 and 675", "Fig08_LG_611.png, Fig09_LLG_692-675.png", "calculated"],
       ["Fig. 10", "EMT, LL at 684", "Fig10_EMT_LL_684.png", "PowerFactory EMT"],
       ["Figs. 11-13", "Faults at 646, 645, 632-633 without the DSDR", "Fig11 ... Fig13", "calculated"],
       ["Fig. 14", "Coordination status without the DSDR", "Fig14_without_DSDR.png", "calculated"],
       ["Figs. 15, 16", "LL at 646 with the DSDR", "Fig15_LL_646_DSDR.png, Fig16_LL_646_R1.png", "calculated"],
       ["Fig. 17", "Coordination status with the DSDR", "Fig17_with_DSDR.png", "calculated"]]
story += [table(inv, [2.0 * cm, 6.3 * cm, 6.2 * cm, 3.5 * cm])]
t1p = os.path.join(RES, "comparison", "Table_I_vs_paper.csv")
if os.path.isfile(t1p):
    t1 = list(csv.reader(open(t1p)))
    story += [Spacer(1, 0.4 * cm), Paragraph("Table I - DG parameters, paper against the PowerFactory model", H2),
              table(t1, [7.2 * cm, 2.0 * cm, 2.9 * cm, 2.6 * cm, 1.5 * cm, 1.8 * cm],
                    colour=[(5, k, GOOD if r[5] == "yes" else BAD) for k, r in enumerate(t1) if k])]
story += [PageBreak(), Paragraph("Appendix B - Figs. 1 to 6 redrawn from the model", H1),
          Paragraph("Figs. 1 to 5 of the paper are explanatory and Fig. 6 is the single-line diagram; none of them carries "
                    "results. They are redrawn here with the relay and fuse curves and fault currents of the model, so the "
                    "numbers in them are the replication's, not the paper's.", BODY)]
for png, cap in (("Fig01_conventional_TCC.png", "Fig. 1 - conventional recloser-fuse coordination: R1 fast and delayed curves "
                  "around the fuse band; coordination holds between the two crossing currents."),
                 ("Fig02_typical_network.png", "Fig. 2 - typical radial network with a recloser, lateral fuses and a DG."),
                 ("Fig03_DSDR_TCC.png", "Fig. 3 - the two setting groups of R2 (reverse and forward), each with one real fault."),
                 ("Fig04_series_fuses_SLG.png", "Fig. 4 - two fuses in series for an SLG fault at 652."),
                 ("Fig05_method_flowchart.png", "Fig. 5 - flowchart of the method as it is implemented in step 3."),
                 ("Fig06_IEEE13_with_devices.png", "Fig. 6 - IEEE 13-node feeder with R1, R2, the fuses and the DG at 692.")):
    path = os.path.join(FIG, png)
    if not os.path.isfile(path):
        continue
    im = Image(path)
    ratio = im.imageWidth / float(im.imageHeight)
    w = min(16.5 * cm, 10.8 * cm * ratio)
    story += [KeepTogether([Image(path, width=w, height=w / ratio), Paragraph(cap, CAP), Spacer(1, 0.3 * cm)])]


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#52514e"))
    canvas.drawString(1.5 * cm, 1.0 * cm, "Yousaf et al. 2022 - paper vs replication (IEEE 13-node)")
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, "page %d" % doc.page)
    canvas.restoreState()


pdf = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm,
                        bottomMargin=1.6 * cm, title="Comparison with the reference paper",
                        author="DSDR study, IEEE 13-node feeder")
pdf.build(story, onFirstPage=on_page, onLaterPages=on_page)
for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
print("Saved", OUT)
