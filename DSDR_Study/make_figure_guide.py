"""
Figure guide: every figure of the report on its own page, with what it shows, how to read it and the point
to take away.  A study aid, separate from the report.

Uses the pictures in report/figures (written by make_report_latex.py) and compiles with TinyTeX.
Output: report/DSDR_Figure_Guide.pdf
"""

import os
import shutil
import subprocess
import tempfile


HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, "report", "figures")
OUT = os.path.join(HERE, "report", "DSDR_Figure_Guide.pdf")
PDFLATEX = os.path.join(os.environ.get("APPDATA", ""), "TinyTeX", "bin", "windows", "pdflatex.exe")

# (picture, title, what it shows, how to read it, key point)
GUIDE = [
    ("fig01.png", "Conventional recloser--fuse coordination",
     r"The fast and delayed curves of the feeder recloser R1 around the melting--clearing band of a fuse (F646).",
     r"Both axes are logarithmic: current on $x$, operating time on $y$. A curve lower down means a faster device. "
     r"The shaded band runs from the minimum-melting curve (fuse starts to melt) to the total-clearing curve "
     r"(fuse has cleared).",
     r"Fuse saving needs the fast recloser curve \emph{below} the band (recloser opens before the fuse melts, "
     r"a temporary fault can clear) and the delayed curve \emph{above} the band (the fuse clears a permanent fault "
     r"before the recloser locks out). The current range where both are true is the coordination range."),
    ("flowchart.png", "The coordination method with the DSDR",
     r"The design steps: load flow with the DG, placing the devices, the forward and reverse settings of the "
     r"DSDR, the fuse coefficients, the fault analysis and the coordination check.",
     r"Follow the arrows from Start. The two dashed panels are done side by side: one for the reverse "
     r"direction (DG current), one for the forward direction (grid current). The diamond is the test; the left "
     r"loop is the correction path.",
     r"If coordination is lost, first the recloser time dial is changed. Only when the dial is at its limit is "
     r"the fuse made larger. When every fault holds, the settings are valid for that DG size."),
    ("sld.png", "IEEE 13-node feeder with the protective devices",
     r"The test feeder with the substation recloser R1, the mid-feeder DSDR R2 between 632 and 671, the fuses "
     r"and the DG at node 692.",
     r"Line style tells the number of phases (solid three-phase, dotted two-phase, dash-dot single-phase). "
     r"Red squares are the protective devices with the fuse size of the final design.",
     r"R2 divides the feeder: nodes above R2 (632, 633, 645, 646, DL) are reached by the DG through R2 in the "
     r"reverse direction; nodes below R2 are fed by the DG directly."),
    ("fig08.png", "LG fault at 611, no DG",
     r"R2 (forward) with the series fuses F684 and F671-2 for a single-line-to-ground fault at 611.",
     r"The vertical line is the fault current through the devices. Read where it crosses each curve: that is "
     r"each device's operating time.",
     r"Without DG every device sees the same current, so the fixed curve order (R2 fast, fuses, R2 delayed) "
     r"guarantees coordination."),
    ("fig09.png", "LLG fault on line 692--675 through 1~$\Omega$, no DG",
     r"A second case of the design without DG, with a fault impedance.",
     r"Same reading as before. The fault impedance lowers the current, so the operating point moves left and up "
     r"on the curves.",
     r"R2's fast curve lies below the fuses and its delayed curve above them: coordination holds."),
    ("fig14.png", "Coordination status with DG, conventional R2",
     r"Every node and fault type (39 cells) with the DG of 4.05~MVA connected and the settings unchanged.",
     r"Green tick = coordination held, red cross = lost, dash = fault type not possible at that node.",
     r"The DG breaks coordination mainly above R2 (633, 645, 646, DL): the fuse carries grid + DG current and "
     r"melts before the recloser's fast trip, or R2 does not see the reverse current."),
    ("fig11.png", "LL fault at 646 through 1~$\Omega$, conventional settings",
     r"R1 with the fuses F646 and F632 for a line-to-line fault with the DG in service.",
     r"Compare the vertical lines: the fuse current is larger than the recloser current, because the fuse also "
     r"carries the DG share.",
     r"With different currents the curve order alone no longer decides; the fuse can melt first."),
    ("fig12.png", "LL fault at 645 through 1.5~$\Omega$, conventional R2",
     r"A further case where the DG changes the currents through R2 and the fuse.",
     r"Read the times where each vertical line meets its own device's curve.",
     r"The fixed forward setting of R2 is not designed for the reverse DG current."),
    ("fig13.png", "Three-phase fault at 10\,\% of line 632--633, conventional R2",
     r"A bolted three-phase fault close to 632 with the DG in service.",
     r"The fuse F633 operating point (squares) lies below the recloser fast point: the fuse would melt first.",
     r"This is the clearest example of the fuse-saving loss that the DSDR is meant to fix."),
    ("fig03.png", "The two setting groups of the DSDR",
     r"The reverse group (DG current, faults towards 632) and the forward group (grid current, faults beyond "
     r"671) of R2.",
     r"Each group has its own pickup and time multiplier. The reverse curves start at a lower current because "
     r"the DG contribution is smaller than the grid's.",
     r"The relay chooses the group from the direction of the current, so each direction gets a curve that fits "
     r"its own current level."),
    ("fig17.png", "Coordination status with DG and the DSDR",
     r"The same 39 cells as before, now with R2 as a DSDR and the revised fuse sizes.",
     r"Same symbols as the earlier status figure.",
     r"38 of 39 cells are held. Only the LG fault at 692 stays lost: the series fuse sizes needed there leave "
     r"no room within the dial range."),
    ("fig15.png", "Bolted LL fault at 646: R2 reverse setting",
     r"R2's reverse group against F646 and F632. The fuses carry 3.67~kA, R2 carries 1.11~kA in reverse.",
     r"R2 trips on its reverse fast curve in 0.086~s; F646 starts to melt only at 0.415~s.",
     r"With the reverse group R2 removes the DG current early, so the fuse survives the fast shot."),
    ("fig16.png", "Bolted LL fault at 646: R1",
     r"The feeder recloser R1 against the same two fuses for the same fault.",
     r"The grid current through R1 is read on R1's curves, the fuse current on the fuse band.",
     r"R1 removes the grid share and R2 the DG share: both sources are cut before the fuse melts."),
    ("case05.png", "Single against dual setting: three-phase fault near 632",
     r"The same fault and the same fuses with R2 as a single-setting relay (left) and as a DSDR (right).",
     r"The boxes in the corner give the result. Compare where the orange R2 fast curve meets R2's vertical line "
     r"in the two panels.",
     r"Single setting: R2 fast 0.121~s, F633 melts at 0.100~s, coordination lost. Dual setting: R2 fast "
     r"0.052~s, coordination held. Only the setting group changed."),
    ("case07.png", "Single against dual setting: LG fault at 646",
     r"A ground fault whose reverse DG current through R2 is below the forward pickup.",
     r"In the left panel R2's vertical line lies left of the start of its forward curve: R2 does not pick up.",
     r"The reverse group starts at a lower current, picks up and trips; the fuse is saved."),
    ("cd_sequence.png", "Time-sequence check",
     r"All 39 cells checked by following each fault in time (fuse heating accumulates while current flows), "
     r"for the single (S) and dual (D) setting side by side.",
     r"Left block: faults above R2; right block: faults below R2. Colour gives the outcome of each half-cell.",
     r"Above R2 the dual setting holds 18 of 18 against 15 of 18. The three restored cells are LG faults at "
     r"633, 645 and 646, where the single-setting R2 does not trip on the reverse current. Below R2 the DG feeds "
     r"the fault directly and the setting of R2 makes no difference."),
    ("fig10.png", "Time-domain verification (EMT)",
     r"The phase currents at node 632 for an LL fault at 684 through 0.2~$\Omega$, without DG (top) and with DG "
     r"(bottom), with the trip and reclose instants of R2.",
     r"Dotted lines mark the events. The grey trace is the current through the fuse F671-2.",
     r"Without DG the fuse survives both fast shots and then clears the permanent fault. With DG the fuse current "
     r"continues while R2 is open (the DG keeps feeding the fault), and F671-2 melts at the end of the second "
     r"fast shot."),
    ("pen_ring.png", "CTI against DG penetration",
     r"The coordination time interval CTI $= t_{MMT}(\mathrm{fuse}) - t_{fast}(\mathrm{recloser})$ at each "
     r"penetration level, as a share of the ring (outer ring node 671, inner ring node 633).",
     r"Each ring adds up to 100\,\% of the absolute CTI values. A negative share means the fuse melts before the "
     r"recloser's fast trip.",
     r"At 671 the CTI stays positive but shrinks as the DG grows; at 633 it is negative from low penetration "
     r"upward."),
    ("pen_currents.png", "Why the CTI falls with DG penetration",
     r"Fuse current (grid + DG share), recloser current (grid share), DG current and CTI against penetration.",
     r"Follow the fuse current up and the recloser current flat or slightly down.",
     r"The fuse sits between the fault and both sources, the recloser sees only the grid. A fuse curve is steep, "
     r"so its time drops much faster than the recloser's time rises: the CTI decreases."),
    ("pen_tcc.png", "TCC at all penetration levels",
     r"Fixed curves (settings unchanged) with the fuse operating points (squares) and recloser operating points "
     r"(circles) for every penetration level.",
     r"Colour gives the penetration level.",
     r"The recloser point hardly moves; the fuse point moves to higher current and shorter time with every step."),
    ("pen_tcc633.png", "Node 633 level by level",
     r"F633 and R1 at each penetration level, with the vertical short-circuit lines, operating times and CTI.",
     r"Each panel gives $t_{fast}$ of R1, $t_{MMT}$ of the fuse and the CTI arrow between them.",
     r"CTI goes from $+4$~ms without DG to $-51$~ms at 100\,\%: the margin at 633 is lost almost immediately."),
]


def build():
    head = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2cm]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{xcolor}
\usepackage[hidelinks]{hyperref}
\usepackage{parskip}
\graphicspath{{FIGDIR/}}
\definecolor{navy}{HTML}{1F3B5C}
\newcommand{\lab}[1]{\par\textbf{\color{navy}#1}\par\nopagebreak}
\begin{document}
\begin{center}
{\LARGE\bfseries Figure Guide}\\[4pt]
{\large Dual-Setting Directional Recloser and Fuse Coordination on the IEEE 13-Node Feeder}\\[10pt]
\end{center}
\section*{How to read a time--current characteristic (TCC)}
Most figures are TCC plots. Both axes are logarithmic: the current is on the horizontal axis and the
operating time on the vertical axis. Every device is a curve; a lower curve is a faster device. A vertical
line marks the fault current through a device, and the point where it meets the device's own curve is that
device's operating time. For fuse saving the recloser's fast curve must lie below the fuse's minimum-melting
curve at the fault current and its delayed curve above the fuse's total-clearing curve.

\textbf{Abbreviations.} R1 feeder recloser at the substation; R2 mid-feeder recloser between 632 and 671
(single setting or DSDR); DG distributed generator at 692 (4.05\,MVA at 100\,\%); LG, LL, LLG, LLL fault
types; $t_{MMT}$ minimum-melting time; CTI coordination time interval.

\tableofcontents
""".replace("FIGDIR", "figs")
    body = []
    for k, (pic, title, what, how, key) in enumerate(GUIDE, 1):
        body.append(r"""\clearpage
\section*{%d. %s}
\addcontentsline{toc}{section}{%d. %s}
\begin{center}\includegraphics[width=\textwidth,height=0.52\textheight,keepaspectratio]{%s}\end{center}
\lab{What it shows} %s

\lab{How to read it} %s

\lab{Key point} %s
""" % (k, title, k, title, pic, what, how, key))
    return head + "\n".join(body) + "\n\\end{document}\n"


def main():
    missing = [g[0] for g in GUIDE if not os.path.exists(os.path.join(FIGS, g[0]))]
    if missing:
        raise SystemExit("run make_report_latex.py first; missing: %s" % ", ".join(missing))
    pdflatex = PDFLATEX if os.path.exists(PDFLATEX) else "pdflatex"
    work = tempfile.mkdtemp(prefix="figguide_")
    shutil.copytree(FIGS, os.path.join(work, "figs"))
    open(os.path.join(work, "guide.tex"), "w", encoding="utf-8").write(build())
    for _ in range(2):
        p = subprocess.run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "guide.tex"], cwd=work,
                           capture_output=True, text=True, errors="replace")
        if p.returncode:
            print(p.stdout[-2500:])
            raise SystemExit("pdflatex failed")
    shutil.copy(os.path.join(work, "guide.pdf"), OUT)
    print("FIGURE GUIDE:", OUT)


if __name__ == "__main__":
    main()
