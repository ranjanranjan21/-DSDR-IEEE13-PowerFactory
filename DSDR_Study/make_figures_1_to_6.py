"""
Figs. 1 to 6 of the paper, redrawn from the replication's own devices and results (the paper's
versions are schematic).  PowerFactory is not needed.

  Fig. 1  conventional recloser-fuse coordination: recloser fast / delayed, fuse MMT / TCT and the
          coordination range between I_F,min (point A) and I_F,max (point B)          - R1 and F646
  Fig. 2  a typical distribution network with reclosers, fuses and a DG (concept sketch)
  Fig. 3  the proposed characteristics of the dual-setting recloser: reverse and forward settings of R2
  Fig. 4  series fuse coordination for a single line-to-ground fault                  - F652 and F671-2
  Fig. 5  the method (flow chart) as implemented in the scripts
  Fig. 6  the IEEE 13-node feeder with the protective devices

Outputs: results/figures/Fig01 ... Fig06 *.png
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

import step3_design_and_evaluate as m
from curves import INF, _loglog

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "results", "figures")
os.makedirs(FIG, exist_ok=True)
SET = json.load(open(os.path.join(HERE, "results", "settings.json")))
CONV, DS = SET["conventional"], SET["dsdr"]
BLUE, ORANGE, AQUA, VIOLET, RED = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7", "#d03b3b"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#d9d8d4", "#fcfcfb"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "savefig.facecolor": SURF})
II = [10 ** (2 + k / 250.0) for k in range(576)]            # 100 A ... 20 kA


def save(fig, name):
    path = os.path.join(FIG, name)
    try:
        fig.savefig(path, dpi=160)
    except OSError:                                          # open in a viewer
        path = path[:-4] + "_new.png"
        fig.savefig(path, dpi=160)
    plt.close(fig)
    print("  " + os.path.basename(path))


def cross(f1, f2, lo=200.0, hi=20000.0):
    """currents at which two time curves intersect"""
    out, xs = [], [lo * (hi / lo) ** (k / 6000.0) for k in range(6001)]
    for a, b in zip(xs, xs[1:]):
        ya, yb = f1(a) - f2(a), f1(b) - f2(b)
        if abs(ya) < 1e9 and abs(yb) < 1e9 and ya * yb < 0:
            out.append((a + b) / 2)
    return out


def band(ax, fz, col, label=None):
    lo = [(i, fz.mmt(i)) for i in II if fz.mmt(i) < 1000]
    hi = [(i, fz.tct(i)) for i in II if fz.tct(i) < 1000]
    ax.plot(*zip(*lo), color=col, lw=1.3)
    ax.plot(*zip(*hi), color=col, lw=1.3)
    ax.fill_betweenx([p[1] for p in lo], [p[0] for p in lo],
                     [_loglog(p[1], sorted((b, a) for a, b in fz.clear)) or p[0] for p in lo], color=col, alpha=0.2, lw=0,
                     label=label)


def curve(ax, fun, col, ls="-", lw=1.8, label=None):
    pts = [(i, fun(i)) for i in II if fun(i) < 1000]
    ax.plot(*zip(*pts), color=col, ls=ls, lw=lw, label=label)


def loglog(ax, xlab="Current (A at 4.16 kV)"):
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(0.01, 1000)
    ax.grid(True, which="major", color=GRID, lw=0.8)
    ax.grid(True, which="minor", color=GRID, lw=0.3, alpha=0.6)
    ax.set_xlabel(xlab)


# ---------------------------------------------------------------------------------------------
def fig1():
    fz = m.FTYPE[CONV["fuses"]["F646"]]
    fast, slow = (lambda i: m.t_r1(i, CONV, "f")), (lambda i: m.t_r1(i, CONV, "d"))
    a = cross(slow, fz.tct)                 # below A the fuse clears after the delayed trip
    b = cross(fast, fz.mmt)                 # above B the fuse melts before the fast trip
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    band(ax, fz, AQUA, "fuse F646 (%s): MMT - TCT band" % CONV["fuses"]["F646"].replace("A055C", ""))
    curve(ax, fast, BLUE, label="recloser R1, fast")
    curve(ax, slow, BLUE, ls="--", label="recloser R1, delayed")
    for x, lab, f in ((a, "A", slow), (b, "B", fast)):
        if x:
            ax.plot([x[0]], [f(x[0])], marker="o", ms=8, color=RED, mec=SURF, mew=1.5, zorder=6)
            ax.axvline(x[0], color=RED, lw=0.9, ls=":")
            ax.text(x[0] * 1.06, f(x[0]) * 1.5, "%s\n%s = %.0f A" % (lab, "I F,min" if lab == "A" else "I F,max", x[0]),
                    fontsize=8.5, color=RED, fontweight="bold")
    if a and b:
        ax.annotate("", xy=(b[0], 0.016), xytext=(a[0], 0.016), arrowprops=dict(arrowstyle="<->", color=RED, lw=1.3))
        ax.text((a[0] * b[0]) ** 0.5, 0.019, "coordination range", ha="center", fontsize=8.5, color=RED)
    loglog(ax)
    ax.set_xlim(300, 2e4)
    ax.set_ylabel("Time (s)")
    ax.legend(frameon=True, framealpha=0.92, fontsize=8, loc="upper right")
    ax.set_title("Fig. 1 - conventional recloser-fuse coordination for the fuse-saving scheme",
                 fontsize=9.5, loc="left")
    fig.tight_layout()
    save(fig, "Fig01_conventional_TCC.png")
    return a, b


# ---------------------------------------------------------------------------------------------
def bus(ax, x, y, name, w=0.5, vertical=False, lab_dy=0.22):
    if vertical:
        ax.plot([x, x], [y - w / 2, y + w / 2], color=INK, lw=3, solid_capstyle="butt")
    else:
        ax.plot([x - w / 2, x + w / 2], [y, y], color=INK, lw=3, solid_capstyle="butt")
    ax.text(x, y + lab_dy, name, ha="center", va="bottom", fontsize=7.5, fontweight="bold")


def recl(ax, x, y, name):
    ax.add_patch(plt.Rectangle((x - 0.13, y - 0.13), 0.26, 0.26, fc=RED, ec=INK, lw=0.8, zorder=5))
    ax.text(x, y, name, ha="center", va="center", fontsize=6.3, color="white", fontweight="bold", zorder=6)


def fusemark(ax, x, y, name, dx=0.14, ha="left"):
    ax.plot([x], [y], marker="s", ms=5, color=RED, mec=INK, mew=0.6, zorder=5)
    ax.text(x + dx, y, name, ha=ha, va="center", fontsize=6.6, color=RED, fontweight="bold")


def load(ax, x, y, name, dy=-0.45):
    ax.annotate("", xy=(x, y + dy), xytext=(x, y), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.1))
    ax.text(x + 0.08, y + dy, name, fontsize=6.6, va="center")


def fig2():
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    ax.set_xlim(-0.6, 11.2)
    ax.set_ylim(-2.9, 2.1)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((-0.5, -0.3), 0.8, 0.6, fc="#555", ec=INK))
    ax.text(-0.1, 0, "Grid", color="white", ha="center", va="center", fontsize=7.5, fontweight="bold")
    xs = {"B1": 0.9, "B2": 2.2, "B5": 3.5, "B7": 4.8, "B9": 6.1, "B11": 7.6, "B14": 9.0}
    ax.plot([0.3, 9.0], [0, 0], color=INK, lw=1.3)
    for n, x in xs.items():
        bus(ax, x, 0, n, vertical=True, lab_dy=0.3)
    recl(ax, 1.25, 0, "R1")
    recl(ax, 3.85, 0, "R2")
    recl(ax, 7.95, 0, "R3")
    ax.add_patch(plt.Circle((9.55, 0), 0.16, fc=SURF, ec=INK, lw=1.1))
    ax.add_patch(plt.Circle((9.8, 0), 0.16, fc=SURF, ec=INK, lw=1.1))
    ax.plot([9.0, 9.39], [0, 0], color=INK, lw=1.3)
    ax.add_patch(plt.Circle((10.45, 0), 0.3, fc=SURF, ec=INK, lw=1.3))
    ax.plot([9.96, 10.15], [0, 0], color=INK, lw=1.3)
    ax.text(10.45, 0, "DG", ha="center", va="center", fontsize=8, fontweight="bold")
    # lateral B2 - B3 - B4 with two series fuses, fault F1 at B4
    ax.plot([2.2, 2.2, 2.2], [0, -1.0, -2.0], color=INK, lw=1.3)
    bus(ax, 2.2, -1.0, "B3", lab_dy=-0.32)
    bus(ax, 2.2, -2.0, "B4", lab_dy=-0.32)
    fusemark(ax, 2.2, -0.5, "F2-3")
    fusemark(ax, 2.2, -1.5, "F3-4")
    load(ax, 2.45, -1.0, "L1")
    load(ax, 2.45, -2.0, "L2")
    ax.plot([1.95], [-2.0], marker=(4, 1, 0), ms=11, color=RED)
    ax.text(1.75, -2.0, "F1", color=RED, fontsize=8, fontweight="bold", ha="right", va="center")
    # laterals up and down along the feeder
    ax.plot([3.5, 3.5], [0, 1.1], color=INK, lw=1.3)
    bus(ax, 3.5, 1.1, "B6")
    fusemark(ax, 3.5, 0.55, "F5-6")
    ax.plot([4.8, 4.8], [0, -1.0], color=INK, lw=1.3)
    bus(ax, 4.8, -1.0, "B8", lab_dy=-0.32)
    fusemark(ax, 4.8, -0.5, "F7-8")
    load(ax, 5.05, -1.0, "L4")
    ax.plot([6.1, 6.1], [0, 1.1], color=INK, lw=1.3)
    bus(ax, 6.1, 1.1, "B10")
    fusemark(ax, 6.1, 0.55, "F9-10")
    ax.plot([5.85], [1.1], marker=(4, 1, 0), ms=11, color=RED)
    ax.text(5.65, 1.1, "F2", color=RED, fontsize=8, fontweight="bold", ha="right", va="center")
    ax.plot([7.6, 7.6, 7.6], [0, -1.0, -2.0], color=INK, lw=1.3)
    bus(ax, 7.6, -1.0, "B12", lab_dy=-0.32)
    bus(ax, 7.6, -2.0, "B13", lab_dy=-0.32)
    fusemark(ax, 7.6, -0.5, "F11-12")
    fusemark(ax, 7.6, -1.5, "F12-13")
    load(ax, 7.85, -1.0, "L6")
    load(ax, 7.85, -2.0, "L7")
    ax.text(0.2, -2.75, "For fault F1 the series fuses F3-4 and F2-3 carry the grid's and the DG's current; R1 carries the grid's, "
            "R2 only the DG's, in reverse.", fontsize=7.6, color=INK2)
    ax.set_title("Fig. 2 - a typical distribution network with reclosers, fuses and a DG", fontsize=9.5, loc="left")
    fig.tight_layout()
    save(fig, "Fig02_typical_network.png")


# ---------------------------------------------------------------------------------------------
def fig3():
    """Both setting groups of R2 with the fuse of one real fault per direction.  The recloser and the
    fuse carry different currents (the fuse also carries the other source's share), so each device
    is marked at its own current."""
    cases = {"R2rv": ([r for r in m.FAULTS if r["case"] == "Fig15"][0], "F646", "solid LL fault at 646"),
             "R2fw": ([r for r in m.FAULTS if r["case"] == "Fig8"][0], "F684", "LG fault at 611")}
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.8), sharey=True)
    out = {}
    for ax, unit, title, col in ((axes[0], "R2rv", "Reverse direction: DG contribution, faults above R2", ORANGE),
                                 (axes[1], "R2fw", "Forward direction: grid contribution, faults below R2", BLUE)):
        rec, fname, flt = cases[unit]
        fz = m.FTYPE[DS["fuses"][fname]]
        fast, slow = (lambda i, u=unit: m.t_r2(i, DS, u, "f")), (lambda i, u=unit: m.t_r2(i, DS, u, "d"))
        band(ax, fz, AQUA, "fuse %s (%s)" % (fname, DS["fuses"][fname].replace("A055C", "")))
        curve(ax, fast, col, label="R2 fast: plug %.0f A, TMS %.1f" % (DS[unit]["is_f"], DS[unit]["tms_f"]))
        curve(ax, slow, col, ls="--", label="R2 delayed: plug %.0f A, TMS %.1f" % (DS[unit]["is_d"], DS[unit]["tms_d"]))
        i_r, i_f = m.imax(rec, "R2"), m.imax(rec, fname)
        ax.axvline(i_r, color=col, lw=0.9, alpha=0.8)
        ax.axvline(i_f, color=AQUA, lw=0.9, alpha=0.9)
        tf, td, mm, tc = fast(i_r), slow(i_r), fz.mmt(i_f), fz.tct(i_f)
        for t in (tf, td):
            if t < INF:
                ax.plot([i_r], [t], marker="o", ms=6.5, color=col, mec=SURF, mew=1.4, zorder=6)
        for t in (mm, tc):
            ax.plot([i_f], [t], marker="s", ms=5.5, color=AQUA, mec=SURF, mew=1.2, zorder=6)
        ax.text(0.03, 0.03, "%s\nR2 %.0f A: fast %.3f s, delayed %s\n%s %.0f A: melts %.3f s, clears %.3f s" % (
            flt, i_r, tf, "%.3f s" % td if td < INF else "no trip", fname, i_f, mm, tc), transform=ax.transAxes, fontsize=7.6,
            va="bottom", bbox=dict(boxstyle="round,pad=0.3", fc=SURF, ec=GRID))
        out[unit] = (i_r, tf, td, i_f, mm, tc)
        loglog(ax, "Current (A at 4.16 kV)")
        ax.set_xlim(200, 2e4)
        ax.set_title(title, fontsize=9, loc="left")
        ax.legend(frameon=True, framealpha=0.92, fontsize=7.6, loc="upper center" if unit == "R2rv" else "upper right")
    axes[0].invert_xaxis()
    axes[0].set_ylabel("Time (s)")
    fig.suptitle("Fig. 3 - time-current characteristics of the dual-setting recloser R2: reverse and forward setting",
                 fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "Fig03_DSDR_TCC.png")
    return out


# ---------------------------------------------------------------------------------------------
def fig4():
    recs = m.faults("max", 0.0, "652", "LG")
    r = max(recs, key=lambda x: m.imax(x, "F652"))
    i_f = m.imax(r, "F652")
    f1, f2 = m.FTYPE[CONV["fuses"]["F652"]], m.FTYPE[CONV["fuses"]["F671-2"]]
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    band(ax, f1, BLUE, "F652 (%s), nearest the fault" % CONV["fuses"]["F652"].replace("A055C", ""))
    band(ax, f2, VIOLET, "F671-2 (%s), upstream" % CONV["fuses"]["F671-2"].replace("A055C", ""))
    ax.axvline(i_f, color=RED, lw=1.1)
    vals = [("F652 melts", f1.mmt(i_f), BLUE), ("F652 clears", f1.tct(i_f), BLUE),
            ("F671-2 melts", f2.mmt(i_f), VIOLET), ("F671-2 clears", f2.tct(i_f), VIOLET)]
    for lab, t, col in vals:
        ax.plot([i_f], [t], marker="s", ms=6, color=col, mec=SURF, mew=1.3, zorder=6)
        ax.text(i_f * 1.12, t, "%s  %.3f s" % (lab, t), fontsize=8, va="center", color=col, fontweight="bold")
    ok = f1.tct(i_f) < 0.75 * f2.mmt(i_f)
    ax.text(0.03, 0.04, "LG fault at 652, phase a, DG out: %.0f A through both fuses\n"
            "75 %% rule, eq. (8): F652 clears in %.3f s; 0.75 x F671-2 melting time = %.3f s  ->  %s" % (
                i_f, f1.tct(i_f), 0.75 * f2.mmt(i_f), "coordinated" if ok else "NOT coordinated"),
            transform=ax.transAxes, fontsize=7.8, color=INK, bbox=dict(boxstyle="round,pad=0.35", fc=SURF, ec=GRID))
    loglog(ax, "Fault current (A at 4.16 kV)")
    ax.set_xlim(100, 2e4)
    ax.set_ylabel("Time (s)")
    ax.legend(frameon=True, framealpha=0.92, fontsize=8, loc="upper right")
    ax.set_title("Fig. 4 - series fuse coordination for a single line-to-ground fault", fontsize=9.5, loc="left")
    fig.tight_layout()
    save(fig, "Fig04_series_fuses_SLG.png")
    return i_f, vals, ok


# ---------------------------------------------------------------------------------------------
def fig5():
    boxes = [
        ("box", "Start"),
        ("box", "1  Load flow with and without the DG\nrated currents I nom                [step2_studies, loadflow_all_buses]"),
        ("box", "2-3  Place reclosers and fuses; pickups by eqs. (3), (12)\nI p = OLF x I nom, forward and reverse     [step1_build_model, step3]"),
        ("box", "4  Fuse coefficients a, b by eqs. (6)-(9)\nseries fuses: 75 % rule, eq. (8)                              [step3: Table III]"),
        ("box", "5  Fault analysis: every node, LG / LL / LLG / LLL\ncurrent through R1, R2 and every fuse      [step2_studies, database_study]"),
        ("box", "6-7  Operating times; classify every fault\ncoordination held or lost                          [step3: Figs. 14, 17, Table IV]"),
        ("dec", "Coordination held?"),
        ("box", "8  Revise the recloser TDS by I f,Rec / I f,Fuse\nwithin TDS min ... TDS max"),
        ("box", "9-10  TDS limit reached: revise the fuse size\nseries fuses re-checked with eq. (8)"),
        ("box", "11  Settings valid for this DG capacity\nwrite them into the model and verify         [step4_apply_settings]"),
    ]
    fig, ax = plt.subplots(figsize=(6.8, 9.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(boxes) * 1.0 + 0.3)
    ax.axis("off")
    ys = {}
    for k, (kind, text) in enumerate(boxes):
        y = len(boxes) - k - 0.3
        ys[k] = y
        if kind == "dec":
            ax.add_patch(Polygon([(5, y + 0.42), (7.6, y), (5, y - 0.42), (2.4, y)], closed=True, fc="#fff3d6", ec=INK2, lw=1.2))
            ax.text(5, y, text, ha="center", va="center", fontsize=8.6, fontweight="bold")
        else:
            w = 2.2 if text == "Start" else 8.6
            ax.add_patch(FancyBboxPatch((5 - w / 2, y - 0.34), w, 0.68, boxstyle="round,pad=0.02,rounding_size=0.1",
                                        fc="#eef4fc", ec=BLUE, lw=1.2))
            ax.text(5, y, text, ha="center", va="center", fontsize=7.9, linespacing=1.25)
        if k:
            top = ys[k - 1] - (0.42 if boxes[k - 1][0] == "dec" else 0.34)
            ax.add_patch(FancyArrowPatch((5, top), (5, y + (0.42 if kind == "dec" else 0.34)), arrowstyle="-|>",
                                         mutation_scale=11, color=INK2, lw=1.1))
    yd = ys[6]
    ax.text(5.15, yd - 0.52, "lost", fontsize=8, color=RED, fontweight="bold")
    # held -> step 11
    ax.plot([7.6, 9.75, 9.75], [yd, yd, ys[9]], color=INK2, lw=1.1)
    ax.add_patch(FancyArrowPatch((9.75, ys[9]), (9.3, ys[9]), arrowstyle="-|>", mutation_scale=11, color=INK2, lw=1.1))
    ax.text(8.0, yd + 0.1, "held", fontsize=8, color="#0ca30c", fontweight="bold")
    # after 8 and 9-10: back to the classification
    ax.plot([0.7, 0.25, 0.25], [ys[8], ys[8], ys[5]], color=INK2, lw=1.1)
    ax.plot([0.7, 0.25], [ys[7], ys[7]], color=INK2, lw=1.1)
    ax.add_patch(FancyArrowPatch((0.25, ys[5]), (0.7, ys[5]), arrowstyle="-|>", mutation_scale=11, color=INK2, lw=1.1))
    ax.text(0.32, (ys[5] + ys[7]) / 2, "re-check", fontsize=7.5, color=INK2, rotation=90, va="center")
    ax.set_title("Fig. 5 - the method for recloser-fuse coordination with the DSDR, with the script of each step",
                 fontsize=9.2, loc="left")
    fig.tight_layout()
    save(fig, "Fig05_method_flowchart.png")


# ---------------------------------------------------------------------------------------------
def fig6():
    fz = {k: v.replace("A055C", "") for k, v in DS["fuses"].items()}
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.set_xlim(-0.8, 11.0)
    ax.set_ylim(-0.7, 7.6)
    ax.axis("off")
    P = {"650": (5, 7.0), "RG60": (5, 6.2), "632": (5, 5.0), "633": (7.2, 5.0), "634": (9.6, 5.0), "645": (2.8, 5.0),
         "646": (0.6, 5.0), "DL": (3.6, 3.6), "671": (5, 2.2), "692": (7.2, 2.2), "675": (9.6, 2.2), "684": (2.8, 2.2),
         "611": (0.6, 2.2), "652": (2.8, 0.6), "680": (5, 0.6)}
    lines = [("650", "RG60"), ("RG60", "632"), ("632", "633"), ("633", "634"), ("632", "645"), ("645", "646"), ("632", "671"),
             ("671", "692"), ("692", "675"), ("671", "684"), ("684", "611"), ("684", "652"), ("671", "680")]
    style = {("632", "645"): ":", ("645", "646"): ":", ("671", "684"): ":", ("684", "611"): "-.", ("684", "652"): "-."}
    for a, b in lines:
        ax.plot([P[a][0], P[b][0]], [P[a][1], P[b][1]], color=INK, lw=1.4, ls=style.get((a, b), "-"), zorder=1)
    ax.plot([5, 3.6], [3.6, 3.6], color=INK, lw=1.4)
    for n, (x, y) in P.items():
        if n == "DL":
            ax.text(x - 0.4, y, "distributed load", fontsize=7, color=INK2, ha="right", va="center")
            continue
        bus(ax, x, y, n, w=0.9, lab_dy=0.1)
    # source and regulator
    ax.add_patch(plt.Circle((5, 7.45), 0.16, fc=SURF, ec=INK, lw=1.2))
    ax.text(5.25, 7.45, "grid, 115/4.16 kV 5 MVA substation transformer", fontsize=7, va="center", color=INK2)
    ax.text(5.5, 6.6, "regulator", fontsize=7, color=INK2, va="center")
    # reclosers
    recl(ax, 5, 5.75, "R1")
    recl(ax, 5, 2.65, "R2")
    ax.text(5.25, 5.75, "IAC77, 720 A", fontsize=6.6, color=RED, va="center")
    ax.text(5.25, 2.65, "CDG34, DSDR", fontsize=6.6, color=RED, va="center")
    # fuses (name, x, y, label offset)
    for name, x, y, dx, ha in (("F632", 4.45, 5.0, 0, "c"), ("F633", 5.55, 5.0, 0, "c"), ("F634", 9.1, 5.0, 0, "c"),
                               ("F646", 2.25, 5.0, 0, "c"), ("F645", 2.55, 4.72, 0.12, "left"), ("F-DL", 4.5, 3.6, 0, "c"),
                               ("F671-1", 5.6, 2.2, 0, "c"), ("F671-2", 4.4, 2.2, 0, "c"), ("F671", 5.35, 1.9, 0.14, "left"),
                               ("F692", 6.95, 1.92, -0.12, "right"), ("F692-R", 7.8, 2.2, 0, "c"), ("F675", 9.35, 1.92, -0.12, "right"),
                               ("F684", 2.25, 2.2, 0, "c"), ("F652", 2.8, 1.5, 0.14, "left"), ("F611", 0.35, 1.92, -0.12, "right")):
        ax.plot([x], [y], marker="s", ms=5.5, color=RED, mec=INK, mew=0.6, zorder=5)
        txt = "%s\n%s" % (name, fz[name])
        if ha == "c" and name == "F671-1":                  # above the line: F671's label sits below
            ax.text(x + 0.1, y + 0.12, "%s %s" % (name, fz[name]), ha="left", va="bottom", fontsize=6.3, color=RED,
                    fontweight="bold")
        elif name == "F671":                                # below its marker, clear of F692's label
            ax.text(x + 0.1, y - 0.2, "%s %s" % (name, fz[name]), ha="left", va="center", fontsize=6.3, color=RED,
                    fontweight="bold")
        elif ha == "c":
            ax.text(x, y - 0.14, txt, ha="center", va="top", fontsize=6.3, color=RED, fontweight="bold", linespacing=1.0)
        else:
            ax.text(x + dx, y, txt.replace("\n", " "), ha=ha, va="center", fontsize=6.3, color=RED, fontweight="bold")
    # loads, capacitors, DG, transformer
    for n, lab in (("634", "L634"), ("646", "L646"), ("645", "L645"), ("692", "L692"), ("675", "L675"), ("611", "L611"),
                   ("652", "L652")):
        if n == "692":
            continue
        x, y = P[n]
        ax.annotate("", xy=(x - 0.25, y - 0.55), xytext=(x - 0.25, y), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
        ax.text(x - 0.32, y - 0.55, lab, fontsize=6.4, ha="right", va="center")
    ax.annotate("", xy=(5.35, 1.45), xytext=(5.35, 2.2), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    ax.text(5.42, 1.42, "L671", fontsize=6.4, va="top")
    ax.annotate("", xy=(6.95, 1.65), xytext=(6.95, 2.2), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    ax.text(6.88, 1.6, "L692", fontsize=6.4, ha="right", va="center")
    ax.annotate("", xy=(3.25, 3.6), xytext=(3.6, 3.6), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
    for n in ("611", "675"):
        x, y = P[n]
        ax.plot([x + 0.3, x + 0.3], [y, y - 0.35], color=INK, lw=1.0)
        ax.plot([x + 0.2, x + 0.4], [y - 0.35, y - 0.35], color=INK, lw=1.6)
        ax.plot([x + 0.2, x + 0.4], [y - 0.43, y - 0.43], color=INK, lw=1.6)
        ax.text(x + 0.3, y - 0.6, "C" + n, fontsize=6.4, va="center", ha="center")
    ax.add_patch(plt.Circle((8.3, 5.0), 0.13, fc=SURF, ec=INK, lw=1.1, zorder=4))
    ax.add_patch(plt.Circle((8.5, 5.0), 0.13, fc=SURF, ec=INK, lw=1.1, zorder=4))
    ax.text(8.4, 5.28, "XFM-1", fontsize=6.6, ha="center")
    ax.plot([7.2, 7.2], [2.2, 3.1], color=INK, lw=1.3)
    ax.add_patch(plt.Circle((7.2, 3.2), 0.12, fc=SURF, ec=INK, lw=1.1, zorder=4))
    ax.add_patch(plt.Circle((7.2, 3.38), 0.12, fc=SURF, ec=INK, lw=1.1, zorder=4))
    ax.add_patch(plt.Circle((7.2, 3.85), 0.28, fc=SURF, ec=ORANGE, lw=1.6, zorder=4))
    ax.text(7.2, 3.85, "DG", ha="center", va="center", fontsize=8, fontweight="bold", zorder=5)
    ax.text(7.55, 3.85, "4.05 MVA, 0.69 kV\n0.69/4.16 kV, 0.15 pu", fontsize=6.6, va="center", color=INK2)
    ax.legend(handles=[Line2D([], [], color=INK, lw=1.4, label="three-phase line"),
                       Line2D([], [], color=INK, lw=1.4, ls=":", label="two-phase line"),
                       Line2D([], [], color=INK, lw=1.4, ls="-.", label="single-phase line"),
                       Line2D([], [], marker="s", ms=6, color=RED, ls="", label="recloser / fuse (size of the final design)")],
              loc="lower right", fontsize=7.4, frameon=False)
    ax.set_title("Fig. 6 - IEEE 13-node test feeder with the protective devices of this study", fontsize=9.5,
                 loc="left")
    fig.tight_layout()
    save(fig, "Fig06_IEEE13_with_devices.png")


if __name__ == "__main__":
    print("Figures 1-6:")
    a, b = fig1()
    fig2()
    rng = fig3()
    i_f, vals, ok = fig4()
    fig5()
    fig6()
    print("Fig. 1: R1 with F646 %s - coordination range %.0f A (A) ... %.0f A (B)" % (
        CONV["fuses"]["F646"], a[0] if a else float("nan"), b[0] if b else float("nan")))
    for u, lab in (("R2rv", "reverse"), ("R2fw", "forward")):
        print("Fig. 3: R2 %s - R2 %.0f A fast %.3f s; fuse %.0f A melts %.3f s" % (lab, rng[u][0], rng[u][1], rng[u][3], rng[u][4]))
    print("Fig. 4: LG at 652, %.0f A: %s; 75 %% rule %s" % (i_f, ", ".join("%s %.3f s" % (v[0], v[1]) for v in vals),
                                                         "kept" if ok else "NOT kept"))
