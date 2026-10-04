"""
Equations of the DSDR coordination method as one picture for the presentation (matplotlib mathtext, no LaTeX).
Output: results/figures/DSDR_equations.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY, INK, FILL, EDGE = "#1b3755", "#262d34", "#eef4f9", "#9db4cf"

BOXES = [
    ("1  Recloser operating time (forward fw and reverse rv)",
     [r"$t^{d}_{k,F} = TDS^{d}_{k,F}\,\left[\dfrac{A}{(I_{f}/I^{d}_{p,k})^{n}-1}+B\right]$",
      r"$t^{d}_{k,D} = TDS^{d}_{k,D}\,\left[\dfrac{A}{(I_{f}/I^{d}_{p,k})^{n}-1}+B\right]$",
      r"$d \in \{fw,\ rv\}$:  F = fast, D = delayed;  same curve, two time dials"]),
    ("2  Pickup and constraints",
     [r"$I^{fw}_{p,k} = OLF \times I^{fw}_{nom,k}$      $I^{rv}_{p,k} = OLF \times I^{rv}_{nom,k}$",
      r"$TDS_{min} < TDS^{d}_{k,F},\ TDS^{d}_{k,D} < TDS_{max}$",
      r"$I_{nom} < I_{p,k} < I_{f,min}$      (OLF = 1.25)"]),
    ("3  Fuse characteristic and coefficient",
     [r"$\log\,t_{fuse,i} = a_i \log I_{f,i} + b_i$      ($a_i = -1.8$)",
      r"$b_i = \log\left[\dfrac{t_{k,F}+t_{k,D}}{2}\right] - a_i \log I_{f,i}$      (single fuse)",
      r"$b_i = \log\left[t_{k,F}+\dfrac{i\,(t_{k,D}-t_{k,F})}{z+1}\right] - a_i \log I_{f,i}$      (z fuses in series)"]),
    ("4  Coordination conditions (fuse saving)",
     [r"$CTI = t_{MMT}(I_{fuse}) - t_{k,F}(I_{rec}) > 0$      fast trip first",
      r"$t_{TCT}(I_{fuse}) < t_{k,D}(I_{rec})$      fuse clears first",
      r"$t_{TCT,i} \leq 0.75\; t_{MMT,i+1}$      series fuses"]),
]


def main():
    fig = plt.figure(figsize=(13.0, 6.2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    pos = [(0.15, 3.2), (6.6, 3.2), (0.15, 0.1), (6.6, 0.1)]
    for (x, y), (title, lines) in zip(pos, BOXES):
        ax.add_patch(FancyBboxPatch((x, y), 6.25, 2.9, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=FILL, ec=EDGE, lw=1.2))
        ax.text(x + 0.2, y + 2.6, title, fontsize=13, fontweight="bold", color=NAVY, va="center")
        for j, ln in enumerate(lines):
            ax.text(x + 0.3, y + 1.9 - 0.75 * j, ln, fontsize=13.5 if (j < 2 or "dfrac" in ln) else 12, color=INK, va="center")
    out = os.path.join(HERE, "results", "figures", "DSDR_equations.png")
    fig.savefig(out, dpi=180, facecolor="white")
    plt.close(fig)
    print("written", out)


if __name__ == "__main__":
    main()
