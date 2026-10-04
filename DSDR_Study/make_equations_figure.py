"""
Equation pictures for the presentation (matplotlib mathtext, no LaTeX):

  results/figures/DSDR_equations_method.png  the equations of the coordination method
  results/figures/DSDR_equations_impl.png    how the operating-time equation is implemented with the
                                             real relay curves (t = TDS x g(M))
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "figures")
NAVY, INK, FILL, EDGE, GREY = "#1b3755", "#262d34", "#eef4f9", "#9db4cf", "#6b727a"

METHOD = [
    ("1  Recloser operating time (forward fw, reverse rv)",
     [r"$t^{d}_{k,F} = TDS^{d}_{k,F}\,\left[\dfrac{A}{(I_{f}/I^{d}_{p,k})^{n}-1}+B\right]$",
      r"$t^{d}_{k,D} = TDS^{d}_{k,D}\,\left[\dfrac{A}{(I_{f}/I^{d}_{p,k})^{n}-1}+B\right]$",
      r"$d \in \{fw,\ rv\}$:  F = fast, D = delayed;  one curve, two time dials"]),
    ("2  Pickup and constraints",
     [r"$I^{fw}_{p,k} = OLF \times I^{fw}_{nom,k}$      $I^{rv}_{p,k} = OLF \times I^{rv}_{nom,k}$",
      r"$TDS_{min} < TDS^{d}_{k,F},\ TDS^{d}_{k,D} < TDS_{max}$",
      r"$I_{nom} < I_{p,k} < I_{f,min}$      (OLF = 1.25)"]),
    ("3  Fuse characteristic and coefficient",
     [r"$\log\,t_{fuse,i} = a_i \log I_{f,i} + b_i$      ($a_i = -1.8$)",
      r"$b_i = \log\left[\dfrac{t_{k,F}+t_{k,D}}{2}\right] - a_i \log I_{f,i}$      (single fuse)",
      r"$b_i = \log\left[t_{k,F}+\dfrac{i\,(t_{k,D}-t_{k,F})}{z+1}\right] - a_i \log I_{f,i}$   (z in series)"]),
    ("4  Coordination conditions (fuse saving)",
     [r"$CTI = t_{MMT}(I_{fuse}) - t_{k,F}(I_{rec}) > 0$      fast trip first",
      r"$t_{TCT}(I_{fuse}) < t_{k,D}(I_{rec})$      fuse clears first",
      r"$t_{TCT,i} \leq 0.75\; t_{MMT,i+1}$      series fuses"]),
]


def box(ax, x, y, w, h, title, lines, size=13.5, size2=12, dy=0.75):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=FILL, ec=EDGE, lw=1.2))
    ax.text(x + 0.2, y + h - 0.3, title, fontsize=13, fontweight="bold", color=NAVY, va="center")
    for j, ln in enumerate(lines):
        ax.text(x + 0.3, y + h - 1.0 - dy * j, ln, fontsize=size if j == 0 or "dfrac" in ln else size2,
                color=INK, va="center")


def method():
    fig = plt.figure(figsize=(13.0, 6.2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    for (x, y), (title, lines) in zip([(0.15, 3.2), (6.6, 3.2), (0.15, 0.1), (6.6, 0.1)], METHOD):
        box(ax, x, y, 6.25, 2.9, title, lines)
    fig.savefig(os.path.join(OUT, "DSDR_equations_method.png"), dpi=180, facecolor="white")
    plt.close(fig)


def impl():
    fig = plt.figure(figsize=(13.0, 4.3))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4.3)
    ax.axis("off")
    # bridge: the method's form and the general form it belongs to
    ax.add_patch(FancyBboxPatch((0.15, 3.05), 12.7, 1.1, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc="white", ec=NAVY, lw=1.5))
    ax.text(0.45, 3.6, r"Method:  $t = TDS\,\left[\dfrac{A}{M^{n}-1}+B\right]$", fontsize=15, color=INK, va="center")
    ax.text(5.55, 3.6, r"$\Longrightarrow$", fontsize=20, color=NAVY, va="center")
    ax.text(6.35, 3.6, r"in general:  $t = TDS \times g(M),\quad M = I_f / I_p$", fontsize=15, color=INK, va="center")
    ax.text(10.75, 3.6, "g(M) = the curve\nof the real relay", fontsize=12, color=GREY, va="center", style="italic")
    box(ax, 0.15, 0.1, 6.25, 2.75, "R1: GE IAC77B801A, extremely inverse",
        [r"$g(M) = A+\dfrac{B}{M-C}+\dfrac{D}{(M-C)^2}+\dfrac{E}{(M-C)^3}$",
         r"$A=0.004,\ B=0.6379,\ C=0.62,\ D=1.7872,\ E=0.2461$",
         r"GE Multilin manual;  $I_p$ = 720 A,  TDS 0.5 / 10"], dy=0.7)
    box(ax, 6.6, 0.1, 6.25, 2.75, "R2 (DSDR): GE/Alstom CDG34, extremely inverse",
        [r"$g(M) = t_1\left(\dfrac{t_2}{t_1}\right)^{f},\ \ f=\dfrac{\ln(M/M_1)}{\ln(M_2/M_1)}$",
         r"manufacturer table (PowerFactory library), $M = I_f/I_s$",
         r"fwd $I_s$ 300/600 A, rev 150/300 A;  TMS 0.1 / 1.0"], dy=0.7)
    fig.savefig(os.path.join(OUT, "DSDR_equations_impl.png"), dpi=180, facecolor="white")
    plt.close(fig)


def main():
    method()
    impl()
    print("written DSDR_equations_method.png, DSDR_equations_impl.png in", OUT)


if __name__ == "__main__":
    main()
