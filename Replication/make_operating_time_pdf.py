"""
Builds results/Operating_Time_Calculation.pdf: how the recloser fast and delayed operating times
and the fuse melting times (t_MMT) of Table IV are calculated, with every number worked by hand for
five buses.

Needs: results of run_all.py (studies.json, settings.json, Table_IV.csv), reportlab, matplotlib.
"""

import csv
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from curves import IAC, CDG, Fuse
from protection_data import PAPER_TABLE4, NODES, OLF

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
TMP = os.path.join(RES, "_pdf_tmp")
os.makedirs(TMP, exist_ok=True)
OUT = os.path.join(RES, "Operating_Time_Calculation.pdf")

D = json.load(open(os.path.join(RES, "studies.json")))
S = json.load(open(os.path.join(RES, "settings.json")))["dsdr"]
T4 = {r["node"]: r for r in csv.DictReader(open(os.path.join(RES, "Table_IV.csv")))}
IACC, CDGC = IAC(D["curves"]["iac"]), CDG(D["curves"]["cdg"])
LF = D["loadflow"]
R1, FW, RV = S["R1"], S["R2fw"], S["R2rv"]
FUSE = {n: Fuse(D["curves"]["fuses"][t]) for n, t in S["fuses"].items()}
SIZE = {n: t.replace("A055C", "") for n, t in S["fuses"].items()}

EXAMPLES = ["633", "646", "671", "675", "611"]          # two in R1's zone, three in R2's zone
FAULT_NAME = {"LLL": "three-phase (LLL)", "LL": "line-to-line (LL)", "LG": "single line-to-ground (LG)"}

# ---------------------------------------------------------------------------------------------
# Fonts and styles
# ---------------------------------------------------------------------------------------------
FONTS = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
for name, f in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
                ("DV-BI", "DejaVuSans-BoldOblique.ttf")):
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, f)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

INK, INK2, RULE = colors.HexColor("#1a1a1a"), colors.HexColor("#55534e"), colors.HexColor("#cfcdc7")
ACCENT, SHADE, KEY = colors.HexColor("#1f5fa8"), colors.HexColor("#eef2f7"), colors.HexColor("#fff6dc")

P = ParagraphStyle("p", fontName="DV", fontSize=9.3, leading=13.2, textColor=INK, spaceAfter=5)
SMALL = ParagraphStyle("small", parent=P, fontSize=8, leading=10.6, spaceAfter=0)
CELL = ParagraphStyle("cell", parent=P, fontSize=8.4, leading=11.2, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="DV-B")
HEAD = ParagraphStyle("head", parent=CELL, fontName="DV-B", textColor=colors.white)
TINY = ParagraphStyle("tiny", parent=P, fontSize=6.8, leading=9.5, spaceAfter=0)
HEADS = ParagraphStyle("heads", parent=HEAD, fontSize=7.4, leading=9.8)
H1 = ParagraphStyle("h1", parent=P, fontName="DV-B", fontSize=13, leading=17, textColor=ACCENT, spaceBefore=10,
                    spaceAfter=6, keepWithNext=True)
H2 = ParagraphStyle("h2", parent=P, fontName="DV-B", fontSize=10.4, leading=14, spaceBefore=7, spaceAfter=4,
                    keepWithNext=True)
TITLE = ParagraphStyle("title", parent=P, fontName="DV-B", fontSize=18, leading=23, spaceAfter=4)
SUB = ParagraphStyle("sub", parent=P, fontSize=9.5, leading=13, textColor=INK2, spaceAfter=10)
NOTE = ParagraphStyle("note", parent=P, fontSize=8.6, leading=12, textColor=INK2)

W = A4[0] - 3.6 * cm


def p(text, style=P):
    return Paragraph(text, style)


def table(rows, widths, head=True, key_rows=(), font=CELL, pad=5):
    data = [[c if not isinstance(c, str) else Paragraph(c, (HEAD if font is CELL else HEADS) if (head and i == 0) else font) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
          ("LEFTPADDING", (0, 0), (-1, -1), pad), ("RIGHTPADDING", (0, 0), (-1, -1), pad)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), ACCENT))
    for k in key_rows:
        st.append(("BACKGROUND", (0, k), (-1, k), KEY))
    t.setStyle(TableStyle(st))
    return t


def equation(name, tex, height_pt=None, size=13):
    path = os.path.join(TMP, "eq_%s.png" % name)
    fig = plt.figure(figsize=(0.1, 0.1))
    fig.text(0, 0, "$%s$" % tex, fontsize=size, color="#1a1a1a")
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.04, facecolor="white")
    plt.close(fig)
    img = Image(path)
    k = 72.0 / 300.0
    w, h = img.imageWidth * k, img.imageHeight * k
    if w > W:
        w, h = W, h * W / w
    img.drawWidth, img.drawHeight = w, h
    img.hAlign = "LEFT"
    return img


# ---------------------------------------------------------------------------------------------
# The two hand calculations.  Each returns (steps, t_fast, t_delayed); a step is (what, working, result).
# ---------------------------------------------------------------------------------------------
def iac_steps(i, ip=None, tds_f=None, tds_d=None):
    ip = ip or R1["ip"]
    tds_f, tds_d = tds_f or R1["tds_f"], tds_d or R1["tds_d"]
    m = i / ip
    x = m - 0.62
    a, b, c = 0.6379 / x, 1.7872 / x ** 2, 0.2461 / x ** 3
    k = 0.004 + a + b + c
    tf, td = tds_f * k, tds_d * k
    steps = [
        ("Multiple of pickup", "M = I<sub>f</sub> / I<sub>p</sub> = %.1f / %.0f" % (i, ip), "%.4f" % m),
        ("Shifted multiple", "x = M − 0.62 = %.4f − 0.62" % m, "%.4f" % x),
        ("First term", "0.6379 / x = 0.6379 / %.4f" % x, "%.5f" % a),
        ("Second term", "1.7872 / x<super>2</super> = 1.7872 / %.4f" % x ** 2, "%.5f" % b),
        ("Third term", "0.2461 / x<super>3</super> = 0.2461 / %.3f" % x ** 3, "%.5f" % c),
        ("Curve value for TDS = 1", "K = 0.004 + %.5f + %.5f + %.5f" % (a, b, c), "%.5f s" % k),
        ("<b>Fast</b> (TDS = %.1f)" % tds_f, "t<sub>F</sub> = %.1f × %.5f" % (tds_f, k), "<b>%.3f s</b>" % tf),
        ("<b>Delayed</b> (TDS = %.0f)" % tds_d, "t<sub>D</sub> = %.0f × %.5f" % (tds_d, k), "<b>%.3f s</b>" % td),
    ]
    return steps, tf, td


def cdg_one(i, i_s, tms, label):
    """One CDG operating time.  TMS 0.1 and 1.0 are columns of the table, so only M is interpolated."""
    col = CDGC.tms.index(tms) + 1
    m = i / i_s
    lo, hi = next((a, b) for a, b in zip(CDGC.rows, CDGC.rows[1:]) if a[0] <= m <= b[0])
    f = math.log(m / lo[0]) / math.log(hi[0] / lo[0])
    t = lo[col] * (hi[col] / lo[col]) ** f
    steps = [
        ("Multiple of plug setting", "M = I<sub>f</sub> / I<sub>s</sub> = %.1f / %.0f" % (i, i_s), "%.4f" % m),
        ("Table rows around M (TMS %.1f)" % tms, "M<sub>1</sub> = %.0f → t<sub>1</sub> = %g s;  M<sub>2</sub> = %.0f → "
         "t<sub>2</sub> = %g s" % (lo[0], lo[col], hi[0], hi[col]), ""),
        ("Position between the rows", "f = ln(%.4f / %.0f) / ln(%.0f / %.0f) = %.5f / %.5f" % (
            m, lo[0], hi[0], lo[0], math.log(m / lo[0]), math.log(hi[0] / lo[0])), "%.4f" % f),
        ("<b>%s</b> (TMS = %.1f)" % (label, tms), "t = t<sub>1</sub> × (t<sub>2</sub> / t<sub>1</sub>)<super>f</super> = "
         "%g × (%.5f)<super>%.4f</super>" % (lo[col], hi[col] / lo[col], f), "<b>%.3f s</b>" % t),
    ]
    return steps, t


def cdg_steps(i, unit):
    sf, tf = cdg_one(i, unit["is_f"], unit["tms_f"], "Fast")
    sd, td = cdg_one(i, unit["is_d"], unit["tms_d"], "Delayed")
    return sf, sd, tf, td


def fuse_steps(i, fz, clear=False):
    """Melting (or clearing) time of a fuse: its table read at the fuse current, log-log between points."""
    pts = fz.clear if clear else fz.melt
    sym = "TCT" if clear else "MMT"
    if i > pts[-1][0]:
        return [("Fuse current", "I<sub>fuse</sub> = %.1f A is above the last table point (%.0f A)" % (i, pts[-1][0]), ""),
                ("<b>t<sub>%s</sub></b>" % sym, "time of the last table point", "<b>%.3f s</b>" % pts[-1][1])], pts[-1][1]
    (i1, t1), (i2, t2) = next((a, b) for a, b in zip(pts, pts[1:]) if a[0] <= i <= b[0])
    f = math.log(i / i1) / math.log(i2 / i1)
    t = t1 * (t2 / t1) ** f
    return [("Table points around I<sub>fuse</sub>", "I<sub>1</sub> = %.0f A → t<sub>1</sub> = %.4g s;  I<sub>2</sub> = %.0f A → "
             "t<sub>2</sub> = %.4g s" % (i1, t1, i2, t2), ""),
            ("Position between the points", "f = ln(%.1f / %.0f) / ln(%.0f / %.0f) = %.5f / %.5f" % (
                i, i1, i2, i1, math.log(i / i1), math.log(i2 / i1)), "%.4f" % f),
            ("<b>t<sub>%s</sub></b>" % sym, "t = t<sub>1</sub> × (t<sub>2</sub> / t<sub>1</sub>)<super>f</super> = "
             "%.4g × (%.5f)<super>%.4f</super>" % (t1, t2 / t1, f), "<b>%.3f s</b>" % t)], t


def last_fast(node):
    """Fast trip the fuse has to outlast: R2 below R2; the later of R1 and R2 (reverse) above R2."""
    r = T4[node]
    return float(r["R2 fast (s)"]) if NODES[node]["zone"] == "R2" else max(float(r["R1 fast (s)"]), float(r["R2 fast (s)"]))


def step_table(steps, key_rows):
    rows = [["Step", "Working", "Result"]] + [list(s) for s in steps]
    return table(rows, [4.3 * cm, W - 4.3 * cm - 2.3 * cm, 2.3 * cm], key_rows=key_rows)


def diff(model, paper, nd=0):
    return "%+.*f %%" % (nd, 100.0 * (model - paper) / paper)


def record(node):
    row = T4[node]
    recs = [r for r in D["faults"] if r["case"] == "max" and r["dg"] == 1.0 and r["where"] == node
            and r["type"] == row["fault"]]
    return max(recs, key=lambda r: max(r["I"]["R1"]))


def implied_current(t_delayed):
    """Current through R1 that gives the paper's delayed time with the model's R1 settings."""
    lo, hi = 1.5 * R1["ip"], 40 * R1["ip"]
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if IACC.t(mid, R1["ip"], R1["tds_d"]) > t_delayed else (lo, mid)
    return lo


# ---------------------------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------------------------
story = []
story.append(p("How the recloser operating times and the fuse melting times are calculated", TITLE))
story.append(p("Replication of Yousaf et al. (2022), IEEE 13-node feeder, Table IV. All numbers are taken from the "
               "PowerFactory replication in <i>Replication/results</i> (studies.json, settings.json, Table_IV.csv).", SUB))

# ---- 1 summary -------------------------------------------------------------------------------
ex_chk, _, _ = None, None, None
_, ex_f, ex_d = iac_steps(4219.0)
pf = [r for f in ("conventional", "dsdr") for r in csv.DictReader(open(os.path.join(RES, "PF_vs_Python_times_%s.csv" % f)))]
pf_max = max(abs(float(r["deviation %"])) for r in pf)

story.append(p("1. Summary", H1))
story.append(p(
    "Each operating time is obtained in three steps: <b>(a)</b> the fault current through the recloser is read from "
    "the PowerFactory short-circuit study, <b>(b)</b> it is divided by the pickup setting to get the multiple "
    "<i>M</i>, and <b>(c)</b> <i>M</i> is put into the relay's time-current curve and scaled by the time dial. "
    "The fast and the delayed operation use the same curve with two different dials (and, for R2, two different "
    "plug settings). The fuse time <i>t</i><sub>MMT</sub> of Table IV is read from the fuse's minimum-melting curve at "
    "the current through the fuse (section 4.3)."))
story.append(p(
    "The two reclosers use different curves, so there are two calculation methods: R1 (GE IAC77B801A) has a closed "
    "formula, R2 (GE/Alstom CDG34) has a manufacturer's table that is interpolated. The replicated times do "
    "<b>not</b> equal the paper's Table IV: R1 is %s to %s slower in eleven of twelve rows (bus 652 is 34 %% faster). "
    "The R1 formula itself is confirmed by the paper's own worked example (section 3), so the difference comes from "
    "the fault currents; for R2 the paper does not publish the settings, so they had to be assumed (section 6)." % (
        "12 %", "78 %")))

# ---- 2 what is in table IV --------------------------------------------------------------------
story.append(p("2. Which operation each column of Table IV is", H1))
story.append(p(
    "The paper's eqs. (1) and (2) give the <b>forward</b> fast and delayed times, eqs. (10) and (11) the "
    "<b>reverse</b> ones. R1 only ever sees current from the grid, so both R1 columns are forward for every bus. "
    "R2 is the dual-setting directional recloser: it operates forward for faults downstream of it and reverse "
    "(DG current flowing back towards 632) for faults upstream of it."))
story.append(table([
    ["Faulted bus", "R1 fast / delayed", "R2 fast / delayed", "Formula in the paper"],
    ["632, 633, 645, 646, DL (upstream of R2)", "forward", "<b>reverse</b> setting group", "R1: eqs. (1), (2);  R2: eqs. (10), (11)"],
    ["671, 692, 675, 680, 684, 611, 652 (downstream of R2)", "forward", "<b>forward</b> setting group", "R1 and R2: eqs. (1), (2)"],
], [6.2 * cm, 2.9 * cm, 3.6 * cm, W - 12.7 * cm]))
story.append(Spacer(1, 6))

# ---- 3 settings ------------------------------------------------------------------------------
story.append(p("3. Settings used in the calculation", H1))
story.append(p("Pickup, eq. (3) of the paper (eq. (12) for the reverse direction), with OLF = 1.25:"))
story.append(equation("pickup", r"I_p = OLF \times I_{nom}"))
story.append(Spacer(1, 4))
inom1, inom2 = max(LF["dg_out"]["R1"]), max(LF["dg_out"]["R2"])
story.append(table([
    ["Recloser", "Load current I<sub>nom</sub>", "1.25 × I<sub>nom</sub>", "Setting actually used", "Time dial fast / delayed"],
    ["R1  IAC77B801A, forward", "%.1f A (load flow, DG out)" % inom1, "%.1f A" % (OLF * inom1),
     "tap %.0f A on CT 900/5 = <b>%.0f A</b>" % (R1["tap"], R1["ip"]), "TDS <b>%.1f / %.0f</b>" % (R1["tds_f"], R1["tds_d"])],
    ["R2  CDG34, forward", "%.1f A (load flow, DG out)" % inom2, "%.1f A" % FW["ip_eq3"],
     "CT 1000/5: fast plug %.1f A = <b>%.0f A</b>, delayed plug %.1f A = <b>%.0f A</b>" % (
         FW["tap_f"], FW["is_f"], FW["tap_d"], FW["is_d"]), "TMS <b>%.1f / %.1f</b>" % (FW["tms_f"], FW["tms_d"])],
    ["R2  CDG34, reverse", "%.1f A (load flow, DG in, towards 632)" % RV["i_nom_rv"], "%.1f A" % RV["ip_eq12"],
     "CT 500/5: fast plug %.1f A = <b>%.0f A</b>, delayed plug %.1f A = <b>%.0f A</b>" % (
         RV["tap_f"], RV["is_f"], RV["tap_d"], RV["is_d"]), "TMS <b>%.1f / %.1f</b>" % (RV["tms_f"], RV["tms_d"])],
], [3.3 * cm, 3.5 * cm, 1.9 * cm, W - 11.6 * cm, 2.9 * cm]))
story.append(Spacer(1, 4))
story.append(p(
    "For R2 the fast plug is half of 1.25 × I<sub>nom</sub> and the delayed plug equals 1.25 × I<sub>nom</sub>, because "
    "the CDG curve only begins at 2 × the plug setting. The fast curve therefore starts at about I<sub>p</sub> "
    "(600 A forward) and the delayed curve at 2 I<sub>p</sub> (1200 A forward). Only the R1 time dials are "
    "printed in the paper; the basis of every other value is given in section 6.", NOTE))

# ---- 4 methods -------------------------------------------------------------------------------
story.append(p("4. The two calculation methods", H1))
story.append(p("4.1  R1: GE IAC extremely inverse equation", H2))
story.append(p("The paper writes the recloser time in the general form of eqs. (1) and (2):"))
story.append(equation("generic", r"t = TDS \left[ \frac{A}{(I_f / I_p)^{n} - 1} + B \right]"))
story.append(p(
    "but does not give A, B and n. For the IAC77B801A the model uses the manufacturer's extremely inverse "
    "equation (PowerFactory library type <i>IAC Extremely Inverse GES7005B</i>), valid from 1.5 to 40 times pickup:"))
story.append(equation("iac", r"t = TDS \left[ 0.004 + \frac{0.6379}{M - 0.62} + \frac{1.7872}{(M - 0.62)^{2}} + "
                             r"\frac{0.2461}{(M - 0.62)^{3}} \right] , \qquad M = \frac{I_f}{I_p}"))
story.append(Spacer(1, 3))
story.append(p(
    "<b>Check against the paper.</b> The paper gives one worked example: for 4219 A downstream of F645, R1 "
    "operates in 0.097 s (fast) and 1.932 s (delayed). The same current in the equation above:"))
ex_steps, _, _ = iac_steps(4219.0)
story.append(step_table(ex_steps, (7, 8)))
m_ex = 4219.0 / R1["ip"]
ieee = 28.2 / (m_ex ** 2 - 1) + 0.1217
story.append(Spacer(1, 4))
story.append(p(
    "Result %.3f s and %.3f s against the paper's 0.097 s and 1.932 s (%s and %s). With the standard IEEE "
    "extremely inverse constants in eq. (1) (A = 28.2, B = 0.1217, n = 2) the same current would give %.3f s and "
    "%.2f s, five times too slow, so the IAC equation is the one the paper used. In every row of the paper's "
    "Table IV the R1 delayed time is 20 times the fast time, which is the ratio of the two dials, 10 / 0.5." % (
        ex_f, ex_d, diff(ex_f, 0.097, 1), diff(ex_d, 1.932, 1), R1["tds_f"] * ieee, R1["tds_d"] * ieee), NOTE))

story.append(p("4.2  R2: GE/Alstom CDG34, extremely inverse table", H2))
story.append(p(
    "The CDG extremely inverse characteristic (PowerFactory library type <i>Extremely Inverse No. 398.S23.37 "
    "CDG14</i>) is not a formula but a table of time against M = I<sub>f</sub> / I<sub>s</sub>, with one column per "
    "time multiplier from 0.1 to 1.0. The settings used here are exactly the first column (TMS 0.1, fast) and the "
    "last column (TMS 1.0, delayed), so only M has to be interpolated. Between two table rows the curve is "
    "taken as a straight line on log-log axes:"))
story.append(equation("cdg", r"t = t_1 \left( \frac{t_2}{t_1} \right)^{f} , \qquad f = \frac{\ln (M / M_1)}{\ln (M_2 / M_1)} , "
                             r"\qquad M = \frac{I_f}{I_s}"))
story.append(Spacer(1, 3))
story.append(p("Part of the table (seconds). Below M = 2 the relay does not operate; above M = 40 the time stays at the M = 40 value."))
part = [r for r in CDGC.rows if r[0] <= 12]
story.append(table(
    [["M = I<sub>f</sub> / I<sub>s</sub>"] + ["%.0f" % r[0] for r in part],
     ["TMS 0.1 (fast)"] + ["%g" % r[1] for r in part],
     ["TMS 1.0 (delayed)"] + ["%g" % r[10] for r in part]],
    [3.0 * cm] + [(W - 3.0 * cm) / len(part)] * len(part), font=TINY, pad=2.5))

story.append(p("4.3  Fuses: minimum melting time t<sub>MMT</sub> from the fuse curve", H2))
ex_fuse = T4[EXAMPLES[0]]["fuse"]
ex_fz = FUSE[ex_fuse]
story.append(p(
    "The paper describes a fuse by the straight line of eq. (6), log t = a log I + b with a = −1.8, and uses it "
    "to find the size that is needed (Table III). The time printed in Table IV is the melting time of the fuse "
    "that is actually installed. A fuse has no formula: the manufacturer gives the <b>minimum-melting</b> curve "
    "(the fuse element starts to melt, t<sub>MMT</sub>) and the <b>total-clearing</b> curve (the arc is out, "
    "t<sub>TCT</sub>) as points. The model uses the PowerFactory library fuses Gould-Shawmut A055C (5.5 kV, E-rated) and "
    "reads the curve at the fuse current with the same log-log interpolation as for the CDG table:"))
story.append(equation("fuse", r"t_{MMT} = t_1 \left( \frac{t_2}{t_1} \right)^{f} , \qquad f = \frac{\ln (I_{fuse} / I_1)}{\ln (I_2 / I_1)}"))
story.append(Spacer(1, 3))
story.append(p(
    "<b>I<sub>fuse</sub> is the current through the fuse, not the recloser current.</b> With the DG in service a fuse "
    "between the two sources and the fault carries the grid share and the DG share together, so it sees more current "
    "than either recloser. Example at bus 633: R1 carries %s A, R2 (reverse) %s A, the fuse F633 %s A." % (
        T4["633"]["I R1 (A)"], T4["633"]["I R2 (A)"], T4["633"]["I fuse (A)"])))
pts = [q for q in ex_fz.melt if q[1] <= 100][-9:]
story.append(p("Minimum-melting points of %s (%s), the fuse of the first example:" % (S["fuses"][ex_fuse], ex_fuse)))
story.append(table([["Current (A)"] + ["%.0f" % q[0] for q in pts], ["t<sub>MMT</sub> (s)"] + ["%.3g" % q[1] for q in pts]],
                   [2.6 * cm] + [(W - 2.6 * cm) / len(pts)] * len(pts), font=TINY, pad=2.5))
story.append(Spacer(1, 4))
story.append(p(
    "Coordination needs t<sub>MMT</sub> to be longer than the recloser's fast trip (fuse saving) and t<sub>TCT</sub> "
    "to be shorter than the delayed trip (the fuse clears a permanent fault before the recloser locks out).", NOTE))

# ---- 5 worked examples -----------------------------------------------------------------------
story.append(PageBreak())
story.append(p("5. Worked examples for five buses", H1))
story.append(p(
    "Fault currents are from the PowerFactory short-circuit study with the DG in service (4.05 MVA at 692) and a "
    "bolted fault. The current used for each recloser is the largest of its three phase currents. Buses %s are in "
    "R1's zone (R2 operates in reverse); buses %s are downstream of R2 (R2 operates forward)." % (
        " and ".join(n for n in EXAMPLES if NODES[n]["zone"] == "R1"),
        ", ".join(n for n in EXAMPLES if NODES[n]["zone"] == "R2")), P))

for k, node in enumerate(EXAMPLES, 1):
    row, rec = T4[node], record(node)
    i1, i2 = max(rec["I"]["R1"]), max(rec["I"]["R2"])
    fwd = NODES[node]["zone"] == "R2"
    unit = FW if fwd else RV
    s1, t1f, t1d = iac_steps(i1)
    s2f, s2d, t2f, t2d = cdg_steps(i2, unit)
    # the hand calculation must reproduce the pipeline's Table_IV.csv
    for mine, ref in ((t1f, "R1 fast (s)"), (t1d, "R1 delayed (s)"), (t2f, "R2 fast (s)"), (t2d, "R2 delayed (s)")):
        assert "%.3f" % mine == row[ref], (node, ref, mine, row[ref])
    paper = PAPER_TABLE4[node]
    block = [p("Example %d: bus %s, %s fault on phases %s" % (k, node, FAULT_NAME[row["fault"]], rec["phases"]), H2),
             p("Current through R1: <b>%.1f A</b>.  Current through R2: <b>%.1f A</b> (%s)." % (
                 i1, i2, "forward, from the grid" if fwd else "reverse, DG contribution only")),
             p("R1 forward, I<sub>p</sub> = %.0f A" % R1["ip"], CELLB), Spacer(1, 2), step_table(s1, (7, 8))]
    story.append(KeepTogether(block))
    story.append(Spacer(1, 6))
    story.append(KeepTogether([
        p("R2 %s, fast: I<sub>s</sub> = %.0f A, TMS %.1f" % ("forward" if fwd else "reverse", unit["is_f"], unit["tms_f"]), CELLB),
        Spacer(1, 2), step_table(s2f, (4,)), Spacer(1, 5),
        p("R2 %s, delayed: I<sub>s</sub> = %.0f A, TMS %.1f" % ("forward" if fwd else "reverse", unit["is_d"], unit["tms_d"]), CELLB),
        Spacer(1, 2), step_table(s2d, (4,))]))
    story.append(Spacer(1, 6))
    fname = row["fuse"]
    if fname != "---":
        i_f = max(rec["I"][fname])
        sm, tm = fuse_steps(i_f, FUSE[fname])
        sc, tc = fuse_steps(i_f, FUSE[fname], clear=True)
        assert "%.3f" % tm == row["fuse MMT (s)"] and "%.3f" % tc == row["fuse TCT (s)"], (node, tm, tc, row)
        lf = last_fast(node)
        story.append(KeepTogether([
            p("Fuse %s (%s): current through the fuse <b>%.1f A</b>, minimum-melting curve" % (fname, S["fuses"][fname], i_f), CELLB),
            Spacer(1, 2), step_table(sm, (len(sm),)), Spacer(1, 5),
            p("Fuse %s, total-clearing curve" % fname, CELLB), Spacer(1, 2), step_table(sc, (len(sc),)), Spacer(1, 3),
            p("Fuse saving: t<sub>MMT</sub> %.3f s − last fast trip %.3f s = <b>%+.3f s</b> (%s).  Permanent fault: "
              "t<sub>TCT</sub> %.3f s, first delayed trip %.3f s (%s)." % (
                  tm, lf, tm - lf, "the recloser trips first" if tm > lf else "the fuse melts first", tc, min(t1d, t2d),
                  "the fuse clears first" if tc < min(t1d, t2d) else "the recloser trips first"), NOTE)]))
        story.append(Spacer(1, 6))
        fcol = ["%.3f s" % tm, "%.3f s" % paper[4], diff(tm, paper[4])]
    else:
        fcol = ["no fuse", "---", "---"]
    story.append(KeepTogether([table([
        ["Bus %s" % node, "R1 fast", "R1 delayed", "R2 fast (%s)" % ("fwd" if fwd else "rev"), "R2 delayed (%s)" % ("fwd" if fwd else "rev"),
         "Fuse t<sub>MMT</sub>"],
        ["Calculated above", "%.3f s" % t1f, "%.3f s" % t1d, "%.3f s" % t2f, "%.3f s" % t2d, fcol[0]],
        ["Paper, Table IV", "%.3f s" % paper[0], "%.3f s" % paper[1], "%.3f s" % paper[2], "%.3f s" % paper[3], fcol[1]],
        ["Difference", diff(t1f, paper[0]), diff(t1d, paper[1]), diff(t2f, paper[2]), diff(t2d, paper[3]), fcol[2]],
    ], [3.1 * cm] + [(W - 3.1 * cm) / 5] * 5)]))
    story.append(Spacer(1, 12))

# ---- all rows --------------------------------------------------------------------------------
story.append(PageBreak())
story.append(p("All twelve rows of Table IV", H2))
story.append(p("The same two calculations for every bus (model value / paper value, seconds). The examples of "
               "section 5 are highlighted. The last column is the current R1 would need in order to give the "
               "paper's delayed time with the settings of section 3."))
head = ["Bus", "Fault", "I<sub>R1</sub> (A)", "R1 fast", "R1 delayed", "R2", "I<sub>R2</sub> (A)", "R2 fast", "R2 delayed",
        "I<sub>R1</sub> from paper (A)"]
rows, keys = [head], []
for n, node in enumerate(T4, 1):
    r, pp = T4[node], PAPER_TABLE4[node]
    rows.append([node, r["fault"], r["I R1 (A)"], "%s / %.3f" % (r["R1 fast (s)"], pp[0]),
                 "%s / %.3f" % (r["R1 delayed (s)"], pp[1]), r["R2 unit"], r["I R2 (A)"],
                 "%s / %.3f" % (r["R2 fast (s)"], pp[2]), "%s / %.3f" % (r["R2 delayed (s)"], pp[3]),
                 "%.0f" % implied_current(pp[1])])
    if node in EXAMPLES:
        keys.append(n)
story.append(table(rows, [1.0 * cm, 1.2 * cm, 1.4 * cm, 2.3 * cm, 2.5 * cm, 0.9 * cm, 1.4 * cm, 2.3 * cm, 2.5 * cm,
                          W - 15.5 * cm], key_rows=keys, font=SMALL))

story.append(Spacer(1, 8))
story.append(p("Fuse column of Table IV", H2))
story.append(p("Fuse nearest to the fault on the path from the reclosers, its size after step 9 of the method, the current "
               "through it and the two fuse times. Margin = t<sub>MMT</sub> − last fast trip (R2 for faults downstream of R2; "
               "the later of R1 and R2 reverse upstream of it). Buses 632, 671 and 680 are on the main feeder and have no fuse."))
frows, fkeys = [["Bus", "Fault", "Fuse", "Size", "I<sub>fuse</sub> (A)", "t<sub>MMT</sub> model / paper", "Diff.",
                 "t<sub>TCT</sub> (s)", "Last fast trip (s)", "Margin (s)", "Status"]], []
for node in T4:
    r, pp = T4[node], PAPER_TABLE4[node]
    if r["fuse"] == "---":
        continue
    lf = last_fast(node)
    frows.append([node, r["fault"], r["fuse"], SIZE[r["fuse"]], r["I fuse (A)"], "%s / %.3f" % (r["fuse MMT (s)"], pp[4]),
                  diff(float(r["fuse MMT (s)"]), pp[4]), r["fuse TCT (s)"], "%.3f" % lf,
                  "%+.3f" % (float(r["fuse MMT (s)"]) - lf), r["status"]])
    if node in EXAMPLES:
        fkeys.append(len(frows) - 1)
story.append(table(frows, [1.0 * cm, 1.1 * cm, 1.5 * cm, 1.2 * cm, 1.4 * cm, 2.7 * cm, 1.4 * cm, 1.4 * cm, 1.7 * cm, 1.5 * cm,
                           W - 14.9 * cm], key_rows=fkeys, font=SMALL))

# ---- 6 assumptions ---------------------------------------------------------------------------
story.append(p("6. Assumptions and their basis", H1))
story.append(p("The paper states the relay types, OLF = 1.25 and R1's two time dials. Everything else below had to "
               "be chosen; the right-hand column says on what basis."))
A = [
    ["#", "Value used", "In the paper?", "Basis"],
    ["1", "R1 time dials 0.5 (fast) and 10 (delayed)", "Yes", "Section IV-A of the paper."],
    ["2", "R1 curve is the GE IAC extremely inverse equation, not eq. (1) with IEEE or IEC constants",
     "Relay type only", "The paper names the IAC77B801A but gives no A, B, n. This equation reproduces the paper's "
     "worked example (4219 A → 0.097 / 1.932 s) as %.3f / %.3f s; IEEE constants give %.3f / %.2f s." % (
         ex_f, ex_d, R1["tds_f"] * ieee, R1["tds_d"] * ieee)],
    ["3", "R1 pickup 720 A (tap 4 A on a 900/5 CT) instead of 1.25 × %.1f = %.1f A" % (inom1, OLF * inom1), "No",
     "A relay is set on discrete taps. The CT ratio is my choice. Solving the paper's worked example backwards for "
     "the pickup gives 722 A, so 720 A fits better than 734.6 A (which gives %.3f / %.3f s)." % (
         IACC.t(4219, OLF * inom1, 0.5), IACC.t(4219, OLF * inom1, 10))],
    ["4", "R2 curve is the CDG14 extremely inverse table, interpolated log-log between rows", "Relay type only",
     "The paper names the CDG34 with extremely inverse characteristic. PowerFactory's own relay and fuse models "
     "agree with this calculation on %d operating times, largest deviation %.2f %%." % (len(pf), pf_max)],
    ["5", "R2 forward plug settings 300 A (fast) and 600 A (delayed) on a 1000/5 CT", "No",
     "1.25 × %.1f A = %.1f A by eq. (3). The CDG curve begins at 2 × plug, and in the paper's Figs. 8 and 13 R2's "
     "fast curve begins near I<sub>p</sub> and the delayed curve near 2 I<sub>p</sub>. <b>This is the largest "
     "assumption</b>: the paper never prints R2's settings." % (inom2, FW["ip_eq3"])],
    ["6", "R2 time multipliers 0.1 (fast) and 1.0 (delayed)", "No",
     "Fast: the lowest dial of the relay. Delayed: the highest dial that still operates at least 10 cycles before "
     "R1's delayed curve for every fault downstream of R2 (the paper's criterion for the two reclosers)."],
    ["7", "R2 reverse plug settings 150 A and 300 A on a 500/5 CT, same dials", "No",
     "Eq. (12): 1.25 × %.1f A reverse load current = %.1f A, then the same rule as item 5." % (RV["i_nom_rv"], RV["ip_eq12"])],
    ["8", "Bolted fault, DG in service; LLL at three-phase buses, LL at two-phase buses (645, 646, 684), LG at "
     "single-phase buses (611, 652)", "No", "Table IV does not state the fault type or impedance of any row. The "
     "largest fault the bus can have was taken."],
    ["9", "Largest phase current through the recloser is the operating current", "No",
     "An overcurrent relay trips on its fastest (highest-current) phase element."],
    ["10", "Source: study case with the 115/4.16 kV, 5 MVA substation transformer", "No",
     "It reproduces the IEEE 13-node short-circuit benchmark within about 2 %. The paper's source impedance is not given."],
    ["11", "R2's direction is decided by fault location (upstream of R2 = reverse)", "Implied",
     "PowerFactory's CDG34 has no directional element. The paper itself uses R2 reverse for the fault at 646."],
    ["12", "Fuses are Gould-Shawmut A055C (E-rated); t<sub>MMT</sub> and t<sub>TCT</sub> are read from the library curves, "
     "log-log between points", "No",
     "The paper gives no fuse make and no fuse curve data, only eq. (6) with a = −1.8. A real curve is needed to get a time; "
     "PowerFactory's own fuse model returns the same times (item 4)."],
    ["13", "Fuse sizes: %s" % ", ".join("%s %s" % (n, SIZE[n]) for n in sorted({r["fuse"] for r in T4.values() if r["fuse"] != "---"})),
     "Partly", "Starting sizes from the paper's figures and ref. [8]; then raised by step 9 of the method until the fuse outlasts "
     "the fast trips with the DG in service. The sizes behind the paper's Table IV are not printed."],
    ["14", "The fuse time is taken at the current through the fuse (largest phase), which includes the DG share", "Implied",
     "The fuse melts on its own current. Paper, Fig. 15: the fuse F646 carries 3.64 kA while R2 carries 1.54 kA."],
]
story.append(table(A, [0.95 * cm, 5.3 * cm, 2.1 * cm, W - 8.35 * cm], key_rows=(5,)))

# ---- 7 why different -------------------------------------------------------------------------
story.append(p("7. Why the values differ from the paper's Table IV", H1))
r633 = T4["633"]
story.append(p(
    "<b>R1.</b> The equation and settings reproduce the paper's worked example, so the difference is in the "
    "current fed into the equation. Example: at bus 633 the model has %s A through R1 and gets %s s; the paper's "
    "%.3f s needs %.0f A. The model's fault levels follow the IEEE benchmark and are lower than the paper's "
    "(feeder-head maximum 4.73 kA against the paper's 5.41 kA in Table II). Bus 652 is the opposite: the paper's "
    "13.525 s corresponds to only %.0f A, which is less than the model's LG fault current there, so that row was "
    "probably computed for a fault through impedance or a different fault type." % (
        r633["I R1 (A)"], r633["R1 delayed (s)"], PAPER_TABLE4["633"][1], implied_current(PAPER_TABLE4["633"][1]),
        implied_current(PAPER_TABLE4["652"][1]))))
story.append(p(
    "<b>R2.</b> Besides the current, the settings themselves are assumed (items 5 to 7), because the paper "
    "does not print them and they cannot be read back from Table IV. The fast times come out between 37 % below "
    "and 15 % above the paper's; the delayed times between 30 % below and 183 % above. These R2 values should be "
    "read as the result of the stated method, not as a match to the paper."))
fd = [(n, 100.0 * (float(T4[n]["fuse MMT (s)"]) - PAPER_TABLE4[n][4]) / PAPER_TABLE4[n][4]) for n in T4 if T4[n]["fuse"] != "---"]
story.append(p(
    "<b>Fuses.</b> The fuse times differ from the paper's by %.0f %% (bus %s) to %+.0f %% (bus %s). A fuse curve is "
    "steep (t falls roughly with I<super>−2</super> to I<super>−3</super>), so a 20 %% difference in current already changes "
    "t<sub>MMT</sub> by 40 to 70 %%, and a different fuse size by more. The paper gives neither the sizes nor the fuse currents behind its column, "
    "so this column is the result of the method on this model; what can be checked is the criterion itself: "
    "t<sub>MMT</sub> is longer than the last fast trip in %d of %d rows (margin column above)." % (
        min(fd, key=lambda x: x[1])[1], min(fd, key=lambda x: x[1])[0], max(fd, key=lambda x: x[1])[1], max(fd, key=lambda x: x[1])[0],
        sum(float(T4[n]["fuse MMT (s)"]) > last_fast(n) for n, _ in fd), len(fd))))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(INK2)
    canvas.drawString(1.8 * cm, 1.1 * cm, "Recloser and fuse operating-time calculation - Yousaf et al. (2022) replication, Table IV")
    canvas.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, "Page %d" % doc.page)
    canvas.restoreState()


SimpleDocTemplate(OUT, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.7 * cm, bottomMargin=1.9 * cm,
                  title="Recloser and fuse operating-time calculation",
                  author="Yousaf 2022 replication").build(story, onFirstPage=footer, onLaterPages=footer)
print("written", OUT)
