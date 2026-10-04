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
    ("1  R1: GE IAC77B801A, extremely inverse (GE Multilin)",
     [r"$t = TDS\left[A+\dfrac{B}{M-C}+\dfrac{D}{(M-C)^2}+\dfrac{E}{(M-C)^3}\right],\ \ M=\dfrac{I_f}{I_p}$",
      r"$A=0.004,\ B=0.6379,\ C=0.62,\ D=1.7872,\ E=0.2461$",
      r"$I_p = 720$ A;  $TDS$ = 0.5 (fast) / 10 (delayed)"]),
    ("2  R2 (DSDR): CDG34, extremely inverse (table)",
     [r"$t = t_1\left(\dfrac{t_2}{t_1}\right)^{f},\ \ f=\dfrac{\ln(M/M_1)}{\ln(M_2/M_1)},\ \ M=\dfrac{I_f}{I_s}$",
      r"table points $(M_1,t_1),(M_2,t_2)$; linear in TMS;  curve from $M = 2$",
      r"forward $I_s$ = 300 / 600 A,  reverse $I_s$ = 150 / 300 A;  TMS 0.1 / 1.0"]),
    ("3  Pickup, constraints and fuses",
     [r"$I^{d}_{p,k} = OLF \times I^{d}_{nom,k}$,  $d \in \{fw,rv\}$,  OLF = 1.25",
      r"$TDS_{min} < TDS_{F},\ TDS_{D} < TDS_{max}$;   $I_{nom} < I_{p} < I_{f,min}$",
      r"fuses: A055C library curves;  $b_i$ by eq. (9), $a=-1.8$"]),
    ("4  Coordination conditions (fuse saving)",
     [r"$CTI = t_{MMT}(I_{fuse}) - t_{F}(I_{rec}) > 0$      fast trip first",
      r"$t_{TCT}(I_{fuse}) < t_{D}(I_{rec})$      fuse clears first",
      r"$t_{TCT,i} \leq 0.75\; t_{MMT,i+1}$      series fuses"]),
]
NOTE = (r"The method's general form $t = TDS\,[A/(M^{n}-1)+B]$ is replaced by the real curves of the two relays "
        "(R1 by its equation, R2 by its table).")


def main():
    fig = plt.figure(figsize=(13.0, 6.6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.6)
    ax.axis("off")
    ax.text(6.5, 6.4, NOTE, fontsize=12, color="#6b727a", ha="center", va="center", style="italic")
    pos = [(0.15, 3.2), (6.6, 3.2), (0.15, 0.1), (6.6, 0.1)]
    for (x, y), (title, lines) in zip(pos, BOXES):
        ax.add_patch(FancyBboxPatch((x, y), 6.25, 2.9, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=FILL, ec=EDGE, lw=1.2))
        ax.text(x + 0.2, y + 2.6, title, fontsize=13, fontweight="bold", color=NAVY, va="center")
        for j, ln in enumerate(lines):
            ax.text(x + 0.3, y + 1.9 - 0.75 * j, ln, fontsize=13.5 if j == 0 else 12, color=INK, va="center")
    out = os.path.join(HERE, "results", "figures", "DSDR_equations.png")
    fig.savefig(out, dpi=180, facecolor="white")
    plt.close(fig)
    print("written", out)


if __name__ == "__main__":
    main()
