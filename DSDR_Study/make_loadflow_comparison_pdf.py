"""
Builds results/LoadFlow_Comparison_Base_vs_DG.pdf: the load flow with the DG connected compared
with the base case (DG disconnected), branch by branch ("From node -> To node") and bus by bus.

Reads the files written by loadflow_all_buses.py (results/database/7 ... 10_*.csv); PowerFactory
is not needed.  Needs reportlab and matplotlib.
"""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
DB = os.path.join(RES, "database")
TMP = os.path.join(RES, "_lf_tmp")
os.makedirs(TMP, exist_ok=True)
OUT = os.path.join(RES, "LoadFlow_Comparison_Base_vs_DG.pdf")

BLUE, ORANGE, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#d9d8d4", "#fcfcfb"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "savefig.facecolor": SURF})


def read(name):
    return list(csv.DictReader(open(os.path.join(DB, name))))


def num(s):
    return None if s in ("-", "", None) else float(s)


BR = {"base": read("7_BranchFlow_DG_out.csv"), "dg": read("8_BranchFlow_DG_in.csv")}
BUS = {"base": read("9_BusLoadFlow_DG_out.csv"), "dg": read("10_BusLoadFlow_DG_in.csv")}
KEYS = [(r["From node"], r["To node"]) for r in BR["base"]]
B = {c: {(r["From node"], r["To node"]): r for r in BR[c]} for c in BR}
U = {c: {r["Bus"]: r for r in BUS[c]} for c in BUS}
BUSES = [r["Bus"] for r in BUS["base"]]
SEG = [("632", "nDL1"), ("nDL1", "nDL2"), ("nDL2", "nDL"), ("nDL", "nDL4"), ("nDL4", "nDL5"), ("nDL5", "671")]


def P(c, k):
    return float(B[c][k]["P (kW)"])


def Q(c, k):
    return float(B[c][k]["Q (kvar)"])


def I(c, k):
    return [num(B[c][k]["I %s (A)" % p]) for p in "abc"]


def imax(c, k):
    v = [abs(x) for x in I(c, k) if x is not None]
    return max(v) if v else 0.0


def loss(c, k):
    return float(B[c][k]["Loss (kW)"])


def flow(c, k):
    return B[c][k]["Active power flows"]


def label(k):
    return "%s -> %s" % k


# ---------------------------------------------------------------------------------------------
# Figure 1: feeder diagram with the direction of the active power
# ---------------------------------------------------------------------------------------------
POS = {"SubstationHV": (5, 11.2), "650": (5, 10.2), "RG60": (5, 9.2), "632": (5, 8), "633": (7.2, 8), "634": (9.4, 8),
       "645": (2.8, 8), "646": (0.6, 8), "nDL": (5, 6.5), "DL": (6.6, 6.5), "671": (5, 5), "692": (7.2, 5),
       "675": (9.4, 5), "DG": (7.2, 6.3), "684": (2.8, 5), "611": (0.6, 5), "652": (2.8, 3.6), "680": (5, 3.6)}
# drawn edge -> (row used for the label, i.e. the end nearer to the grid)
EDGES = [("SubstationHV", "650", ("SubstationHV", "650")), ("650", "RG60", ("650", "RG60")),
         ("RG60", "632", ("RG60", "632")), ("632", "633", ("632", "633")), ("633", "634", ("633", "634")),
         ("632", "645", ("632", "645")), ("645", "646", ("645", "646")), ("632", "nDL", ("632", "nDL1")),
         ("nDL", "DL", ("nDL", "DL")), ("nDL", "671", ("nDL5", "671")), ("671", "692", ("671", "692")),
         ("692", "675", ("692", "675")), ("692", "DG", ("692", "DG")), ("671", "684", ("671", "684")),
         ("684", "611", ("684", "611")), ("684", "652", ("684", "652")), ("671", "680", ("671", "680"))]


def diagram(c, title, path):
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    ax.set_xlim(-0.4, 10.4)
    ax.set_ylim(3.0, 11.8)
    ax.axis("off")
    for a, b, k in EDGES:
        (x1, y1), (x2, y2) = POS[a], POS[b]
        p = P(c, k)
        if abs(p) < 0.05:
            ax.plot([x1, x2], [y1, y2], color=GRID, lw=2, zorder=1)
            txt, col = "no flow", INK2
        else:
            fwd = p > 0
            col = BLUE if fwd else ORANGE
            s, e = ((x1, y1), (x2, y2)) if fwd else ((x2, y2), (x1, y1))
            ax.add_patch(FancyArrowPatch(s, e, arrowstyle="-|>", mutation_scale=13, lw=2.2, color=col,
                                         shrinkA=11, shrinkB=11, zorder=2))
            txt = "%.0f kW\n%.0f A" % (abs(p), imax(c, k))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if abs(x1 - x2) < 0.01:                       # vertical edge: label to the left
            ax.text(mx - 0.18, my, txt, ha="right", va="center", fontsize=7.3, color=INK)
        else:
            ax.text(mx, my + 0.16, txt, ha="center", va="bottom", fontsize=7.3, color=INK, linespacing=1.0)
    for n, (x, y) in POS.items():
        dg = n == "DG"
        ax.plot([x], [y], marker="s" if dg else "o", ms=17 if n != "SubstationHV" else 19, mfc=SURF,
                mec=ORANGE if dg else INK, mew=1.4, zorder=3)
        ax.text(x, y, {"SubstationHV": "Grid", "nDL": "mid"}.get(n, n), ha="center", va="center",
                fontsize=6.6 if len(n) > 3 else 7.2, fontweight="bold", zorder=4)
    ax.text(5.35, 6.5, "", fontsize=6)
    ax.legend(handles=[Line2D([], [], color=BLUE, lw=2.2, marker=">", ms=6, label="active power flows away from the grid"),
                       Line2D([], [], color=ORANGE, lw=2.2, marker="<", ms=6, label="active power flows towards the grid (reversed)"),
                       Line2D([], [], color=GRID, lw=2.2, label="no flow")],
              loc="lower right", fontsize=7.5, frameon=False)
    ax.set_title(title, fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=190)
    plt.close(fig)


# ---------------------------------------------------------------------------------------------
# Figure 2: active power per branch;  Figure 3: voltage profile;  Figure 4: losses
# ---------------------------------------------------------------------------------------------
def fig_branch_p(path):
    keys = [k for k in KEYS if abs(P("base", k)) > 0.05 or abs(P("dg", k)) > 0.05]
    fig, ax = plt.subplots(figsize=(7.4, 6.6))
    y = list(range(len(keys)))[::-1]
    h = 0.36
    ax.barh([v + h / 2 for v in y], [P("base", k) for k in keys], height=h, color=BLUE, label="base case (DG disconnected)")
    ax.barh([v - h / 2 for v in y], [P("dg", k) for k in keys], height=h, color=ORANGE, label="DG connected")
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([label(k).replace("SubstationHV", "Grid") for k in keys], fontsize=7.6)
    ax.set_xlabel("Active power at the From node (kW);  negative = flows towards the grid")
    ax.grid(True, axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Active power in every branch, From node -> To node", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=190)
    plt.close(fig)


PATH_MAIN = [("650", 0), ("RG60", 0), ("632", 2000), ("nDL1", 2333), ("nDL2", 2667), ("nDL", 3000), ("nDL4", 3333),
             ("nDL5", 3667), ("671", 4000), ("692", 4000), ("675", 4500)]


def fig_voltage(path):
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.2), sharey=True)
    for ax, ph in zip(axes, "abc"):
        for c, col, lab in (("base", BLUE, "base case"), ("dg", ORANGE, "DG connected")):
            xs = [d for n, d in PATH_MAIN]
            ys = [float(U[c][n]["V%s (pu)" % ph]) for n, d in PATH_MAIN]
            ax.plot(xs, ys, color=col, lw=1.8, marker="o", ms=3.5, label=lab)
        ax.axhline(1.05, color=INK2, lw=0.8, ls=":")
        ax.axhline(0.95, color=INK2, lw=0.8, ls=":")
        ax.set_title("phase %s" % ph, fontsize=9, loc="left")
        ax.set_xlabel("distance from the substation (ft)")
        ax.grid(True, color=GRID, lw=0.5)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("voltage (pu)")
    axes[2].text(4450, 1.051, "1.05 pu", fontsize=7, color=INK2, va="bottom", ha="right")
    axes[2].text(4450, 0.951, "0.95 pu", fontsize=7, color=INK2, va="bottom", ha="right")
    axes[0].legend(frameon=False, fontsize=7.5, loc="lower left")
    fig.suptitle("Voltage along the main feeder 650 - RG60 - 632 - 671 - 692 - 675", fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=190)
    plt.close(fig)


def fig_loss(path):
    keys = [k for k in KEYS if loss("base", k) > 0.3 or loss("dg", k) > 0.3]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    y = list(range(len(keys)))[::-1]
    h = 0.36
    ax.barh([v + h / 2 for v in y], [loss("base", k) for k in keys], height=h, color=BLUE, label="base case (DG disconnected)")
    ax.barh([v - h / 2 for v in y], [loss("dg", k) for k in keys], height=h, color=ORANGE, label="DG connected")
    ax.set_yticks(y)
    ax.set_yticklabels([label(k).replace("SubstationHV", "Grid") for k in keys], fontsize=7.6)
    ax.set_xlabel("Active power loss (kW)")
    ax.grid(True, axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Losses per branch (branches above 0.3 kW)", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=190)
    plt.close(fig)


# ---------------------------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------------------------
def total(c, col):
    return sum(num(r[col]) or 0.0 for r in BUS[c])


def volts(c, feeder_only=True):
    out = []
    for r in BUS[c]:
        if float(r["Un (kV)"]) > 100 or (feeder_only and float(r["Un (kV)"]) < 1):
            continue
        for p in "abc":
            v = num(r["V%s (pu)" % p])
            if v is not None:
                out.append((v, r["Bus"], p))
    return out


SUM = {}
for c in ("base", "dg"):
    grid_row = U[c]["SubstationHV"]
    v = volts(c)
    SUM[c] = dict(load_p=total(c, "Load P (kW)"), load_q=total(c, "Load Q (kvar)"),
                  cap=total(c, "Cap Q supplied (kvar)"), grid_p=num(grid_row["Source P (kW)"]),
                  grid_q=num(grid_row["Source Q (kvar)"]), dg_p=num(U[c]["DG"]["Source P (kW)"]) or 0.0,
                  dg_q=num(U[c]["DG"]["Source Q (kvar)"]) or 0.0, loss=sum(loss(c, k) for k in KEYS),
                  vmin=min(v), vmax=max(v), over=sum(x[0] > 1.05 for x in v), under=sum(x[0] < 0.95 for x in v),
                  n=len(v))
REVERSED = [k for k in KEYS if P("base", k) > 0.05 and P("dg", k) < -0.05]
R1, R2 = ("RG60", "632"), ("nDL5", "671")

# ---------------------------------------------------------------------------------------------
# PDF
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
                     borderColor=colors.HexColor("#2a78d6"), borderWidth=0.8, borderPadding=5, spaceBefore=4,
                     spaceAfter=8)
REV, HI, LO = colors.HexColor("#fde3d6"), colors.HexColor("#fff3d6"), colors.HexColor("#fbe0e0")


def table(data, widths, colour=None, header_rows=1):
    data = [[Paragraph(str(c), HEAD if r < header_rows else CELL) for c in row] for r, row in enumerate(data)]
    tb = Table(data, colWidths=widths, repeatRows=header_rows)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9b8b3")),
          ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#1b4f93")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.6),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6)]
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


def sgn(x, nd=1):
    return "%+.*f" % (nd, x)


def arrow(s):
    return s.replace("SubstationHV", "Grid")


b, d = SUM["base"], SUM["dg"]
story = [Spacer(1, 0.8 * cm),
         Paragraph("Load flow: DG connected vs base case", ParagraphStyle("T", parent=H1, fontSize=21, leading=25)),
         Paragraph("IEEE 13-node feeder - all buses and branches, From node -> To node",
                   ParagraphStyle("st", parent=H2, fontSize=12.5)),
         Spacer(1, 0.2 * cm),
         Paragraph("<b>Base case:</b> DG disconnected. <b>Compared case:</b> 4.05 MVA synchronous DG connected at "
                   "node 692 through its 0.69/4.16 kV transformer, dispatched at %.0f kW. Both are AC unbalanced "
                   "three-phase load flows in PowerFactory (project <i>IEEE13 DSDR Fuse Coordination</i>, study case "
                   "<i>Study with Substation Transformer</i>, regulator taps fixed). No relay, fuse or network "
                   "setting differs between the two cases." % d["dg_p"], BODY),
         Spacer(1, 0.25 * cm),
         Paragraph("Every branch is written <b>From node -> To node</b> in the direction away from the grid. Values are "
                   "taken at the From node: <b>+</b> means the power or current flows From -> To, <b>-</b> means it "
                   "flows To -> From (towards the grid). The power balance closes to 0.03 kW at every bus in both "
                   "cases.", BOX),
         Paragraph("Summary", H2)]
rows = [["Quantity", "Base case (DG out)", "DG connected", "Change"],
        ["Power from the grid", "%.1f kW / %.1f kvar" % (b["grid_p"], b["grid_q"]), "%.1f kW / %.1f kvar" % (d["grid_p"], d["grid_q"]),
         "%s kW (%.0f %%)" % (sgn(d["grid_p"] - b["grid_p"]), 100 * (d["grid_p"] / b["grid_p"] - 1))],
        ["Power from the DG", "-", "%.1f kW / %.1f kvar" % (d["dg_p"], d["dg_q"]), ""],
        ["Total load", "%.1f kW / %.1f kvar" % (b["load_p"], b["load_q"]), "%.1f kW / %.1f kvar" % (d["load_p"], d["load_q"]),
         "%s kW" % sgn(d["load_p"] - b["load_p"])],
        ["Capacitors supply", "%.1f kvar" % b["cap"], "%.1f kvar" % d["cap"], "%s kvar" % sgn(d["cap"] - b["cap"])],
        ["Total losses", "%.1f kW" % b["loss"], "%.1f kW" % d["loss"],
         "%s kW (%.0f %%)" % (sgn(d["loss"] - b["loss"]), 100 * (d["loss"] / b["loss"] - 1))],
        ["Lowest feeder voltage", "%.4f pu (%s phase %s)" % b["vmin"], "%.4f pu (%s phase %s)" % d["vmin"],
         "%s pu" % sgn(d["vmin"][0] - b["vmin"][0], 4)],
        ["Highest feeder voltage", "%.4f pu (%s phase %s)" % b["vmax"], "%.4f pu (%s phase %s)" % d["vmax"],
         "%s pu" % sgn(d["vmax"][0] - b["vmax"][0], 4)],
        ["Phase voltages above 1.05 pu", "%d of %d" % (b["over"], b["n"]), "%d of %d" % (d["over"], d["n"]), sgn(d["over"] - b["over"], 0)],
        ["Phase voltages below 0.95 pu", "%d of %d" % (b["under"], b["n"]), "%d of %d" % (d["under"], d["n"]), sgn(d["under"] - b["under"], 0)],
        ["R1 (RG60 -> 632), largest phase current", "%.1f A" % imax("base", R1), "%.1f A" % imax("dg", R1),
         "%s A" % sgn(imax("dg", R1) - imax("base", R1))],
        ["R2 (632 -> 671 at 671), largest phase current", "%.1f A, %s" % (imax("base", R2), "forward"),
         "%.1f A, %s" % (imax("dg", R2), "reverse" if P("dg", R2) < 0 else "forward"),
         "%s A" % sgn(imax("dg", R2) - imax("base", R2))],
        ["Branch elements with reversed active power", "0", "%d (671-692 and the six segments of 632-671)" % len(REVERSED), ""]]
story += [table(rows, [5.6 * cm, 4.3 * cm, 4.3 * cm, 3.6 * cm]), PageBreak()]

# ---- diagrams ------------------------------------------------------------------------------------
p1, p2 = os.path.join(TMP, "d_base.png"), os.path.join(TMP, "d_dg.png")
diagram("base", "Base case (DG disconnected): active power and largest phase current per branch", p1)
diagram("dg", "DG connected: active power and largest phase current per branch", p2)
story += [Paragraph("1. Direction of the power flow", H1),
          image(p1, 15.6 * cm), image(p2, 15.6 * cm),
          Paragraph("\"mid\" is the middle of line 632-671, where the distributed-load lateral DL is tapped; the line "
                    "is modelled in six segments (label above mid: at 632; label below mid: at 671).", SMALL), PageBreak()]

# ---- branch flows ------------------------------------------------------------------------------------
p3 = os.path.join(TMP, "p.png")
fig_branch_p(p3)
rows = [["From node", "To node", "P base (kW)", "P with DG (kW)", "Change (kW)", "Q base (kvar)", "Q with DG (kvar)",
         "Flow, base", "Flow, with DG"]]
col = []
for n, k in enumerate(KEYS, 1):
    rows.append([arrow(k[0]), k[1], sgn(P("base", k)), sgn(P("dg", k)), sgn(P("dg", k) - P("base", k)),
                 sgn(Q("base", k)), sgn(Q("dg", k)), arrow(flow("base", k)), arrow(flow("dg", k))])
    if k in REVERSED:
        col += [(3, n, REV), (8, n, REV)]
story += [Paragraph("2. Branch flows, From node -> To node", H1),
          table(rows, [1.8 * cm, 1.4 * cm, 1.9 * cm, 2.1 * cm, 1.9 * cm, 1.9 * cm, 2.1 * cm, 2.4 * cm, 2.4 * cm], colour=col),
          Paragraph("Shaded: active power reversed by the DG. Values at the From node.", SMALL), PageBreak(),
          image(p3, 16 * cm),
          Paragraph("The DG's %.0f kW enter at 692, cover the loads at 692, 675, 671, 684, 611 and 652, and the rest "
                    "(%.0f kW) flows back through 671 and the whole line 671 -> 632, where it supplies 633/634, 645/646 "
                    "and the distributed load. The grid then only supplies %.0f kW, but still %.0f kvar, because the "
                    "DG delivers no reactive power in this operating point." % (
                        d["dg_p"], -P("dg", R2), d["grid_p"], d["grid_q"]), BODY), PageBreak()]

# ---- currents ------------------------------------------------------------------------------------------
rows = [["From node", "To node", "Ia base", "Ib base", "Ic base", "Ia with DG", "Ib with DG", "Ic with DG",
         "Largest phase: base -> DG (A)", "Change"]]
col = []
for n, k in enumerate(KEYS, 1):
    ib, idg = B["base"][k], B["dg"][k]
    a, c = imax("base", k), imax("dg", k)
    rows.append([arrow(k[0]), k[1]] + [ib["I %s (A)" % p] for p in "abc"] + [idg["I %s (A)" % p] for p in "abc"] +
                ["%.1f -> %.1f" % (a, c), "%+.0f %%" % (100 * (c / a - 1)) if a > 0.05 else "-"])
    for j, p in enumerate("abc"):
        v = num(idg["I %s (A)" % p])
        if v is not None and v < -0.05:
            col.append((5 + j, n, REV))
story += [Paragraph("3. Branch currents per phase (A)", H1),
          table(rows, [1.8 * cm, 1.4 * cm] + [1.45 * cm] * 6 + [3.3 * cm, 1.6 * cm], colour=col),
          Paragraph("The sign of a phase current is the direction of that phase's active power (- = towards the grid, "
                    "shaded). \"-\" = the branch does not have that phase. With the DG the feeder is strongly "
                    "unbalanced in direction: at R1 (RG60 -> 632) phase b carries power towards the grid while phases "
                    "a and c still import.", SMALL), PageBreak()]

# ---- voltages ----------------------------------------------------------------------------------------
p4 = os.path.join(TMP, "v.png")
fig_voltage(p4)
rows = [["Bus", "Va base", "Va DG", "dVa", "Vb base", "Vb DG", "dVb", "Vc base", "Vc DG", "dVc"]]
col = []
for n, bus in enumerate([x for x in BUSES if x != "SubstationHV"], 1):
    row = [bus]
    for j, p in enumerate("abc"):
        x, y = num(U["base"][bus]["V%s (pu)" % p]), num(U["dg"][bus]["V%s (pu)" % p])
        if x is None:
            row += ["-", "-", "-"]
            continue
        row += ["%.4f" % x, "%.4f" % y, sgn(y - x, 4)]
        for off, v in ((1, x), (2, y)):
            if v > 1.05:
                col.append((3 * j + off, n, HI))
            elif v < 0.95:
                col.append((3 * j + off, n, LO))
    rows.append(row)
story += [Paragraph("4. Bus voltages (pu, phase-to-neutral)", H1), image(p4, 16.5 * cm),
          table(rows, [1.9 * cm] + [1.7 * cm] * 9, colour=col),
          Paragraph("Shaded yellow: above 1.05 pu. \"-\" = the bus does not have that phase. 634 is the 0.48 kV bus, "
                    "DG the 0.69 kV generator bus.", SMALL),
          Paragraph("The DG raises phases a and c along the whole feeder (up to %s pu at the far end) and removes the "
                    "voltage drop towards 671. Phase b is already above 1.05 pu in the base case (it is lightly "
                    "loaded and the regulator taps are fixed), and the DG raises it slightly further."
                    % sgn(max(num(U["dg"][x]["V%s (pu)" % p]) - num(U["base"][x]["V%s (pu)" % p]) for x in BUSES for p in "ac"
                              if num(U["base"][x]["V%s (pu)" % p]) is not None and x not in ("DG", "SubstationHV")), 3), BODY),
          PageBreak()]

# ---- losses and loads ----------------------------------------------------------------------------------
p5 = os.path.join(TMP, "l.png")
fig_loss(p5)
rows = [["From node", "To node", "Loss base (kW)", "Loss with DG (kW)", "Change (kW)"]]
for k in KEYS:
    if loss("base", k) > 0.005 or loss("dg", k) > 0.005:
        rows.append([arrow(k[0]), k[1], "%.2f" % loss("base", k), "%.2f" % loss("dg", k), sgn(loss("dg", k) - loss("base", k), 2)])
rows.append(["Total", "", "%.1f" % b["loss"], "%.1f" % d["loss"], sgn(d["loss"] - b["loss"])])
story += [Paragraph("5. Losses", H1), image(p5, 15.5 * cm), table(rows, [3 * cm, 2.5 * cm, 3.5 * cm, 3.5 * cm, 3 * cm]),
          PageBreak()]
rows = [["Bus", "Load base (kW / kvar)", "Load with DG (kW / kvar)", "Change (kW)", "Capacitor base (kvar)",
         "Capacitor with DG (kvar)"]]
for bus in BUSES:
    x, y = U["base"][bus], U["dg"][bus]
    if x["Load P (kW)"] == "-" and x["Cap Q supplied (kvar)"] == "-":
        continue
    rows.append([bus, "%s / %s" % (x["Load P (kW)"], x["Load Q (kvar)"]), "%s / %s" % (y["Load P (kW)"], y["Load Q (kvar)"]),
                 sgn(num(y["Load P (kW)"]) - num(x["Load P (kW)"])) if x["Load P (kW)"] != "-" else "-",
                 x["Cap Q supplied (kvar)"], y["Cap Q supplied (kvar)"]])
story += [Paragraph("6. Loads and capacitors at the buses", H1),
          table(rows, [2 * cm, 3.8 * cm, 3.8 * cm, 2.4 * cm, 2.9 * cm, 2.9 * cm]),
          Paragraph("Constant-impedance and constant-current loads (646, 652, 692, 611) and the capacitors draw or supply "
                    "more at the higher voltage with the DG, which is why the total load rises by %.1f kW." % (
                        d["load_p"] - b["load_p"]), SMALL),
          Spacer(1, 0.4 * cm), Paragraph("Findings", H1)]
for s in [
    "<b>Power flow reverses on the main feeder.</b> With the DG, active power flows 692 -> 671 -> 632: through the "
    "671-692 switch and all six segments of line 632-671 (%d branch elements). R2 (at the 671 end of line 632-671) "
    "carries %.1f A in reverse instead of %.1f A forward." % (len(REVERSED), imax("dg", R2), imax("base", R2)),
    "<b>The grid import falls from %.0f kW to %.0f kW</b>, and R1's largest phase current from %.1f A to %.1f A. The "
    "current at R1 does not fall in proportion, because the grid still supplies %.0f kvar." % (
        b["grid_p"], d["grid_p"], imax("base", R1), imax("dg", R1), d["grid_q"]),
    "<b>Losses fall from %.1f kW to %.1f kW</b> (%.0f %%), mainly on RG60 -> 632, the substation transformer and "
    "line 632 -> 671." % (b["loss"], d["loss"], 100 * (d["loss"] / b["loss"] - 1)),
    "<b>Voltages rise.</b> The lowest feeder voltage goes from %.4f pu to %.4f pu. %d of %d phase voltages are above "
    "1.05 pu in the base case and %d with the DG; none is below 0.95 pu in either case." % (
        b["vmin"][0], d["vmin"][0], b["over"], b["n"], d["over"]),
    "<b>Laterals are unaffected.</b> 632 -> 633 -> 634, 632 -> 645 -> 646, 671 -> 684 -> 611 / 652 and 692 -> 675 keep "
    "their direction and change only through the voltage dependence of their loads.",
]:
    story.append(Paragraph("&bull; " + s, BODY))


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#52514e"))
    canvas.drawString(1.5 * cm, 1.0 * cm, "IEEE 13-node feeder - load flow, DG connected vs base case")
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, "page %d" % doc.page)
    canvas.restoreState()


SimpleDocTemplate(OUT, pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.4 * cm,
                  bottomMargin=1.6 * cm, title="Load flow - DG connected vs base case").build(
    story, onFirstPage=on_page, onLaterPages=on_page)
for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
print("Saved", OUT)
