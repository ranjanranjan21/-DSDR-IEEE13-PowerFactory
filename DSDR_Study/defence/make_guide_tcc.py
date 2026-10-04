"""
TCC figures for the DG-CTI guide (fault at 633, fuse F633, recloser R1, and R2 for the DG share).

  figs/tcc_degradation.png  conventional protection: the operating points at 0 % and 100 % DG
  figs/tcc_dsdr.png         DSDR protection at 100 % and at 25 % DG

Curves: the library curves of the study (step3_design_and_evaluate / curves.py, checked against
PowerFactory within 1.2 %). Currents: PowerFactory, penetration studies.
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, STUDY)
import step3_design_and_evaluate as S3          # noqa: E402  (curves only)

SET = json.load(open(os.path.join(STUDY, "results", "settings.json")))
CONV, DSDR = SET["conventional"], SET["dsdr"]
INF = float("inf")
II = [10 ** (2 + k / 300.0) for k in range(751)]
GREEN, BLUE, ORANGE, GREY, RED = "#1baf7a", "#2a78d6", "#eb6834", "#9a9993", "#c62828"

# PowerFactory currents, LLL fault at 633 (A)
I = {0: dict(fuse=4102.5, r1=4162.2, r2=66.0), 25: dict(fuse=4478.0, r1=4111.4, r2=416.0),
     100: dict(fuse=5425.8, r1=3970.1, r2=1500.0)}


def line(ax, fn, **kw):
    pts = [(i, fn(i)) for i in II]
    pts = [(i, t) for i, t in pts if t < INF and 0 < t < 1000]
    ax.plot([i for i, _ in pts], [t for _, t in pts], **kw)


def fuse_band(ax, fz, label, alpha=0.18, col=GREEN, lw=1.8):
    m = [(i, fz.mmt(i)) for i in II if fz.mmt(i) < INF]
    ax.fill_between([i for i, _ in m], [t for _, t in m], [fz.tct(i) for i, _ in m], color=col, alpha=alpha, lw=0)
    ax.plot([i for i, _ in m], [t for _, t in m], color=col, lw=lw, label=label)


def style(ax, xlim, ylim, title):
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.grid(True, which="major", color="#d9d8d4", lw=0.8)
    ax.grid(True, which="minor", color="#d9d8d4", lw=0.3, alpha=0.6)
    ax.set_xlabel("Current (A at 4.16 kV)")
    ax.set_ylabel("Time (s)")
    ax.set_title(title, fontsize=10, loc="left")


def point(ax, i, t, col, marker, text, dx=1.04, dy=1.0, ha="left"):
    ax.axvline(i, color=col, lw=0.8, ls=":")
    ax.plot([i], [t], marker=marker, ms=8, color=col, mec="white", mew=1.2, zorder=6)
    ax.annotate(text, (i, t), xytext=(i * dx, t * dy), fontsize=8.2, color=col, ha=ha, va="center")


def cti_arrow(ax, x, t_low, t_high, text, col):
    ax.annotate("", xy=(x, t_low), xytext=(x, t_high), arrowprops=dict(arrowstyle="<->", color=col, lw=1.4))
    ax.text(x * 1.03, (t_low * t_high) ** 0.5, text, fontsize=9, color=col, fontweight="bold", va="center")


def degradation():
    f250 = S3.FTYPE[CONV["fuses"]["F633"]]
    r1 = lambda i: S3.t_r1(i, CONV, "f")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))
    # full view
    ax = axes[0]
    fuse_band(ax, f250, "F633 250E: melting (solid) to clearing band")
    line(ax, r1, color=BLUE, lw=1.8, label="R1 fast (TDS 0.5)")
    line(ax, lambda i: S3.t_r1(i, CONV, "d"), color=BLUE, lw=1.2, ls="--", label="R1 delayed (TDS 10)")
    ax.axvspan(3500, 6500, color="#fff2cc", alpha=0.6, lw=0)
    ax.text(3600, 40, "zoomed\non the right", fontsize=8, color=GREY)
    style(ax, (300, 2e4), (0.01, 100), "Full view: the curves do not move, the currents do")
    ax.legend(fontsize=8, loc="lower left")
    # zoom
    ax = axes[1]
    fuse_band(ax, f250, "F633 250E melting")
    line(ax, r1, color=BLUE, lw=1.8, label="R1 fast")
    pts = []
    for lev, col in ((0, "#0b3c5d"), (100, RED)):
        c = I[lev]
        tf, tr = f250.mmt(c["fuse"]), r1(c["r1"])
        for i, t, mk, tag in ((c["fuse"], tf, "s", "fuse %d %%" % lev), (c["r1"], tr, "o", "R1 %d %%" % lev)):
            ax.axvline(i, color=col, lw=0.8, ls=":")
            ax.plot([i], [t], marker=mk, ms=8, color=col, mec="white", mew=1.2, zorder=6)
            pts.append((tag, i, t, col))
    ax.annotate("fuse 0 %", (I[0]["fuse"], f250.mmt(I[0]["fuse"])), xytext=(4200, 0.118), fontsize=8.5,
                color="#0b3c5d", arrowprops=dict(arrowstyle="-", color="#0b3c5d", lw=0.7))
    ax.annotate("R1 0 %", (I[0]["r1"], r1(I[0]["r1"])), xytext=(4300, 0.088), fontsize=8.5,
                color="#0b3c5d", arrowprops=dict(arrowstyle="-", color="#0b3c5d", lw=0.7))
    ax.annotate("R1 100 %", (I[100]["r1"], r1(I[100]["r1"])), xytext=(3560, 0.122), fontsize=8.5,
                color=RED, arrowprops=dict(arrowstyle="-", color=RED, lw=0.7))
    ax.annotate("fuse 100 %", (I[100]["fuse"], f250.mmt(I[100]["fuse"])), xytext=(5550, 0.047), fontsize=8.5,
                color=RED, arrowprops=dict(arrowstyle="-", color=RED, lw=0.7))
    c0, c1 = I[0], I[100]
    rows = ["            current    time",
            "fuse 0 %%    %4.0f A   %.3f s" % (c0["fuse"], f250.mmt(c0["fuse"])),
            "R1   0 %%    %4.0f A   %.3f s" % (c0["r1"], r1(c0["r1"])),
            "fuse 100 %%  %4.0f A   %.3f s" % (c1["fuse"], f250.mmt(c1["fuse"])),
            "R1   100 %%  %4.0f A   %.3f s" % (c1["r1"], r1(c1["r1"])),
            "",
            "CTI 0 %%   = %+.0f ms (fuse saved)" % (1000 * (f250.mmt(c0["fuse"]) - r1(c0["r1"]))),
            "CTI 100 %% = %+.0f ms (fuse melts first)" % (1000 * (f250.mmt(c1["fuse"]) - r1(c1["r1"])))]
    ax.text(0.47, 0.97, "\n".join(rows), transform=ax.transAxes, fontsize=8.2, family="monospace", va="top",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#9a9993"))
    ax.annotate("", xy=(c1["fuse"], f250.mmt(c1["fuse"])), xytext=(c0["fuse"] * 1.01, f250.mmt(c0["fuse"]) * 0.98),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.6))
    style(ax, (3500, 6500), (0.04, 0.2), "Zoom: fuse point moves right and down (+32 % current), R1 point barely moves")
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "figs", "tcc_degradation.png"), dpi=170)
    plt.close(fig)


def dsdr():
    f250, f400 = S3.FTYPE[CONV["fuses"]["F633"]], S3.FTYPE[DSDR["fuses"]["F633"]]
    r1 = lambda i: S3.t_r1(i, DSDR, "f")
    r2rv = lambda i: S3.t_r2(i, DSDR, "R2rv", "f")
    r2fw = lambda i: S3.t_r2(i, CONV, "R2fw", "f")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4))
    for ax, lev in zip(axes, (100, 25)):
        c = I[lev]
        fuse_band(ax, f250, "F633 250E (before revision)", alpha=0.06, col=GREY, lw=1.0)
        fuse_band(ax, f400, "F633 400E melting (revised)")
        line(ax, r1, color=BLUE, lw=1.8, label="R1 fast (removes the grid share)")
        line(ax, r2rv, color=ORANGE, lw=1.8, label="R2 reverse fast, DSDR (removes the DG share)")
        line(ax, r2fw, color=ORANGE, lw=1.1, ls="--", alpha=0.6, label="R2 forward fast = conventional R2")
        tf, t1, t2 = f400.mmt(c["fuse"]), r1(c["r1"]), r2rv(c["r2"])
        point(ax, c["fuse"], tf, GREEN, "s", "F633 400E: %.0f A\nmelts %.3f s" % (c["fuse"], tf), dx=1.04, dy=1.0)
        point(ax, c["r1"], t1, BLUE, "o", "R1: %.0f A\n%.3f s" % (c["r1"], t1), dx=0.96, dy=0.75, ha="right")
        if t2 < INF:
            point(ax, c["r2"], t2, ORANGE, "o", "R2 reverse: %.0f A\n%.3f s" % (c["r2"], t2), dx=0.93, dy=1.0, ha="right")
        t2c = r2fw(c["r2"])
        last = max(t1, t2 if t2 < INF else 0)
        txt = ("CTI vs R1 = %+.0f ms\nmargin to last fast trip = %+.0f ms" % (1000 * (tf - t1), 1000 * (tf - last)))
        ax.text(0.03, 0.04, txt, transform=ax.transAxes, fontsize=9, fontweight="bold",
                color="#2e7d32" if tf > last else RED,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#2e7d32" if tf > last else RED))
        conv_txt = "conventional R2 at %.0f A: %s" % (c["r2"], "no trip" if t2c == INF else "%.3f s" % t2c)
        ax.text(0.03, 0.3, conv_txt, transform=ax.transAxes, fontsize=8, color=GREY)
        style(ax, (200, 2e4), (0.02, 20), "DG %d %%: fault at 633 with the DSDR" % lev)
        ax.legend(fontsize=7.4, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "figs", "tcc_dsdr.png"), dpi=170)
    plt.close(fig)
    for lev in (100, 25):
        c = I[lev]
        print(lev, "F633 400E", round(f400.mmt(c["fuse"]), 3), "R1", round(r1(c["r1"]), 3), "R2rv", round(r2rv(c["r2"]), 3),
              "R2 conv", r2fw(c["r2"]))


if __name__ == "__main__":
    degradation()
    dsdr()
    print("written figs/tcc_degradation.png, figs/tcc_dsdr.png")
