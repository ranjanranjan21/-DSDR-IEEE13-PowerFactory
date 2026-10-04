"""
Figures and numbers for the guide on the margins and on the PowerFactory check.

  figs/margin_cases.png    three faults on a time axis: relay time, breaker time, fuse melting time
  figs/margin_counts.png   cells held with the zero margin, with the breaker time, with breaker time and 75 % MMT
  figs/pf_check.png        distribution of the 1896 comparisons with PowerFactory's own relay and fuse models
  figs/margin_numbers.json the numbers quoted in the guide

Source: results/settings.json, the short-circuit database (through step3_design_and_evaluate) and
results/PF_vs_Python_times_*.csv.
"""

import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, STUDY)
os.chdir(STUDY)
import step3_design_and_evaluate as S3          # noqa: E402

FIGS = os.path.join(HERE, "figs")
GREEN, BLUE, ORANGE, GREY, RED, INK = "#1baf7a", "#2a78d6", "#eb6834", "#9a9993", "#c62828", "#33373c"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#8a8983", "axes.linewidth": 0.7})
INF = float("inf")
TB = 3 / 60.0

s = json.load(open(os.path.join(STUDY, "results", "settings.json")))["dsdr"]
grid, detail = S3.classify(s, True, 1.0)
cells = [k for k, v in grid.items() if v != "n/a"]


def count(rule):
    bad = set()
    for e in detail:
        key = (e["node"], e["type"])
        if not e["held"]:
            bad.add(key)
            continue
        if e["fuse"] is None:
            continue
        for name, unit, i, tf, td in e["reclosers"]:
            if tf < INF and not rule(tf, e["mmt"]):
                bad.add(key)
    return len(cells) - len(bad), sorted(bad)


n0, lost0 = count(lambda tf, mmt: True)
n1, lost1 = count(lambda tf, mmt: tf + TB < mmt)
n2, lost2 = count(lambda tf, mmt: tf + TB < 0.75 * mmt)


def worst(node, ftype):
    """the phase combination of this cell with the smallest zero-margin CTI"""
    ev = [e for e in detail if e["node"] == node and e["type"] == ftype and e["fuse"]]
    e = min(ev, key=lambda x: x["cti_f"])
    tf = max(x[3] for x in e["reclosers"])
    who = max(e["reclosers"], key=lambda x: x[3])[0]
    return dict(node=node, type=ftype, fuse=e["fuse"], size=s["fuses"][e["fuse"]].replace("A055C", ""),
                i_fuse=e["i_fuse"], mmt=e["mmt"], t_fast=tf, recloser=who)


CASES = [worst("646", "LL"), worst("633", "LLL"), worst("675", "LLL")]

# ---- PowerFactory against the calculation
rows = []
for f in ("conventional", "dsdr"):
    for r in csv.DictReader(open(os.path.join(STUDY, "results", "PF_vs_Python_times_%s.csv" % f))):
        r["scheme"] = f
        rows.append(r)
notrip = [r for r in rows if r["PowerFactory t (s)"] == "no trip"]
timed = [r for r in rows if r["PowerFactory t (s)"] != "no trip"]
dev = sorted(abs(float(r["deviation %"])) for r in timed)
top = max(timed, key=lambda r: abs(float(r["deviation %"])))
bins = [("0 to 0.1", 0, 0.1), ("0.1 to 0.5", 0.1, 0.5), ("0.5 to 1.0", 0.5, 1.0), ("1.0 to 1.22", 1.0, 9)]
hist = [(lab, sum(1 for d in dev if lo <= d < hi)) for lab, lo, hi in bins]
by_dev = {}
for r in rows:
    k = "fuses" if "MMT" in r["device"] else r["device"].split()[0]
    by_dev[k] = by_dev.get(k, 0) + 1
NUM = dict(held=[n0, n1, n2], lost1=[list(x) for x in lost1 if x not in lost0],
           lost2=[list(x) for x in lost2 if x not in lost1], lost0=[list(x) for x in lost0], cases=CASES,
           pf=dict(total=len(rows), conventional=sum(r["scheme"] == "conventional" for r in rows),
                   dsdr=sum(r["scheme"] == "dsdr" for r in rows), notrip=len(notrip), timed=len(timed),
                   notrip_mismatch=sum(r["PowerFactory t (s)"] != r["Python t (s)"] for r in rows
                                       if "no trip" in (r["PowerFactory t (s)"], r["Python t (s)"])),
                   max=max(dev), mean=sum(dev) / len(dev), median=dev[len(dev) // 2], hist=hist, by_device=by_dev,
                   top=dict(node=top["node"], fault=top["fault"], phases=top["phases"], device=top["device"],
                            pf=top["PowerFactory t (s)"], calc=top["Python t (s)"]),
                   dg_out=sum(r["DG"] == "0.0" for r in rows), dg_in=sum(r["DG"] == "1.0" for r in rows)))
json.dump(NUM, open(os.path.join(FIGS, "margin_numbers.json"), "w"), indent=1)


def clean(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


# ------------------------------------------------------------------------------------------ cases
fig, axes = plt.subplots(len(CASES), 1, figsize=(7.4, 4.6), sharex=True)
for ax, c in zip(axes, CASES):
    tf, mmt = c["t_fast"], c["mmt"]
    ax.barh(0, tf, height=0.42, color=BLUE, edgecolor="white", lw=1.5)
    ax.barh(0, TB, left=tf, height=0.42, color="#9cc3ee", edgecolor="white", lw=1.5)
    ax.axvline(mmt, color=RED, lw=1.6)
    ax.axvline(0.75 * mmt, color=RED, lw=1.0, ls="--")
    ax.text(tf / 2, 0, "relay\n%.3f s" % tf, ha="center", va="center", fontsize=7.5, color="white")
    ax.text(tf + TB / 2, 0, "breaker\n0.050 s", ha="center", va="center", fontsize=7.5, color=INK)
    ax.text(mmt + 0.004, 0.36, "fuse melts %.3f s" % mmt, fontsize=8, color=INK, va="center")
    ax.text(0.75 * mmt - 0.004, -0.36, "75 %% = %.3f s" % (0.75 * mmt), fontsize=7.5, color=INK, va="center", ha="right")
    z = "held" if tf < mmt else "lost"
    b = "held" if tf + TB < mmt else "lost"
    m = "held" if tf + TB < 0.75 * mmt else "lost"
    ax.set_title("%s fault at %s: %s fast trip against fuse %s (%s)" % (
        c["type"], c["node"], c["recloser"], c["fuse"], c["size"]), fontsize=9, loc="left", color=INK)
    ax.text(0.555, 0, "zero margin: %s\nwith breaker time: %s\nand 75 %% of MMT: %s" % (z, b, m), fontsize=8,
            color=INK, va="center", ha="right")
    ax.set_yticks([])
    ax.set_ylim(-0.6, 0.6)
    clean(ax)
    ax.spines["left"].set_visible(False)
axes[-1].set_xlim(-0.012, 0.56)
axes[-1].set_xlabel("Time after the fault starts (s)")
fig.tight_layout()
fig.savefig(os.path.join(FIGS, "margin_cases.png"), dpi=170)
plt.close(fig)

# ------------------------------------------------------------------------------------------ counts
fig, ax = plt.subplots(figsize=(6.2, 2.3))
labels = ["Zero margin\n(classification of the report)", "+ breaker time, 3 cycles", "+ breaker time\nand fuse at 75 % of MMT"]
vals = [n0, n1, n2]
ax.barh(range(3), vals, height=0.55, color=[BLUE, "#6ea6e6", "#9cc3ee"], edgecolor="white")
for k, v in enumerate(vals):
    ax.text(v + 0.5, k, "%d of %d" % (v, len(cells)), va="center", fontsize=9, color=INK)
ax.set_yticks(range(3))
ax.set_yticklabels(labels, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlim(0, 46)
ax.set_xlabel("Cells with coordination held (DG in service, DSDR, revised fuses)")
clean(ax)
fig.tight_layout()
fig.savefig(os.path.join(FIGS, "margin_counts.png"), dpi=170)
plt.close(fig)

# ------------------------------------------------------------------------------------------ PowerFactory check
fig, ax = plt.subplots(figsize=(6.2, 2.4))
labs = [h[0] for h in hist]
cnt = [h[1] for h in hist]
ax.bar(range(len(cnt)), cnt, width=0.6, color=BLUE, edgecolor="white")
for k, v in enumerate(cnt):
    ax.text(k, v + 25, str(v), ha="center", fontsize=9, color=INK)
ax.set_xticks(range(len(cnt)))
ax.set_xticklabels(labs)
ax.set_xlabel("Difference between PowerFactory and the calculation (%)")
ax.set_ylabel("Operating times")
ax.set_ylim(0, max(cnt) * 1.15)
clean(ax)
fig.tight_layout()
fig.savefig(os.path.join(FIGS, "pf_check.png"), dpi=170)
plt.close(fig)

print("held:", n0, n1, n2, "of", len(cells))
print("lost with breaker time:", NUM["lost1"])
print("lost in addition with 75 %:", NUM["lost2"])
for c in CASES:
    print(c)
print(NUM["pf"])
