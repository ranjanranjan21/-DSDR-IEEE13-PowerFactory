"""
Time-sequence check of the fuse-saving scheme for every fault behind the 39 node / fault-type cells,
DG connected, R2 with a single setting and as DSDR (same fuse sizes: the final design).

The strict rule of Figs. 14 / 17 compares every recloser's fast time with the fuse's melting time at
the full fault current.  Here the fault is followed in time instead:

  faults above R2 (R1's zone)   the grid feeds through R1, the DG through R2 (reverse).  Until the
      first recloser opens the fuse carries the whole fault current; afterwards only the other
      source's contribution.  Fuse heat = sum(dt / MMT(I)).
  faults below R2 (R2's zone)   R2 interrupts the grid.  The DG at 692 feeds these faults directly;
      no recloser lies between the DG and the fault.

Outcome of one fault (fast shot, temporary fault):
  held        every source is interrupted and the fuse heat stays below 100 %; the delayed-trip and
              series-fuse conditions of the strict rule hold as well
  melts       the fuse reaches 100 % before the reclosers have cut the fault off
  R2 blind    R2 does not trip on the DG's reverse current: the DG keeps feeding the fault
  DG direct   fault below R2: the DG keeps feeding it after R2 has opened (independent of R2's setting)
  other       the fast sequence is fine but a delayed-trip or series-fuse condition fails
A cell takes the worst outcome of its phase combinations.

Assumption: after one recloser has opened, the other source's current stays at the contribution it
had during the fault (initial symmetrical values); nothing is simulated.  Single shot, no breaker time.

Outputs: results/coordination_diagrams/Sequence_check.csv, 10_Sequence_check.png
"""

import copy
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import step3_design_and_evaluate as m
from curves import INF
from protection_data import NODES, NODE_ORDER, FAULT_TYPES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "coordination_diagrams")
os.makedirs(OUT, exist_ok=True)
SET = json.load(open(os.path.join(HERE, "results", "settings.json")))
CONV, DS = SET["conventional"], SET["dsdr"]
ORDER = ["melts", "R2 blind", "DG direct", "other", "held"]          # worst first
DG_MIN = 50.0                                                        # A: a DG share below this is ignored


def open_csv(path):
    """Open a csv for writing; if it is open in Excel write <name>_new.csv instead."""
    try:
        return open(path, "w", newline="")
    except PermissionError:
        print("locked, writing", os.path.basename(path).replace(".csv", "_new.csv"))
        return open(path.replace(".csv", "_new.csv"), "w", newline="")


def scheme(fuses, dual):
    s = copy.deepcopy(DS)
    s["fuses"] = dict(fuses)
    if not dual:
        s["R2fw"] = copy.deepcopy(CONV["R2fw"])
    return s


def sequence(r, s, dual):
    """-> dict(outcome, text, heat, t_end) for one fault record"""
    node = r["where"]
    info = NODES[node]
    path = info["path"]
    i1, i2 = m.imax(r, "R1"), m.imax(r, "R2")
    fz = m.FTYPE[s["fuses"][path[0]]] if path else None
    i_p = m.imax(r, path[0]) if path else 0.0
    st = m.evaluate(r, s, dual)                                       # strict rule, for the other conditions
    other = [x for x in st["reason"].split("; ") if x and ("delayed" in x or "series" in x or "not before" in x)]

    def heat_add(heat, dt, cur):
        mm = fz.mmt(cur) if fz else INF
        return heat + (dt / mm if mm < INF else 0.0), mm

    if info["zone"] == "R1":
        unit = "R2rv" if dual else "R2fw"
        trips = [(m.t_r1(i1, s, "f"), "R1", i1)]
        if r["dg"] > 0 and i2 >= s["dg_infeed"]:
            trips.append((m.t_r2(i2, s, unit, "f"), "R2", i2))
        trips.sort()
        heat, t_prev, cur, steps = 0.0, 0.0, i_p, []
        for k, (t, who, i_src) in enumerate(trips):
            if t == INF:
                return dict(outcome="R2 blind" if who == "R2" else "melts", heat=heat, t_end=INF,
                            text="; ".join(steps + ["%s does not trip: %.0f A keeps feeding the fault" % (who, i_src)]))
            new, mm = heat_add(heat, t - t_prev, cur)
            if fz and new >= 1.0:
                return dict(outcome="melts", heat=1.0, t_end=t_prev + (1.0 - heat) * mm,
                            text="; ".join(steps + ["%s melts at %.3f s, before %s opens (%.3f s)" % (
                                path[0], t_prev + (1.0 - heat) * mm, who, t)]))
            heat, t_prev = new, t
            rest = sum(x[2] for x in trips[k + 1:])
            cur = min(rest, i_p) if path else rest
            steps.append("%s opens %.3f s" % (who, t))
        out = "held" if not other else "other"
        return dict(outcome=out, heat=heat, t_end=t_prev,
                    text="; ".join(steps) + ("; fuse heat %.0f %%" % (100 * heat) if fz else "") +
                         ("; " + other[0] if other else ""))

    # ---- fault below R2 ------------------------------------------------------------------------
    t2 = m.t_r2(i2, s, "R2fw", "f")
    if t2 == INF:
        return dict(outcome="melts", heat=0.0, t_end=INF, text="R2 does not pick up (%.0f A)" % i2)
    heat, mm = heat_add(0.0, t2, i_p)
    if fz and heat >= 1.0:
        return dict(outcome="melts", heat=1.0, t_end=mm, text="%s melts at %.3f s, before R2 opens (%.3f s)" % (path[0], mm, t2))
    i_dg = max(r["ifault"]) - i2 if r.get("ifault") else 0.0
    base = "R2 opens %.3f s" % t2 + ("; fuse heat %.0f %%" % (100 * heat) if fz else "")
    if r["dg"] > 0 and i_dg > DG_MIN:
        i_after = max(i_p - i2, 0.0) if path else 0.0                  # DG share that still flows through the fuse
        mm2 = fz.mmt(i_after) if (fz and i_after > 0) else INF
        tail = ("; the DG's %.0f A then melts %s after a further %.2f s" % (i_after, path[0], (1.0 - heat) * mm2)
                if mm2 < INF else "")
        return dict(outcome="DG direct", heat=heat, t_end=INF,
                    text=base + "; the DG still feeds about %.0f A into the fault%s" % (i_dg, tail))
    out = "held" if not other else "other"
    return dict(outcome=out, heat=heat, t_end=t2, text=base + ("; " + other[0] if other else ""))


def run(fuses=None, write=True):
    fuses = fuses or DS["fuses"]
    rows, grids = [], {}
    for dual in (False, True):
        s = scheme(fuses, dual)
        g = {}
        strict, _ = m.classify(s, dual, 1.0)
        for node in NODE_ORDER:
            for ft in FAULT_TYPES:
                recs = m.faults("max", 1.0, node, ft)
                if NODES[node].get("lv") or not recs:
                    g[(node, ft)] = "n/a"
                    continue
                res = [(r, sequence(r, s, dual)) for r in recs]
                g[(node, ft)] = min((x[1]["outcome"] for x in res), key=ORDER.index)
                for r, q in res:
                    rows.append(["dual" if dual else "single", node, ft, r["phases"], NODES[node]["zone"],
                                 strict[(node, ft)], q["outcome"], "%.0f" % (100 * q["heat"]), q["text"]])
        grids[dual] = (g, strict)
    if write:
        with open_csv(os.path.join(OUT, "Sequence_check.csv")) as f:
            w = csv.writer(f)
            w.writerow(["R2 setting", "node", "fault", "phases", "zone", "strict rule (cell)", "time-sequence outcome",
                        "fuse heat when cut off (%)", "sequence"])
            w.writerows(rows)
    return grids, rows


COLOR = {"held": "#3a9d4a", "melts": "#d03b3b", "R2 blind": "#eb8a34", "DG direct": "#6a5acd", "other": "#9a9993"}
LABEL = {"held": "held: fault cleared before the fuse melts",
         "melts": "fuse melts before the reclosers finish",
         "R2 blind": "R2 does not trip on the reverse (DG) current",
         "DG direct": "below R2: the DG keeps feeding the fault",
         "other": "a delayed-trip or series-fuse condition fails"}


def figure(grids, path):
    """One grid: columns = fault nodes (above R2, then below R2), rows = fault types.  Every cell is split:
    left half = single setting on R2, right half = dual setting (DSDR)."""
    up = [n for n in NODE_ORDER if NODES[n]["zone"] == "R1"]
    dn = [n for n in NODE_ORDER if NODES[n]["zone"] == "R2"]
    cols = up + dn
    gap = 0.6                                              # space between the two zones
    xs = [k + (gap if n in dn else 0) for k, n in enumerate(cols)]
    rows = FAULT_TYPES
    fig, ax = plt.subplots(figsize=(10.2, 4.0), facecolor="white")
    ax.set_facecolor("white")
    for n, x in zip(cols, xs):
        for yk, ft in enumerate(rows):
            y = len(rows) - 1 - yk
            for half, dual in ((0, False), (1, True)):
                st = grids[dual][0][(n, ft)]
                x0 = x - 0.45 + 0.45 * half
                if st == "n/a":
                    ax.add_patch(plt.Rectangle((x0, y - 0.4), 0.45, 0.8, fc="#f1f1ef", ec="white", lw=1.5))
                    continue
                ax.add_patch(plt.Rectangle((x0, y - 0.4), 0.45, 0.8, fc=COLOR[st], ec="white", lw=1.5))
                ax.text(x0 + 0.225, y, "S" if half == 0 else "D", ha="center", va="center", fontsize=7,
                        color="white", fontweight="bold")
    # zone headers
    for group, label in ((up, "Faults above R2 (the DG current flows in reverse through R2)"),
                         (dn, "Faults below R2 (the DG at 692 feeds the fault directly)")):
        gx = [x for n, x in zip(cols, xs) if n in group]
        ax.plot([gx[0] - 0.45, gx[-1] + 0.45], [len(rows) - 0.3] * 2, color="#52514e", lw=1.0)
        ax.text((gx[0] + gx[-1]) / 2, len(rows) - 0.15, label, ha="center", va="bottom", fontsize=8.5,
                color="#0b0b0b")
    # held counts per zone and setting, on the right
    xr = xs[-1] + 0.9
    for yk, (lab, dual) in enumerate((("Single setting (S)", False), ("Dual setting (D)", True))):
        g = grids[dual][0]
        ku = [(n, ft) for n in up for ft in rows if g[(n, ft)] != "n/a"]
        kd = [(n, ft) for n in dn for ft in rows if g[(n, ft)] != "n/a"]
        ax.text(xr, 2.6 - 1.3 * yk, "%s\nabove R2: %d of %d held\nbelow R2: DG feeds %d of %d" % (
            lab, sum(g[k] == "held" for k in ku), len(ku), sum(g[k] == "DG direct" for k in kd), len(kd)),
            ha="left", va="center", fontsize=8.2, linespacing=1.5)
    ax.set_xticks(xs)
    ax.set_xticklabels(cols, fontsize=9)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows[::-1], fontsize=9)
    ax.set_xlabel("Fault node", fontsize=9)
    ax.set_xlim(-0.6, xr + 2.6)
    ax.set_ylim(-0.6, len(rows) + 0.35)
    ax.set_aspect("equal")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    present = {v for d in (False, True) for v in grids[d][0].values()}
    handles = [plt.Rectangle((0, 0), 1, 1, fc=COLOR[k], ec="none", label=LABEL[k]) for k in ORDER[::-1] if k in present]
    handles.append(plt.Rectangle((0, 0), 1, 1, fc="#f1f1ef", ec="none", label="not part of the study grid"))
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=7.8, handlelength=1.4)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    try:
        fig.savefig(path, dpi=170, facecolor="white", bbox_inches="tight", pad_inches=0.08)
    except OSError:                                   # open in a viewer: locked on Windows
        path = path[:-4] + "_new.png"
        fig.savefig(path, dpi=170, facecolor="white", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return path


def cells(pairs):
    out = []
    for n in NODE_ORDER:
        t = [ft for ft in FAULT_TYPES if (n, ft) in pairs]
        if t:
            out.append("%s %s" % (n, "/".join(t)))
    return ", ".join(out) or "none"


def summary(grids):
    """numbers for the text"""
    out = {}
    for dual in (False, True):
        g, strict = grids[dual]
        for zone, lab in (("R1", "above"), ("R2", "below")):
            ks = [k for k, v in g.items() if v != "n/a" and NODES[k[0]]["zone"] == zone]
            out[(dual, lab)] = dict(n=len(ks), strict=sum(strict[k] == "held" for k in ks),
                                    **{o: {k for k in ks if g[k] == o} for o in ORDER})
    return out


if __name__ == "__main__":
    grids, rows = run()
    figure(grids, os.path.join(OUT, "10_Sequence_check.png"))
    sm = summary(grids)
    for dual in (False, True):
        for lab in ("above", "below"):
            d = sm[(dual, lab)]
            print("%-6s %s R2 (%2d cells): strict rule held %2d | sequence: held %2d, melts %d, R2 blind %d, DG direct %d, other %d" % (
                "dual" if dual else "single", lab, d["n"], d["strict"], len(d["held"]), len(d["melts"]), len(d["R2 blind"]),
                len(d["DG direct"]), len(d["other"])))
            for o in ORDER[:-1]:
                if d[o]:
                    print("        %-9s: %s" % (o, cells(d[o])))
    print("Saved", OUT)
