"""
Figures and numbers for the EMT guide (LL a-c fault at 684 through 0.2 ohm, conventional settings).

  figs/emt_paths.png      who feeds the fault while R2 is closed and while it is open
  figs/emt_anatomy.png    one fast shot in detail: instantaneous current, one-cycle RMS, peaks
  figs/emt_sequence.png   RMS current through the fuse during the whole sequence, without and with DG
  figs/emt_heat.png       accumulated fuse heating (per cent of melting) against time
  figs/emt_timeline.png   the events of the two runs on one time axis
  figs/emt_numbers.json   the numbers quoted in the guide

Source: results/Fig10_EMT_DG_out.csv, Fig10_EMT_DG_in.csv and Fig10_summary.json (PowerFactory EMT).
"""

import csv
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, STUDY)
import step3_design_and_evaluate as S3          # noqa: E402  (curves only)

RES = os.path.join(STUDY, "results")
FIGS = os.path.join(HERE, "figs")
SUM = json.load(open(os.path.join(RES, "Fig10_summary.json")))
SET = json.load(open(os.path.join(RES, "settings.json")))["conventional"]
FUSE = S3.FTYPE[SET["fuses"]["F671-2"]]
CYCLE, T0 = 1 / 60.0, 0.30
GREEN, BLUE, ORANGE, GREY, RED, INK = "#1baf7a", "#2a78d6", "#eb6834", "#9a9993", "#c62828", "#33373c"
COL = {"DG out": BLUE, "DG in": ORANGE}
NAME = {"DG out": "without DG", "DG in": "with DG"}
CAP = {"DG out": "Without DG", "DG in": "With DG"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#8a8983", "axes.linewidth": 0.7})

ELEM = {"I632": "LOHL650-632", "IR2": "LOHL632-671end", "IF": "LOHL671-684"}


def load(tag):
    with open(os.path.join(RES, "Fig10_EMT_%s.csv" % tag.replace(" ", "_"))) as f:
        rows = list(csv.reader(f))
    data = [[float(x) for x in r] for r in rows[2:] if r and r[0].strip()]
    t = [r[0] for r in data]
    w = {}
    for key, name in ELEM.items():
        cols = [k for k in range(1, len(rows[0])) if rows[0][k] == name]
        ca = [k for k in cols if "Phase Current A" in rows[1][k]][0]
        cc = [k for k in cols if "Phase Current C" in rows[1][k]][0]
        w[key] = ([r[ca] for r in data], [r[cc] for r in data])
    return t, w


def rms(t, x):
    n = max(1, int(round(CYCLE / (t[1] - t[0]))))
    out, acc = [], 0.0
    for k, v in enumerate(x):
        acc += v * v
        if k >= n:
            acc -= x[k - n] * x[k - n]
        out.append(math.sqrt(max(acc, 0.0) / min(k + 1, n)))
    return out


def max_rms(t, w, key):
    a, c = rms(t, w[key][0]), rms(t, w[key][1])
    return [max(p, q) for p, q in zip(a, c)]


def heat(t, i_f):
    """accumulated melting heat sum(dt / MMT(I)) from the fault instant"""
    h, acc = [], 0.0
    for k in range(len(t)):
        if k and t[k] >= T0 and i_f[k] > 0:
            acc += (t[k] - t[k - 1]) / FUSE.mmt(i_f[k])
        h.append(acc)
    return h


def clean(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(True, color="#e3e2de", lw=0.5)
    ax.set_axisbelow(True)


DATA = {}
for tag in ("DG out", "DG in"):
    t, w = load(tag)
    i_f = max_rms(t, w, "IF")
    DATA[tag] = dict(t=t, w=w, iF=i_f, iR2=max_rms(t, w, "IR2"), heat=heat(t, i_f), ev=SUM[tag]["events"])

NUM = {}
for tag, d in DATA.items():
    t, h, ev, s = d["t"], d["heat"], d["ev"], SUM[tag]
    at = lambda x, when: x[min(range(len(t)), key=lambda j: abs(t[j] - when))]
    marks = [("fault", T0)] + [(e[1], e[0]) for e in ev]
    budget, prev_t, prev_h = [], T0, 0.0
    for name, tt in marks[1:]:
        hh = min(at(h, tt), 1.0) if tt > (s["t_melt"] or 9) else at(h, tt)
        budget.append(dict(until=name, t=tt, added=at(h, tt) - prev_h, total=at(h, tt),
                           i_fuse=at(d["iF"], tt - 0.01)))
        prev_t, prev_h = tt, at(h, tt)
    NUM[tag] = dict(budget=budget, i_fuse_fault=s["i_fuse"], i_r2=s["i_r2"], t_fast=s["t_fast"],
                    mmt_at_fault=FUSE.mmt(s["i_fuse"]), tct_at_fault=FUSE.tct(s["i_fuse"]),
                    i_fuse_dead=at(d["iF"], ev[0][0] + 0.15), mmt_dead=FUSE.mmt(max(at(d["iF"], ev[0][0] + 0.15), 1.0)),
                    t_melt=s["t_melt"], t_clear=s["t_clear"], heat_fast=s["heat_after_fast_shots"])
    # the curve (RMS-study) value of the fast time, without the breaker time
    NUM[tag]["t_fast_curve"] = s["t_fast"] - 3 / 60.0
json.dump(NUM, open(os.path.join(FIGS, "emt_numbers.json"), "w"), indent=1)


# --------------------------------------------------------------------------------------------- paths
def paths():
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 4.5))
    for ax, (title, r2_closed) in zip(axes, (("R2 closed: the fault is fed from both sides", True),
                                             ("R2 open (dead time): only the DG still feeds the fault", False))):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 3.2)
        ax.axis("off")
        ax.text(0, 3.05, title, fontsize=9.5, color=INK, weight="bold", va="top")
        y = 1.6
        ax.plot([0.6, 8.2], [y, y], color=INK, lw=1.4)
        xs = {"Grid": 0.6, "R1": 1.7, "632": 2.8, "R2": 4.0, "671": 5.3, "F671-2": 6.6, "684": 8.2}
        ax.add_patch(Circle((0.6, y), 0.22, fc="white", ec=INK, lw=1.2))
        ax.text(0.6, y, "~", ha="center", va="center", fontsize=11)
        ax.text(0.6, y - 0.5, "Grid", ha="center", fontsize=8)
        for name in ("R1", "R2"):
            closed = r2_closed or name == "R1"
            ax.add_patch(Rectangle((xs[name] - 0.2, y - 0.2), 0.4, 0.4, fc=GREEN if closed else "white",
                                   ec=GREEN if closed else RED, lw=1.4))
            ax.text(xs[name], y - 0.5, name + ("" if closed else " OPEN"), ha="center", fontsize=8,
                    color=INK if closed else RED)
        for name in ("632", "671", "684"):
            ax.plot([xs[name]] * 2, [y - 0.22, y + 0.22], color=INK, lw=2.2)
            ax.text(xs[name], y + 0.32, name, ha="center", fontsize=8)
        ax.add_patch(Rectangle((xs["F671-2"] - 0.28, y - 0.1), 0.56, 0.2, fc="white", ec=ORANGE, lw=1.4))
        ax.text(xs["F671-2"], y - 0.5, "fuse F671-2", ha="center", fontsize=8, color=INK)
        ax.text(8.45, y, "LL fault a-c\n0.2 ohm", va="center", fontsize=8, color=RED)
        ax.plot([8.2], [y], marker=(4, 1, 0), ms=11, color=RED)
        # DG branch at 671 (node 692 is next to 671)
        ax.plot([5.3, 5.3], [y, 0.55], color=INK, lw=1.4)
        ax.add_patch(Circle((5.3, 0.42), 0.2, fc="white", ec=INK, lw=1.2))
        ax.text(5.3, 0.42, "G", ha="center", va="center", fontsize=8)
        ax.text(5.62, 0.42, "DG at 692 (4.05 MVA)", va="center", fontsize=8)
        if r2_closed:
            ax.add_patch(FancyArrowPatch((1.0, y + 0.75), (5.1, y + 0.75), arrowstyle="-|>", mutation_scale=11,
                                         color=BLUE, lw=1.6))
            ax.text(3.0, y + 0.85, "grid share, through R1 and R2", ha="center", fontsize=8, color=INK)
        ax.add_patch(FancyArrowPatch((5.55, 0.75), (5.55, y - 0.25), arrowstyle="-|>", mutation_scale=11,
                                     color=ORANGE, lw=1.6))
        ax.text(5.7, 1.0, "DG share", fontsize=8, color=INK)
        ax.add_patch(FancyArrowPatch((5.5, y + 0.75), (8.0, y + 0.75), arrowstyle="-|>", mutation_scale=11,
                                     color=RED, lw=1.6))
        ax.text(6.75, y + 0.85, "fuse current = grid + DG" if r2_closed else "fuse current = DG only",
                ha="center", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "emt_paths.png"), dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------------------------- anatomy
def anatomy():
    d = DATA["DG out"]
    t, x = d["t"], d["w"]["I632"][1]
    r = rms(t, x)
    s = SUM["DG out"]["node632"]
    k0, k1 = [min(range(len(t)), key=lambda j: abs(t[j] - v)) for v in (0.25, 0.47)]
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    ax.plot(t[k0:k1], x[k0:k1], color=BLUE, lw=0.9, label="instantaneous current, phase c at node 632")
    ax.plot(t[k0:k1], r[k0:k1], color=ORANGE, lw=1.8, label="one-cycle RMS of the same current")
    ax.axvline(T0, color=INK, lw=0.8, ls="--")
    ax.axvline(0.42, color=INK, lw=0.8, ls=":")
    ax.text(T0 - 0.002, -5300, "fault at 0.30 s", ha="right", fontsize=8, color=INK)
    ax.text(0.422, -5300, "R2 opens at 0.420 s", ha="left", fontsize=8, color=INK)
    kp = max(range(k0, k1), key=lambda j: abs(x[j]) if T0 <= t[j] <= T0 + 0.03 else 0)
    ax.annotate("first peak %.0f A\n(DC offset)" % abs(x[kp]), (t[kp], x[kp]), (t[kp] + 0.012, x[kp] * 1.02),
                fontsize=8, color=INK, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7), va="center")
    ax.text(0.385, s["steady_peak_c"] + 250, "steady peak %.0f A" % s["steady_peak_c"], fontsize=8, color=INK, ha="center")
    ax.text(0.362, s["fault_rms_c"] - 620, "RMS %.0f A" % s["fault_rms_c"], fontsize=8, color=INK)
    ax.text(0.262, s["prefault_rms_c"] + 500, "load\nRMS %.0f A" % s["prefault_rms_c"], fontsize=8, color=INK)
    ax.text(0.445, 420, "R2 open:\nonly load upstream of R2", fontsize=8, color=INK, ha="center")
    ax.set_xlim(0.25, 0.47)
    ax.set_ylim(-5800, 5800)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Current (A)")
    clean(ax)
    ax.legend(frameon=False, fontsize=8, loc="lower left", ncol=2, bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "emt_anatomy.png"), dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------------------------- sequence
def shade(ax, ev, ymax):
    opens = [e[0] for e in ev if "trip" in e[1]]
    closes = [e[0] for e in ev if "reclose" in e[1]]
    for k, (a, b) in enumerate(zip(opens, closes)):
        ax.axvspan(a, b, color="#e9e8e4", lw=0)
        ax.text((a + b) / 2, ymax * 0.97, "R2 open", ha="center", va="top", fontsize=7.5, color="#55585c")


def sequence():
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True)
    for ax, tag in zip(axes, ("DG out", "DG in")):
        d, s = DATA[tag], SUM[tag]
        ymax = 5200
        shade(ax, d["ev"], ymax)
        ax.plot(d["t"], d["iF"], color=COL[tag], lw=1.6)
        ax.axvline(T0, color=INK, lw=0.8, ls="--")
        ax.axvline(s["t_melt"], color=RED, lw=1.0, ls="--")
        ax.text(s["t_melt"] + 0.012, ymax * 0.80, "fuse melts\n%.3f s" % s["t_melt"], fontsize=8, color=INK)
        ax.axvline(s["t_clear"], color=INK, lw=0.8, ls=":")
        ax.text(s["t_clear"] + 0.012, ymax * 0.55, "fuse clears\n%.3f s" % s["t_clear"], fontsize=8, color=INK)
        ax.text(0.335, s["i_fuse"] + 150, "%.0f A" % s["i_fuse"], fontsize=8, color=INK)
        ax.set_ylim(0, ymax)
        ax.set_ylabel("Fuse current, RMS (A)")
        ax.set_title("%s: current through fuse F671-2 (300E)" % CAP[tag], fontsize=9.5, loc="left",
                     color=INK)
        clean(ax)
    dead = NUM["DG in"]["i_fuse_dead"]
    axes[1].annotate("the DG keeps feeding the fault:\nabout %.0f A while R2 is open" % dead, (0.53, dead), (0.53, 2250),
                     fontsize=8, color=INK, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7), ha="center")
    axes[0].annotate("no current through the fuse\nwhile R2 is open", (0.53, 60), (0.53, 1100),
                     fontsize=8, color=INK, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7), ha="center")
    axes[1].text(1.31, 1150, "after reclosing the current swings:\nthe DG is no longer in step\nwith the grid", fontsize=8, color=INK)
    axes[1].set_xlabel("Time (s)")
    axes[1].set_xlim(0.2, 1.8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "emt_sequence.png"), dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------------------------- heat
def heat_fig():
    fig, ax = plt.subplots(figsize=(7.4, 3.7))
    for tag in ("DG out", "DG in"):
        d, s = DATA[tag], SUM[tag]
        kk = [k for k in range(len(d["t"])) if d["t"][k] <= s["t_melt"] + 0.02]
        ax.plot([d["t"][k] for k in kk], [100 * min(d["heat"][k], 1.06) for k in kk], color=COL[tag], lw=2,
                label="%s" % NAME[tag])
        ax.plot([s["t_melt"]], [100], "o", ms=7, color=COL[tag], mec="white", mew=1.5)
    ax.axhline(100, color=RED, lw=1.0, ls="--")
    ax.text(0.205, 102.5, "100 % = the fuse element melts", fontsize=8, color=INK)
    for name, tt in (("trip 1", 0.42), ("reclose 1", 0.62), ("trip 2", 0.74), ("reclose 2", 0.94)):
        ax.axvline(tt, color=GREY, lw=0.6, ls=":")
        ax.text(tt, -13, name, ha="center", fontsize=7.5, color="#55585c")
    ax.text(0.80, 34, "without DG: 45 % after\nthe two fast shots", fontsize=8, color=INK)
    ax.text(0.47, 62, "with DG: heating continues\nwhile R2 is open", fontsize=8, color=INK)
    ax.text(SUM["DG in"]["t_melt"] + 0.012, 91, "melts %.3f s" % SUM["DG in"]["t_melt"], fontsize=8, color=INK, va="top")
    ax.text(SUM["DG out"]["t_melt"] + 0.012, 91, "melts %.3f s" % SUM["DG out"]["t_melt"], fontsize=8, color=INK, va="top")
    ax.set_xlim(0.2, 1.4)
    ax.set_ylim(0, 115)
    ax.set_xlabel("Time (s)", labelpad=14)
    ax.set_ylabel("Fuse heat (% of melting)")
    clean(ax)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0, 0.9))
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "emt_heat.png"), dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------------------------- timeline
def timeline():
    fig, ax = plt.subplots(figsize=(7.4, 2.6))
    for row, tag in enumerate(("DG out", "DG in")):
        y = 1 - row
        s, ev = SUM[tag], SUM[tag]["events"]
        tr = [e[0] for e in ev if "trip" in e[1]]
        rc = [e[0] for e in ev if "reclose" in e[1]]
        on = [(T0, tr[0]), (rc[0], tr[1]), (rc[1], s["t_clear"])]
        for a, b in on:
            ax.barh(y, b - a, left=a, height=0.36, color=COL[tag], edgecolor="white", lw=1.5)
        for a, b in zip(tr, rc):
            ax.barh(y, b - a, left=a, height=0.36, color="#e3e2de", edgecolor="white", lw=1.5)
            ax.text((a + b) / 2, y, "R2 open", ha="center", va="center", fontsize=7.5, color="#55585c")
        ax.plot([s["t_melt"]], [y], marker="v", ms=9, color=RED, mec="white", mew=1.2)
        ax.text(s["t_melt"], y + 0.3, "melts %.3f" % s["t_melt"], ha="center", fontsize=7.5, color=INK)
        ax.text(s["t_clear"] + 0.015, y, "clears %.3f s" % s["t_clear"], va="center", fontsize=8, color=INK)
        ax.text(0.19, y, CAP[tag], ha="right", va="center", fontsize=9, color=INK)
    ax.text(T0, 1.52, "fault 0.30 s", ha="center", fontsize=7.5, color=INK)
    ax.set_xlim(0.2, 1.85)
    ax.set_ylim(-0.5, 1.75)
    ax.set_yticks([])
    ax.set_xlabel("Time (s)   -   coloured: fault current flows through the fuse (R2 closed)")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "emt_timeline.png"), dpi=170)
    plt.close(fig)


paths()
anatomy()
sequence()
heat_fig()
timeline()
for tag in NUM:
    n = NUM[tag]
    print(tag, "I_fuse %.0f A, MMT %.3f s, TCT %.3f s, I_R2 %.0f A, t_fast %.3f (curve %.3f), dead I_fuse %.0f A (MMT %.2f s)" % (
        n["i_fuse_fault"], n["mmt_at_fault"], n["tct_at_fault"], n["i_r2"], n["t_fast"], n["t_fast_curve"],
        n["i_fuse_dead"], n["mmt_dead"]))
    for b in n["budget"]:
        print("   until %-16s t=%.3f  +%.1f %%  total %.1f %%   (I_fuse %.0f A)" % (
            b["until"], b["t"], 100 * b["added"], 100 * b["total"], b["i_fuse"]))
