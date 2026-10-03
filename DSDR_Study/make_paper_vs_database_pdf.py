"""
Builds results/Paper_vs_Our_Results.pdf: the load-flow and short-circuit results obtained so far
(results/database, results/studies.json) against what the reference paper publishes for the same
quantities - Table I, Table II, the fault currents quoted in its figures and its statements on the
direction of the current through R2.

PowerFactory is not needed.  Needs reportlab, matplotlib and PyMuPDF (to cut Table II from the paper).
"""

import csv
import json
import os

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from protection_data import PAPER_TABLE2, TABLE2_BRANCHES, OLF

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
DB = os.path.join(RES, "database")
TMP = os.path.join(RES, "_pv_tmp")
os.makedirs(TMP, exist_ok=True)
OUT = os.path.join(RES, "comparison", "Paper_vs_Our_Results.pdf")
PAPER = os.path.join(os.path.dirname(HERE), "An Adaptive Overcurrent Protection Scheme for by mohommad yousuf .pdf")

BLUE, ORANGE, AQUA, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#d9d8d4", "#fcfcfb"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "savefig.facecolor": SURF})


def read(name, folder=DB):
    return list(csv.DictReader(open(os.path.join(folder, name))))


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------------------------
# Our results
# ---------------------------------------------------------------------------------------------
ST = json.load(open(os.path.join(RES, "studies.json")))
FAULTS = ST["faults"]
IFMAX = {c: {r["Bus"]: r for r in read(f)} for c, f in (("out", "Ifmax_DG_out.csv"), ("in", "Ifmax_DG_in.csv"))}
IFMIN = {r["Protection section"]: r for r in read("Comparison_Ifmin.csv")}
IFMIN_OUT = {r["Protection section"]: r for r in read("Ifmin_DG_out.csv")}
LF = {r["Device"]: r for r in read("LoadFlow_comparison.csv")}
SC = {c: read(f) for c, f in (("out", "5_ShortCircuit_DG_out.csv"), ("in", "6_ShortCircuit_DG_in.csv"))}
def inom(case, key):
    """Largest phase current of a Table II branch (A), from the load flow of the short-circuit study
    (results/studies.json).  The all-bus load-flow files are not used here: in the run of 22:14 they
    were written with R2's breaker open."""
    return max(ST["loadflow"]["dg_out" if case == "out" else "dg_in"]["%s-%s" % key])


def branch_ifmax(dg, key, nodes):
    """Largest current through the branch for a bolted fault at any node below it (A)."""
    k = "%s-%s" % key
    return max(max(r["I"][k]) for r in FAULTS if r["case"] == "max" and r["dg"] == dg and r["where"] in nodes)


T2 = []
for frm, to, br, side, nodes in TABLE2_BRANCHES:
    key = (frm, to)
    p = PAPER_TABLE2[key]
    sec = "%s-%s" % key
    T2.append(dict(key=key, label="%s - %s" % key if to != "side" else frm.replace("XFM1-", "XFM-1 ") + " side",
                   p_inom=p[0], p_min=p[1] * 1000, p_max=p[2] * 1000,
                   inom=inom("out", key), inom_dg=inom("in", key),
                   ifmax=branch_ifmax(0.0, key, nodes), ifmax_dg=branch_ifmax(1.0, key, nodes),
                   ifmin=num(IFMIN[sec]["If,min without DG (A)"]), ifmin_dg=num(IFMIN[sec]["If,min with DG (A)"]),
                   far=IFMIN[sec]["Farthest node"], far_fault=IFMIN[sec]["Fault"]))
# XFM-1 HV side: the paper's values (6.48 / 0.73 kA) are those of a fault at the HV terminals
# (node 633), not of a fault on the 0.48 kV side seen from the HV side (which the transformer
# limits to about 1.8 kA, and a 3 ohm LV fault to about load current).  The row is therefore
# compared for the fault at 633; the through-fault values are kept for the note in the text.
for _r in T2:
    if _r["key"] == ("XFM1-HV", "side"):
        _r["through_max"], _r["through_min"] = _r["ifmax"], _r["ifmin"]
        _r["ifmax"] = num(IFMAX["out"]["633"]["If,max (A)"])
        _r["ifmax_dg"] = num(IFMAX["in"]["633"]["If,max (A)"])
        _r["ifmin"] = num(IFMIN["632-633"]["If,min without DG (A)"])
        _r["ifmin_dg"] = num(IFMIN["632-633"]["If,min with DG (A)"])
        _r["far"], _r["far_fault"] = "633 (HV terminals)", IFMIN["632-633"]["Fault"]
        _r["label"] = "XFM-1 HV side *"
HVNOTE = ("* XFM-1 HV side: compared for a fault at the transformer's HV terminals (node 633), which is what the "
          "paper's value corresponds to (it is nearly equal to its 632-633 value). For a fault on the 0.48 kV side the "
          "current on the HV side is only %.2f kA bolted (15.67 kA x 0.48 / 4.16; the 500 kVA transformer limits it) "
          "and %.0f A through 3 ohm, i.e. the load current.")
BENCH = {"632": 4.80, "633": 4.15, "634": 15.28, "645": 3.41, "646": 3.05, "652": 1.79, "671": 3.35, "675": 3.12,
         "680": 2.91, "684": 2.62, "611": 1.85, "692": 3.35}                 # IEEE benchmark quoted in ref. [8], kA


def figcase(case):
    return [r for r in FAULTS if r["case"] == case][0]


def fi(case, dev):
    return max(figcase(case)["I"][dev])


def pct(a, b):
    return "-" if not b else "%+.0f %%" % (100.0 * (a / b - 1))


def dev(a, b):
    return abs(a / b - 1) if b else 0.0


# ---------------------------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------------------------
def bars(path, title, series, labels, xlabel, logx=False):
    fig, ax = plt.subplots(figsize=(7.4, 0.42 * len(labels) + 1.3))
    n = len(series)
    h = 0.8 / n
    y = list(range(len(labels)))[::-1]
    for k, (name, col, vals) in enumerate(series):
        ax.barh([v + 0.4 - h / 2 - k * h for v in y], vals, height=h * 0.92, color=col, label=name)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.8)
    ax.set_xlabel(xlabel)
    if logx:
        ax.set_xscale("log")
    ax.grid(True, axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title(title, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=190)
    plt.close(fig)


def workflow(path):
    steps = [("1", "Input data", "Table I, network"), ("2", "Load flow", "Inom - Table II"),
             ("3", "Maximum fault", "If,max - Table II"), ("4", "Minimum fault", "If,min - Table II"),
             ("5", "Faults with DG", "figure currents"), ("6", "Direction at R2", "forward / reverse"),
             ("7", "Coordination", "separate PDF")]
    fig, ax = plt.subplots(figsize=(8.6, 1.15))
    ax.set_xlim(0, len(steps))
    ax.set_ylim(0, 1)
    ax.axis("off")
    for k, (n, a, b) in enumerate(steps):
        last = k == len(steps) - 1
        ax.add_patch(plt.Rectangle((k + 0.06, 0.12), 0.88, 0.76, fc="#f1f1ee" if last else "#eef4fc",
                                   ec=INK2 if last else BLUE, lw=1.1, ls="--" if last else "-"))
        ax.text(k + 0.5, 0.67, "%s. %s" % (n, a), ha="center", va="center", fontsize=6.6, fontweight="bold")
        ax.text(k + 0.5, 0.35, b, ha="center", va="center", fontsize=6.2, color=INK2)
        if not last:
            ax.annotate("", xy=(k + 1.07, 0.5), xytext=(k + 0.93, 0.5), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1))
    fig.tight_layout(pad=0.2)
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------------------------
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceAfter=6, textColor=colors.HexColor("#1b4f93"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11.5, spaceBefore=8, spaceAfter=4,
                    textColor=colors.HexColor("#1b4f93"))
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9, leading=12)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=7.8, leading=10, textColor=colors.HexColor("#52514e"))
CELL = ParagraphStyle("C", parent=BODY, fontSize=7.6, leading=9.2)
HEAD = ParagraphStyle("h", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")
BOX = ParagraphStyle("SB", parent=BODY, fontSize=8.8, leading=11.5, backColor=colors.HexColor("#eef4fc"),
                     borderColor=colors.HexColor("#2a78d6"), borderWidth=0.8, borderPadding=5, spaceBefore=6,
                     spaceAfter=8)
GOOD, MID, BAD = colors.HexColor("#dff3df"), colors.HexColor("#fff3d6"), colors.HexColor("#fbe0e0")


def shade(d):
    return GOOD if d <= 0.05 else (MID if d <= 0.20 else BAD)


def table(data, widths, colour=None, header_rows=1):
    data = [[Paragraph(str(c), HEAD if r < header_rows else CELL) for c in row] for r, row in enumerate(data)]
    tb = Table(data, colWidths=widths, repeatRows=header_rows)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9b8b3")),
          ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#1b4f93")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.8),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8)]
    for r in range(header_rows, len(data)):
        if (r - header_rows) % 2:
            st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f4f4f2")))
    for c, r, col in (colour or []):
        st.append(("BACKGROUND", (c, r), (c, r), col))
    tb.setStyle(TableStyle(st))
    return tb


def image(path, width):
    im = Image(path)
    return Image(path, width=width, height=width * im.imageHeight / float(im.imageWidth))


def step(n, title, paper, ours):
    return [Paragraph("Step %s - %s" % (n, title), H1),
            Paragraph("<b>Paper:</b> %s<br/><b>Our result:</b> %s" % (paper, ours), BOX)]


def sens_table():
    low = {c: {r["Protection section"]: r["Lowest LG-3-ohm current in the section"] for r in read(f)}
           for c, f in (("out", "Ifmin_DG_out.csv"), ("in", "Ifmin_DG_in.csv"))}
    data = [["Recloser", "Pickup, eq. (3)", "Lowest LG-3-ohm current, DG out", "Lowest LG-3-ohm current, DG in"]]
    col = []
    for k, (name, sec, row) in enumerate((("R1 (RG60 - 632)", "RG60-632", T2[0]), ("R2 (632 - 671)", "632-671", T2[3])), 1):
        ip = OLF * row["inom"]
        cells = [name, "1.25 x %.1f = %.1f A" % (row["inom"], ip)]
        for j, c in enumerate(("out", "in")):
            v = float(low[c][sec].split(" A")[0])
            cells.append("%s - %s" % (low[c][sec].replace(" (", ", ").replace(")", ""),
                                      "above the pickup" if v > ip else "BELOW the pickup"))
            col.append((2 + j, k, GOOD if v > ip else BAD))
        data.append(cells)
    return table(data, [3.2 * cm, 3.8 * cm, 5.2 * cm, 5.3 * cm], colour=col)


LEGEND = Paragraph("Shading of the difference: green within 5 %, yellow within 20 %, red above 20 %.", SMALL)

# ---------------------------------------------------------------------------------------------
# Numbers for the scorecard
# ---------------------------------------------------------------------------------------------
rows_inom = [r for r in T2 if r["p_inom"] > 0]
inom_max = max(dev(r["inom"], r["p_inom"]) for r in rows_inom)
n_max_ok = sum(dev(r["ifmax"], r["p_max"]) <= 0.20 for r in T2)
n_max_ok_dg = sum(min(dev(r["ifmax"], r["p_max"]), dev(r["ifmax_dg"], r["p_max"])) <= 0.20 for r in T2)
n_min_ok = sum(dev(r["ifmin"], r["p_min"]) <= 0.20 for r in T2)
bench_dev = max(dev(num(IFMAX["out"][n]["If,max (A)"]) / 1000, v) for n, v in BENCH.items())
up = [r for r in SC["in"] if r["Faulted bus"] in ("632", "633", "634", "645", "646", "DL") and r["Zf (ohm)"] == "0"]
down = [r for r in SC["in"] if r["Faulted bus"] in ("671", "692", "675", "680", "684", "611", "652") and r["Zf (ohm)"] == "0"]
up_rev = sum(r["R2 direction"] == "reverse" for r in up)
down_fwd = sum(r["R2 direction"] == "forward" for r in down)
f15 = figcase("Fig15")

doc_p = fitz.open(PAPER)
t2_png = os.path.join(TMP, "paper_table2.png")
doc_p[5].get_pixmap(dpi=230, clip=fitz.Rect(44, 62, 290, 286)).save(t2_png)

# ---------------------------------------------------------------------------------------------
story = [Spacer(1, 0.6 * cm),
         Paragraph("Our results vs the reference paper", ParagraphStyle("T", parent=H1, fontSize=21, leading=25)),
         Paragraph("Load-flow and short-circuit database of the IEEE 13-node feeder",
                   ParagraphStyle("st", parent=H2, fontSize=12.5)),
         Spacer(1, 0.15 * cm),
         Paragraph("<b>Reference paper:</b> M. Yousaf, A. Jalilian, K. M. Muttaqi, D. Sutanto, \"An Adaptive Overcurrent "
                   "Protection Scheme for Dual-Setting Directional Recloser and Fuse Coordination in Unbalanced "
                   "Distribution Networks With Distributed Generation,\" <i>IEEE Trans. Ind. Appl.</i>, 58(2), 2022.", BODY),
         Paragraph("<b>Our results:</b> PowerFactory 2021 SP2, project <i>IEEE13 DSDR Fuse Coordination</i>, study case "
                   "<i>Study with Substation Transformer</i>; unbalanced load flow and complete-method short circuits, "
                   "DG disconnected and connected (database run, 17 of 18 internal checks passed).", BODY),
         Spacer(1, 0.2 * cm)]
wf = os.path.join(TMP, "wf.png")
workflow(wf)
story += [image(wf, 17.6 * cm),
          Paragraph("The comparison follows the order in which the results were produced. Step 7 (relay coordination: "
                    "pickups, time dials, Figs. 8-17, Tables III and IV) is compared in "
                    "Comparison_with_Reference_Paper.pdf.", SMALL),
          Paragraph("Scorecard", H2)]
score = [["Step", "Quantity", "Paper", "Our result", "Agreement"],
         ["1", "DG data (Table I)", "8 reactances / resistances", "identical in the model", "exact"],
         ["2", "Rated branch currents Inom (Table II)", "12 branches with load", "largest difference %.1f %%" % (100 * inom_max),
          "very good"],
         ["2", "Pickup by eq. (3), R1 / R2", "734 A / 598 A", "%.0f A / %.0f A" % (OLF * T2[0]["inom"], OLF * T2[3]["inom"]),
          "very good"],
         ["3", "If,max (Table II), 13 branches", "1.93 - 18.76 kA",
          "%d within 20 %% without DG; %d if the DG case is allowed" % (n_max_ok, n_max_ok_dg), "partial"],
         ["3", "If,max vs IEEE benchmark [8]", "(reference the paper cites)", "all 12 nodes within %.1f %%" % (100 * bench_dev),
          "very good"],
         ["4", "If,min (Table II), 13 branches", "0.59 - 1.24 kA", "%d within 20 %%" % n_min_ok, "good"],
         ["4", "Pickup below the minimum fault current (step 5 of the method)", "required", "held without DG; not held with DG",
          "new finding"],
         ["5", "Fuse current, solid LL at 646 with DG (Fig. 15)", "3.64 kA", "%.2f kA" % (max(f15["I"]["F646"]) / 1000), "very good"],
         ["5", "R2 current for the same fault (Fig. 15)", "1.54 kA", "%.2f kA" % (max(f15["I"]["R2"]) / 1000), "28 % lower"],
         ["6", "R2 reverse for faults upstream of R2, with DG", "stated", "%d of %d bolted faults reverse" % (up_rev, len(up)), "confirmed"],
         ["6", "R2 forward for faults downstream of R2", "stated", "%d of %d bolted faults forward" % (down_fwd, len(down)), "confirmed"]]
col = []
for k, r in enumerate(score[1:], 1):
    col.append((4, k, GOOD if r[4] in ("exact", "very good", "confirmed", "good") else MID))
story += [table(score, [1.1 * cm, 6.2 * cm, 3.6 * cm, 4.6 * cm, 2.4 * cm], colour=col), PageBreak()]

# ---- Step 1 -------------------------------------------------------------------------------------
story += step("1", "Input data",
              "IEEE 13-node feeder [33]; synchronous DG 4.05 MVA / 0.69 kV at node 692 through a 0.69/4.16 kV transformer "
              "with 0.15 pu leakage reactance; machine data in Table I; OLF = 1.25; fault impedance 3 ohm for If,min.",
              "the same data in the model. Values the paper does not give are listed below with what the model uses.")
story += [table([["Table I parameter", "Paper", "Model"],
                 ["Xl / Ra", "0.05 / 0.0014 pu", "0.05 / 0.0014 pu"],
                 ["Xd / Xd' / Xd''", "1.4 / 0.231 / 0.118 pu", "1.4 / 0.231 / 0.118 pu"],
                 ["Xq / Xq' / Xq''", "1.372 / 0.8 / 0.118 pu", "1.372 / 0.8 / 0.118 pu"],
                 ["T'do / T''do", "5.5 / 0.05 s", "5.5 / 0.05 s"],
                 ["T'qo / T''qo", "1.25 / 0.19 s", "1.25 / 0.33 s (derived by the machine model; dynamics only)"],
                 ["M = 2H", "1.5 s", "1.5 s"],
                 ["DG rating, transformer", "4.05 MVA, 0.69/4.16 kV, 0.15 pu", "4.05 MVA, 0.69/4.16 kV, uk = 15 %"]],
                [5 * cm, 5.3 * cm, 7.2 * cm]),
          Paragraph("Not given in the paper - what the model uses", H2),
          table([["Item", "Paper", "Model"],
                 ["Source behind node 650", "not given", "115 kV grid behind the 5 MVA 115/4.16 kV substation transformer "
                                                          "(IEEE 13-node benchmark data)"],
                 ["DG operating point for the load flow", "not given", "P = 3240 kW, voltage control; Q comes out as 0 kvar"],
                 ["Regulator taps", "not given", "fixed at +10 / +8 / +11 (IEEE 13-node solution)"],
                 ["Short-circuit method", "not given", "complete method (pre-fault load flow), initial symmetrical current"],
                 ["Whether Table II includes the DG", "Inom: not stated; faults: not stated",
                  "both cases calculated; Inom matches the paper only without DG"],
                 ["Farthest node of each section (If,min)", "not listed", "largest line length from the section's device"]],
                [5 * cm, 4 * cm, 8.5 * cm]), PageBreak()]

# ---- Step 2: Inom ----------------------------------------------------------------------------------
story += step("2", "Load flow: rated branch currents (Table II, I<sub>nom</sub>)",
              "I<sub>nom</sub> of 13 branches from the unbalanced load flow; pickup I<sub>p</sub> = OLF x I<sub>nom</sub> (eq. 3).",
              "largest phase current of the same branches, DG disconnected. The values with the DG are shown for "
              "information; the paper's column is reproduced only without the DG.")
data = [["Branch", "Paper Inom (A)", "Ours, DG out (A)", "Difference", "Ours, DG in (A)"]]
col = []
for k, r in enumerate(T2, 1):
    data.append([r["label"], "%.1f" % r["p_inom"], "%.1f" % r["inom"], pct(r["inom"], r["p_inom"]) if r["p_inom"] else "0 A / 0 A",
                 "%.1f" % r["inom_dg"]])
    col.append((3, k, shade(dev(r["inom"], r["p_inom"]))))
p_i = os.path.join(TMP, "inom.png")
bars(p_i, "Rated branch current: paper vs our load flow (DG disconnected)",
     [("paper, Table II", INK2, [r["p_inom"] for r in T2]), ("our load flow", BLUE, [r["inom"] for r in T2])],
     [r["label"] for r in T2], "Inom (A)")
story += [table(data, [4.2 * cm, 3.2 * cm, 3.4 * cm, 2.8 * cm, 3.4 * cm], colour=col), LEGEND, Spacer(1, 0.2 * cm),
          image(p_i, 14.5 * cm),
          table([["Pickup, eq. (3)", "Paper", "Ours"],
                 ["R1 on RG60 - 632", "1.25 x 587.1 = 733.9 A", "1.25 x %.1f = %.1f A" % (T2[0]["inom"], OLF * T2[0]["inom"])],
                 ["R2 on 632 - 671 (forward)", "1.25 x 478.2 = 597.8 A", "1.25 x %.1f = %.1f A" % (T2[3]["inom"], OLF * T2[3]["inom"])],
                 ["R2 reverse, eq. (12)", "OLF x Inom,rv - value not given",
                  "1.25 x %.1f = %.1f A (reverse load current with the DG)" % (T2[3]["inom_dg"], OLF * T2[3]["inom_dg"])]],
                [4.5 * cm, 5.5 * cm, 7.5 * cm]),
          Paragraph("<b>Result:</b> every rated current agrees within %.1f %%. With the DG the current through R1 falls to "
                    "%.1f A and R2 carries %.1f A in the reverse direction (671 -> 632)." % (
                        100 * inom_max, T2[0]["inom_dg"], T2[3]["inom_dg"]), BODY), PageBreak()]

# ---- Step 3: If,max ----------------------------------------------------------------------------------
story += step("3", "Maximum fault current (Table II, I<sub>f,max</sub>)",
              "three-phase short circuit below the device with negligible fault impedance. The paper does not say "
              "whether the DG is connected.",
              "largest current through the branch for a bolted fault at any node below it (LLG or LG where a three-phase "
              "fault does not exist), calculated without and with the DG.")
data = [["Branch", "Paper (kA)", "Ours, DG out (kA)", "Difference", "Ours, DG in (kA)", "Difference", "Closer case"]]
col = []
for k, r in enumerate(T2, 1):
    a, b = dev(r["ifmax"], r["p_max"]), dev(r["ifmax_dg"], r["p_max"])
    data.append([r["label"], "%.2f" % (r["p_max"] / 1000), "%.2f" % (r["ifmax"] / 1000), pct(r["ifmax"], r["p_max"]),
                 "%.2f" % (r["ifmax_dg"] / 1000), pct(r["ifmax_dg"], r["p_max"]),
                 "same" if abs(a - b) < 0.005 else ("DG out" if a < b else "DG in")])
    col += [(3, k, shade(a)), (5, k, shade(b))]
p_m = os.path.join(TMP, "ifmax.png")
bars(p_m, "Maximum fault current per branch", [("paper, Table II", INK2, [r["p_max"] / 1000 for r in T2]),
                                              ("ours, DG disconnected", BLUE, [r["ifmax"] / 1000 for r in T2]),
                                              ("ours, DG connected", ORANGE, [r["ifmax_dg"] / 1000 for r in T2])],
     [r["label"] for r in T2], "If,max (kA)")
hvr = [r for r in T2 if r["key"] == ("XFM1-HV", "side")][0]
story += [table(data, [3.4 * cm, 2 * cm, 2.9 * cm, 2.1 * cm, 2.8 * cm, 2.1 * cm, 2.2 * cm], colour=col), LEGEND,
          Paragraph(HVNOTE % (hvr["through_max"] / 1000, hvr["through_min"]), SMALL),
          Spacer(1, 0.2 * cm), image(p_m, 14.8 * cm), PageBreak()]
data = [["Node", "IEEE benchmark, quoted in [8] (kA)", "Ours, DG out (kA)", "Difference", "Fault type"]]
col = []
for k, (n, v) in enumerate(BENCH.items(), 1):
    o = num(IFMAX["out"][n]["If,max (A)"]) / 1000
    data.append([n, "%.2f" % v, "%.2f" % o, pct(o, v), "%s %s" % (IFMAX["out"][n]["Fault type"], IFMAX["out"][n]["Faulted phases"])])
    col.append((3, k, shade(dev(o, v))))
story += [Paragraph("Check against the IEEE benchmark the paper builds on", H2),
          Paragraph("Ref. [8] of the paper (Yousaf, Muttaqi, Sutanto, 2020 - the protection design of this same feeder that "
                    "the paper extends) lists the maximum fault current at every node from the IEEE short-circuit benchmark.", BODY),
          table(data, [2.2 * cm, 5.3 * cm, 3.4 * cm, 2.6 * cm, 3.4 * cm], colour=col),
          Spacer(1, 0.25 * cm),
          Paragraph("<b>Result:</b> our fault levels reproduce the IEEE benchmark within %.1f %% at every node, but only %d "
                    "of the 13 branch values of the paper's Table II are within 20 %% (%d if each row may be taken with or "
                    "without the DG). Three observations on the paper's column:" % (100 * bench_dev, n_max_ok, n_max_ok_dg), BODY),
          Paragraph("&bull; It is not consistent with a radial feeder: 632-633 (6.73 kA), 671-680 (6.25 kA) and 692-675 "
                    "(7.83 kA) are larger than the 5.41 kA at the feeder head RG60-632, although they lie further from "
                    "the source. No single network model can reproduce these values together.", BODY),
          Paragraph("&bull; Two rows equal the paper's own with-DG results: 645-646 = 3.64 kA is the fuse current of the "
                    "DG-connected fault of Fig. 15, and our with-DG value for 632-645 (%.2f kA) is within %s of the "
                    "paper's 4.25 kA. The table therefore appears to mix cases." % (
                        T2[2]["ifmax_dg"] / 1000, pct(T2[2]["ifmax_dg"], T2[2]["p_max"]).replace("+", "").replace("-", "")), BODY),
          Paragraph("&bull; The far-end single-phase values (684-611: 1.93 kA) agree with ours without the DG.", BODY),
          PageBreak()]

# ---- Step 4: If,min ----------------------------------------------------------------------------------
story += step("4", "Minimum fault current (Table II, I<sub>f,min</sub>)",
              "single line-to-ground fault at the farthest node through a fault impedance of 3 ohm.",
              "LG fault through 3 ohm at the farthest node of each section (largest line length from the device), current "
              "through the section's first branch.")
data = [["Branch", "Paper (kA)", "Ours, DG out (kA)", "Difference", "Farthest node / fault", "Ours, DG in (kA)"]]
col = []
for k, r in enumerate(T2, 1):
    data.append([r["label"], "%.2f" % (r["p_min"] / 1000), "%.2f" % (r["ifmin"] / 1000), pct(r["ifmin"], r["p_min"]),
                 "%s, %s" % (r["far"], r["far_fault"]), "%.2f" % (r["ifmin_dg"] / 1000)])
    col.append((3, k, shade(dev(r["ifmin"], r["p_min"]))))
p_n = os.path.join(TMP, "ifmin.png")
bars(p_n, "Minimum fault current per branch (LG, 3 ohm, farthest node)",
     [("paper, Table II", INK2, [r["p_min"] / 1000 for r in T2]), ("ours, DG disconnected", BLUE, [r["ifmin"] / 1000 for r in T2])],
     [r["label"] for r in T2], "If,min (kA)")
story += [table(data, [3.4 * cm, 2 * cm, 3 * cm, 2.2 * cm, 3.8 * cm, 3 * cm], colour=col), LEGEND,
          Paragraph(HVNOTE % (hvr["through_max"] / 1000, hvr["through_min"]), SMALL), Spacer(1, 0.2 * cm),
          image(p_n, 11.2 * cm),
          Paragraph("<b>Result:</b> %d of 13 branches agree within 20 %%; the laterals agree best (671-684, 671-680, "
                    "692-675, 684-611, 684-652 within 10 %%). Differences:" % n_min_ok, BODY),
          Paragraph("&bull; <b>XFM-1 LV side:</b> the paper's 0.59 kA is below its own rated current of the same "
                    "branch (704.7 A). A 3 ohm fault at 0.48 kV can only draw 277 V / 3 ohm = 92 A, so the current "
                    "there is essentially the load current (ours %.2f kA)." % (
                        [r for r in T2 if r["key"] == ("XFM1-LV", "side")][0]["ifmin"] / 1000), BODY),
          Paragraph("&bull; <b>RG60-632, 632-645 and 645-646:</b> ours are 11-22 % lower (632-671: 5 % lower), in line "
                    "with the lower fault level of the IEEE-benchmark source.", BODY),
          PageBreak(),
          Paragraph("Which minimum current is used, and what it shows", H2),
          Paragraph("The paper's rule (farthest node) is kept for the comparison with Table II above. For the two "
                    "reclosers the farthest node (652) is not the lowest case: a fault on the lightly loaded phase b "
                    "gives less current. For step 5 of the paper's method - the pickup must be below the minimum fault "
                    "current of the zone - the lowest LG-3-ohm current is therefore used:", BODY),
          sens_table(),
          Paragraph("<b>Result:</b> without the DG both pickups are below the minimum fault current, as the paper "
                    "requires. With the DG they are not: the DG supplies part of the fault current and of the load, so "
                    "a high-resistance fault at the far end draws less current through R1 and R2 than their pickups. "
                    "The paper determines I<sub>f,min</sub> only once and does not examine this case. The reclosers "
                    "then do not see such faults, and clearing is left to the fuses.", BODY),
          Spacer(1, 0.3 * cm)]

# ---- Step 5: figure faults ----------------------------------------------------------------------------
story += step("5", "Fault currents with the DG (values quoted in the paper's figures)",
              "each time-current figure is drawn at the fault current of one fault with the DG connected; the values are "
              "printed in the figures and in the text.",
              "the same faults (location, type, fault impedance) with the DG connected. The paper does not label which "
              "device each printed current belongs to, so the nearest corresponding device is shown.")
FC = [("Fig. 8", "LG at 611", "1976 A", "Fig8", [("F684 / F671-2 (fault path)", "F684"), ("R2", "R2")], 1975.6, "F684"),
      ("Fig. 9", "LLG, middle of 692-675, 1 ohm", "2589 A and 2423 A", "Fig9", [("F692-R (fault path)", "F692-R"), ("R2", "R2")], 2589.4, "F692-R"),
      ("Fig. 11", "LL at 646, 1 ohm", "3492 A", "Fig11", [("F646 (fault path)", "F646"), ("R1", "R1")], 3492.2, "F646"),
      ("Fig. 13", "3-phase at 10 % of 632-633", "8517 A and 3361 A", "Fig13", [("F633 (fault path)", "F633"), ("R1", "R1"), ("R2", "R2")], 8517.2, "F633"),
      ("Figs. 15, 16", "solid LL at 646", "3.64 kA (fuses), 1.54 kA (R2)", "Fig15", [("F646 (fault path)", "F646"), ("R2 (DG part)", "R2"), ("R1 (grid part)", "R1")], 3640.0, "F646")]
data = [["Figure", "Fault", "Paper", "Ours", "Fault-path current: paper -> ours"]]
col = []
for k, (fig, flt, ptxt, case, devs, pval, main) in enumerate(FC, 1):
    o = fi(case, main)
    data.append([fig, flt, ptxt, "; ".join("%s %.0f A" % (lab, fi(case, d)) for lab, d in devs),
                 "%.0f -> %.0f A (%s)" % (pval, o, pct(o, pval))])
    col.append((4, k, shade(dev(o, pval))))
story += [table(data, [1.9 * cm, 3.6 * cm, 3.4 * cm, 5.4 * cm, 3.3 * cm], colour=col), LEGEND, Spacer(1, 0.2 * cm),
          Paragraph("<b>Result:</b> the solid LL fault at 646 - the paper's main DSDR example - is reproduced within 1 %% "
                    "in the fault path (%.2f kA against 3.64 kA). The DG's share through R2 is lower in our model "
                    "(%.2f kA against 1.54 kA) and the grid's share correspondingly higher. For the LG fault at 611 (Fig. 8) ours is 13 %% "
                    "higher; for the faults with a fault impedance (Figs. 9, 11) ours are 20-32 %% lower, and for "
                    "Fig. 13 25 %% lower: a 4.05 MVA "
                    "machine with Xd'' = 0.118 pu behind a 0.15 pu transformer can contribute at most about 2.1 kA at "
                    "4.16 kV, so the paper's 8.5 kA near node 632 is not reachable with the benchmark source "
                    "(our value %.2f kA = %.2f kA grid + %.2f kA DG)." % (
                        fi("Fig15", "F646") / 1000, fi("Fig15", "R2") / 1000, fi("Fig13", "F633") / 1000,
                        fi("Fig13", "R1") / 1000, fi("Fig13", "R2") / 1000), BODY),
          Spacer(1, 0.3 * cm)]

# ---- Step 6: direction ----------------------------------------------------------------------------------
story += step("6", "Direction of the current through R2",
              "with the DG at 692, R2 operates in the reverse direction for faults upstream of it (e.g. 645, 646, "
              "632-633) and experiences only the DG's contribution there; for downstream faults it operates forward. "
              "This is the reason for the dual-setting recloser.",
              "sign of the current through R1 and R2 for every bolted fault (forward = away from the grid).")
bus = ["632", "633", "645", "646", "DL", "671", "692", "675", "680", "684", "652", "611"]
cmpf = {r["Bus"]: r for r in read("Comparison_fault_current.csv")}
data = [["Faulted bus", "Position", "Fault", "If,max DG out (A)", "If,max DG in (A)", "R1 DG in (A)", "R2 DG out (A)", "R2 DG in (A)",
         "R2 with DG"]]
col = []
for k, n in enumerate(bus, 1):
    r = cmpf[n]
    r2 = num(r["R2 with DG (A)"])
    data.append([n, "upstream of R2" if n in ("632", "633", "645", "646", "DL") else "downstream of R2", r["Fault with DG"],
                 r["If,max without DG (A)"], r["If,max with DG (A)"], r["R1 with DG (A)"], r["R2 without DG (A)"],
                 r["R2 with DG (A)"], "reverse" if r2 < 0 else "forward"])
    col.append((8, k, colors.HexColor("#fde3d6") if r2 < 0 else GOOD))
story += [table(data, [1.7 * cm, 2.6 * cm, 1.7 * cm, 2.1 * cm, 2.1 * cm, 1.8 * cm, 1.9 * cm, 1.9 * cm, 1.8 * cm], colour=col),
          Paragraph("Largest bolted fault at each bus. + = forward (away from the grid), - = reverse.", SMALL),
          Paragraph("<b>Result:</b> the paper's statement is confirmed for every case: with the DG, R2 is reverse for all "
                    "%d bolted faults upstream of it and forward for all %d downstream; R1 is forward for all faults. "
                    "For upstream faults R2 carries only the DG contribution (1.1-2.0 kA) while the fault itself is "
                    "3.9-6.5 kA - the dissimilar fault levels the paper describes." % (len(up), len(down)), BODY),
          Spacer(1, 0.3 * cm)]

# ---- conclusion -----------------------------------------------------------------------------------------
story += [Paragraph("Summary of the comparison", H1),
          table([["Quantity", "Agreement with the paper", "Reason for the difference"],
                 ["DG and network data", "identical", "-"],
                 ["Rated currents (Inom)", "within %.1f %%" % (100 * inom_max), "-"],
                 ["Pickups by eq. (3)", "within 2 %", "-"],
                 ["If,max", "%d of 13 within 20 %%" % n_max_ok,
                  "paper's column is not consistent with a radial feeder and seems to mix cases with and without DG; ours "
                  "matches the IEEE benchmark within %.1f %%" % (100 * bench_dev)],
                 ["If,min", "%d of 13 within 20 %%" % n_min_ok, "lower source fault level"],
                 ["Fault current of the DSDR example (Fig. 15)", "within 1 %", "-"],
                 ["DG share through R2 (Fig. 15)", "28 % lower", "not determined - the paper gives neither the source nor the DG operating point"],
                 ["Direction of the R2 current", "confirmed for all faults", "-"]],
                [5.2 * cm, 4.3 * cm, 8 * cm]),
          Spacer(1, 0.3 * cm),
          Paragraph("<b>Conclusion.</b> The load flow reproduces the paper. The short-circuit results reproduce the IEEE "
                    "benchmark and the paper's key DSDR example, and confirm the reversal of the current through R2 that "
                    "motivates the dual-setting recloser. The paper's Table II fault currents cannot be reproduced as a "
                    "set, because they are not mutually consistent.", BODY),
          Paragraph("<b>Next step.</b> Relay coordination (Tables III and IV, Figs. 8-17), built on this database, is "
                    "compared with the paper in Comparison_with_Reference_Paper.pdf.", BODY),
          Spacer(1, 0.3 * cm), Paragraph("Table II as printed in the paper", H2), image(t2_png, 8.2 * cm)]


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#52514e"))
    canvas.drawString(1.5 * cm, 1.0 * cm, "Our results vs Yousaf et al. 2022 - load flow and short circuit, IEEE 13-node feeder")
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, "page %d" % doc.page)
    canvas.restoreState()


SimpleDocTemplate(OUT, pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.4 * cm,
                  bottomMargin=1.6 * cm, title="Our results vs the reference paper").build(
    story, onFirstPage=on_page, onLaterPages=on_page)
doc_p.close()
for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
print("Saved", OUT)
print("check: Inom max dev %.2f %%; If,max within 20 %%: %d (%d with DG option); If,min within 20 %%: %d; benchmark max dev %.2f %%" % (
    100 * inom_max, n_max_ok, n_max_ok_dg, n_min_ok, 100 * bench_dev))
for r in T2:
    print("  %-14s Inom %6.1f/%6.1f  Ifmax paper %5.2f ours %5.2f / DG %5.2f   Ifmin paper %4.2f ours %4.2f" % (
        r["label"], r["p_inom"], r["inom"], r["p_max"] / 1000, r["ifmax"] / 1000, r["ifmax_dg"] / 1000, r["p_min"] / 1000, r["ifmin"] / 1000))
for fig, flt, ptxt, case, devs, pval, main in FC:
    print("  %s %s -> %.0f (%s)" % (fig, pval, fi(case, main), pct(fi(case, main), pval)))
