"""
Read-aloud script for the final presentation: one block per slide with the slide picture, where to point,
and numbered paragraphs to read.  Writes DSDR_Presentation_Script.tex (compiled with pdflatex).

Slide pictures: defence/slides/sNN.png (exported from Presentation and report/DSDR_Final_Presentation.pptx).
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WPM = 125                     # reading speed used for the time estimate

# (slide number, title, [items]) ; an item is ("say", text) or ("point", text)
S = "say"
O = "optional"            # a paragraph that can be skipped when time is short
P = "point"
SLIDES = [
    (1, "Title", [
        (S, "Good afternoon. I am Jhala Nath Kafle, roll number 081 MSPSE 009. My project is an adaptive "
            "overcurrent protection scheme for dual-setting directional recloser and fuse coordination in "
            "distribution networks with distributed generation, on the IEEE 13-node feeder in PowerFactory."),
    ]),
    (2, "Presentation Outline", [
        (S, "I will cover the introduction, objectives, scope, methodology, results and conclusions."),
    ]),
    (3, "1. Introduction: Recloser-Fuse Coordination", [
        (P, "the graph on the right: fast curve below the green fuse band, dashed delayed curve above it"),
        (S, "In a fuse-saving scheme the recloser trips first on its fast curve, so a temporary fault clears "
            "and the fuse is saved. For a permanent fault, the delayed curve lets the fuse clear its lateral."),
        (S, "This works only while the recloser and the fuse carry the same current, and a DG changes both the "
            "size and the direction of the fault current."),
    ]),
    (4, "1. Introduction: Problem Statement", [
        (P, "the three boxes, left to right"),
        (S, "With a DG, the fuse carries grid plus DG current, while the recloser sees only the grid part, and "
            "a mid-line recloser can even see reverse current. The fuse may then melt before the fast trip."),
        (S, "The solution studied is the dual-setting directional recloser, or DSDR: the mid-line recloser R2 "
            "gets separate forward and reverse settings, chosen by the direction of the current."),
    ]),
    (5, "2. Objectives", [
        (S, "The general objective was to build and validate a PowerFactory implementation of the DSDR method "
            "on the IEEE 13-node feeder, with and without DG."),
        (S, "The seven specific objectives are: the model, load flow and short circuit, the settings, "
            "coordination without and with the DG, the dual setting of R2, a time-domain check, and the "
            "effect of DG penetration."),
    ]),
    (6, "3. Scope and Limitations", [
        (S, "The study covers four fault types at twelve locations, which gives 39 node and fault-type cells, "
            "plus one EMT simulation and a penetration study."),
        (P, "the right column, Limitations"),
        (S, "The limitations: some settings are not specified by the method and were defined here; the CDG34 "
            "relay model is not directional, so two relay units are used; a zero margin is used; and only one "
            "DG location is studied."),
    ]),
    (7, "4. Methodology: Coordination Method", [
        (P, "the flowchart on the right"),
        (S, "The method has three stages: A, the conventional design without DG; B, the same settings with "
            "the DG; and C, R2 as a DSDR. If coordination is lost, the time dial is revised first, and at "
            "the dial limit the fuse is made larger."),
    ]),
    (8, "4. Methodology: Mathematical Formulation", [
        (P, "the four boxes, 1 to 4"),
        (S, "These are the equations of the method: the recloser curve with a fast and a delayed time dial, "
            "the pickup from the load current, the fuse line on log-log axes, and the coordination "
            "conditions."),
    ]),
    (9, "4. Methodology: Operating Times from the Manufacturers' Curves", [
        (S, "The method writes the operating time as the time dial times a function of the current. I kept "
            "this structure and used the manufacturer's curve of each relay."),
        (P, "bottom right, How we know it is right"),
        (S, "It is checked twice: R1 reproduces the paper's worked example, and PowerFactory's own relay "
            "models confirm all 1896 times within 1.22 per cent."),
    ]),
    (10, "4. Methodology: Test System in PowerFactory", [
        (P, "the single-line diagram"),
        (S, "This is the PowerFactory model: a 4.16 kV feeder, a 4.05 MVA synchronous generator at node "
            "692, R1 at the feeder head, R2 on line 632 to 671, and fuses on the laterals."),
    ]),
    (11, "4. Methodology: Parameters of the Synchronous DG", [
        (S, "These are the parameters of the synchronous DG, 4.05 MVA, connected at node 692."),
    ]),
    (12, "4. Methodology: Protection Settings", [
        (P, "the table"),
        (S, "R1 has a pickup of 720 amperes. R2 forward uses plugs of 300 and 600 amperes, and the new "
            "reverse group 150 and 300 amperes."),
        (S, "The dials were already at their limits, so the fuse sizes were revised as shown."),
    ]),
    (13, "5. Results: Branch Currents and Fault Levels (DG out)", [
        (S, "The first result is the base case without DG: the rated current and the minimum and maximum "
            "fault current of each branch. The feeder head sees 4.73 kiloamperes."),
    ]),
    (14, "5. Results: Fuse Coefficients", [
        (S, "These are the fuse coefficients from the method's fuse equation, with the installed fuse and "
            "its melting time in the last columns."),
    ]),
    (15, "5. Results: Coordination Without DG", [
        (S, "Without DG, 35 of 39 cells were coordinated, and all 39 after one fuse change."),
        (P, "the left plot, then the right plot"),
        (S, "In both examples, R2's fast curve is below the fuses and its delayed curve is above them."),
    ]),
    (16, "5. Results: DG Connected, Conventional R2", [
        (P, "the red crosses in the chart"),
        (S, "With the DG and unchanged settings, coordination holds in only 24 of 39 cells. The fuse melts "
            "before the fast trip, and for some line-to-ground faults R2 does not even pick up the reverse "
            "current."),
    ]),
    (17, "5. Results: Conventional R2 with DG - Three Faults", [
        (P, "the right plot"),
        (S, "Three faults with the conventional settings. In the first two the recloser still trips first. "
            "For the three-phase fault close to 632, R2 trips in 0.121 seconds, but the fuse melts in 0.039 "
            "seconds: coordination is lost."),
    ]),
    (18, "5. Results: With the DSDR", [
        (P, "the chart: only one red cross is left"),
        (S, "With R2 as a DSDR and revised fuses, 38 of 39 cells are held under the zero-margin criterion. "
            "With the same revised fuses but a single-setting R2, only 31, so the dual setting itself "
            "restores seven cells."),
        (S, "The DSDR with the old fuses gives only 25, so it needs the fuse revision. Only the "
            "line-to-ground fault at 692 stays lost, limited by the maximum delayed dial of R2."),
    ]),
    (19, "5. Results: Bolted LL Fault at 646 with the DSDR", [
        (P, "the left plot for R2, the right plot for R1"),
        (S, "A bolted line-to-line fault at 646 with the DSDR. R2 trips in 0.086 seconds on its reverse "
            "group and R1 in 0.189 seconds. Both are before the fuse starts to melt at 0.415 seconds, so "
            "the fuse is saved."),
    ]),
    (20, "5. Results: Operating Times with the DSDR", [
        (S, "This table gives the operating times with the DSDR. In every row the fuse starts to melt after "
            "the last fast trip."),
    ]),
    (21, "5. Results: Single vs Dual Setting", [
        (P, "the table under the plots"),
        (S, "One case in detail: the three-phase fault near 632. With the single setting, R2 trips in 0.121 "
            "seconds, after the fuse starts melting: lost. With the reverse group, R2 trips in 0.052 "
            "seconds: held. Only the setting group changed."),
    ]),
    (22, "5. Results: Time-Sequence Check of All Faults", [
        (S, "As a second check I followed every fault in time. Above R2 the single setting holds 15 of 18 "
            "cells and the DSDR all 18. Below R2 the DG feeds the fault directly, so R2's setting makes no "
            "difference."),
    ]),
    (23, "5. Results: Time-Domain (EMT) Verification", [
        (P, "the upper waveform = without DG, the lower = with DG"),
        (S, "This EMT simulation is a line-to-line fault at 684. Without DG, the two fast shots use only 45 "
            "per cent of the fuse's melting heat, and the fuse then clears the permanent fault."),
        (S, "With the DG, current keeps flowing while R2 is open, and the fuse melts at 0.75 seconds, during "
            "the second fast shot."),
    ]),
    (24, "5. Results: Effect of the DG Penetration Level", [
        (P, "the ring chart"),
        (S, "Seven models with the DG from 0 to 100 per cent show the CTI falling: at 633 from plus 4 to "
            "minus 51 milliseconds, at 671 from 403 to 75 milliseconds."),
    ]),
    (25, "5. Results: Summary and Verification", [
        (P, "the table, top to bottom"),
        (S, "In summary: without DG, 35 cells and 39 after the fuse revision; 24 with the DG and a "
            "conventional R2; 25 with the DSDR alone, 31 with the fuse revision alone, and 38 with both."),
        (S, "These counts use a zero margin; with a three-cycle breaker time they become 31, and 26 with a "
            "fuse safety margin as well."),
    ]),
    (26, "6. Conclusions and Future Work", [
        (S, "To conclude: with the DG, a conventional R2 keeps only 24 of 39 cells. The combined DSDR and "
            "fuse revision raises this to 38 of 39, and the last cell is limited by R2's maximum delayed "
            "dial."),
        (S, "The DSDR alone gives only 25, so it is necessary but not sufficient, and faults below R2 remain "
            "a limit. Future work includes the 34-node feeder, a true directional element, practical margins "
            "and inverter-based DG."),
    ]),
    (27, "7. References", [
        (S, "These are the main references."),
    ]),
    (32, "Thank You", [
        (S, "Thank you for your attention. I am happy to take your questions."),
    ]),
]

APPENDIX = [
    (28, "Appendix: Comparison with the Reference Paper", [
        (S, "Compared with the reference paper, load currents agree within 2 per cent and the R1 worked "
            "example almost exactly. My fault levels are lower because I validated against the IEEE "
            "benchmark. The paper reports 30 and 39 coordinated cells, I obtained 24 and 38. The main finding "
            "is reproduced: the DSDR with the fuse revision restores the coordination between the grid and "
            "the DG."),
    ]),
    (29, "Appendix: Fault Levels - IEEE Benchmark, This Study and the Paper", [
        (S, "My fault levels are lower than the paper's, so I checked them against the IEEE short-circuit "
            "benchmark. My model agrees within 2 per cent at ten of eleven nodes. The paper's values are up "
            "to 151 per cent higher, and two of them exceed its own feeder-head value of 5.41 kiloamperes, "
            "which is not possible in a radial feeder without DG."),
    ]),
    (30, "Appendix: DSDR Operating Times - This Study and the Paper", [
        (S, "The operating times with the DSDR show the same behaviour as the paper: in every row the fuse "
            "melts after the fast trip of the recloser that protects it. R1's delayed time is twenty times "
            "the fast time in both, which confirms the dials. R2's settings are not published, so its times "
            "are compared in trend only."),
    ]),
    (31, "Appendix: CTI with DG Penetration - Study and Paper", [
        (S, "Both studies show the margin decreasing with DG penetration; where it turns negative depends on "
            "settings the paper does not publish."),
    ]),
]


def tex(s):
    for a, b in (("\\", r"\textbackslash "), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        s = s.replace(a, b)
    return s


def words(items, kinds=(S, O)):
    return sum(len(re.findall(r"[\w.']+", t)) for k, t in items if k in kinds)


def block(n, title, items):
    w = words(items)
    secs = int(round(w / WPM * 60 / 5.0) * 5)
    out = ["\\begin{slideblock}{%d}{%s}{%s}{s%02d.png}" % (n, tex(title), "%d s" % secs if secs < 60 else
                                                           "%d min %02d s" % (secs // 60, secs % 60), n)]
    k = 0
    for kind, text in items:
        if kind == P:
            out.append("\\point{%s}" % tex(text))
        else:
            k += 1
            out.append("\\%s{%d}{%s}" % ("say" if kind == S else "opt", k, tex(text)))
    out.append("\\end{slideblock}\n")
    return "\n".join(out), w


main_blocks, main_words, core_words = [], 0, 0
for n, title, items in SLIDES:
    b, w = block(n, title, items)
    main_blocks.append(b)
    main_words += w
    core_words += words(items, (S,))
app_blocks = [block(n, t, it)[0] for n, t, it in APPENDIX]
minutes = main_words / WPM

DOC = r"""\documentclass[12pt,a4paper]{article}
\usepackage[left=1.6cm,right=1.6cm,top=1.6cm,bottom=1.8cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{mathptmx}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{needspace}
\usepackage{fancyhdr}
\graphicspath{{slides/}}
\definecolor{navy}{HTML}{1B3755}
\definecolor{cue}{HTML}{8A4B08}
\definecolor{rule}{HTML}{C9CED6}
\definecolor{optc}{HTML}{5F6670}
\setlength{\parindent}{0pt}
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\fancyfoot[C]{\small\color{gray} Presentation script --- page \thepage}
% one slide: number, title, time, picture
\newenvironment{slideblock}[4]{\par\needspace{7.5cm}\vspace{4pt}
  {\color{navy}\rule{\linewidth}{1.2pt}}\par\vspace{3pt}
  \noindent\begin{minipage}[c]{0.60\linewidth}
    {\fontsize{22}{24}\selectfont\bfseries\color{navy} SLIDE #1}\par\vspace{3pt}
    {\large\bfseries #2}\par\vspace{3pt}
    {\small\color{gray} about #3 to read}
  \end{minipage}\hfill
  \begin{minipage}[c]{0.38\linewidth}\raggedleft
    \fcolorbox{rule}{white}{\includegraphics[width=0.94\linewidth]{#4}}
  \end{minipage}\par\vspace{8pt}}{\par\vspace{6pt}}
\newcommand{\say}[2]{\par\vspace{10pt}\noindent
  \begin{minipage}[t]{1.5cm}\fontsize{13.5}{19.5}\selectfont{\small\bfseries\color{navy} Para #1}\end{minipage}%
  \begin{minipage}[t]{\dimexpr\linewidth-1.5cm}\fontsize{13.5}{19.5}\selectfont\raggedright #2\end{minipage}\par}
\newcommand{\opt}[2]{\par\vspace{10pt}\noindent
  \begin{minipage}[t]{1.5cm}\fontsize{13.5}{19.5}\selectfont{\small\bfseries\color{gray} Para #1}\\[-6pt]{\scriptsize\color{gray} optional}\end{minipage}%
  \begin{minipage}[t]{\dimexpr\linewidth-1.5cm}\fontsize{13.5}{19.5}\selectfont\raggedright\color{optc} #2\end{minipage}\par}
\newcommand{\point}[1]{\par\vspace{10pt}\noindent\hspace{1.5cm}%
  \begin{minipage}[t]{\dimexpr\linewidth-1.5cm}\small\itshape\color{cue}$\triangleright$ Point to: #1\end{minipage}\par}

\begin{document}
\begin{center}
{\LARGE\bfseries\color{navy} Presentation Script}\\[4pt]
{\large Read-aloud text for every slide of \emph{DSDR\_Final\_Presentation.pptx}}\\[2pt]
Jhala Nath Kafle (081MSPSE009)
\end{center}
\vspace{2pt}
\fbox{\parbox{\dimexpr\linewidth-2\fboxsep-2\fboxrule}{\textbf{How to use this.}
Each block is one slide: the slide number, a small picture of the slide, and the paragraphs to read, numbered
\textbf{Para 1, Para 2, \dots} Read them in order, at a normal pace, and change the slide when the block ends.
The brown lines (\textit{\color{cue}$\triangleright$ Point to}) are not read: they say where to point on the
screen before the next paragraph.\par\smallskip
\textbf{Timing.} Slides 1 to 27 and the closing slide take about \textbf{MINUTES minutes} to read at a
calm speed (COREMIN words). The text is based on the speaker notes of the presentation, shortened a little
to fit 8 to 10 minutes.
\par\smallskip
\textbf{Numbers.} Read ``0.121'' as ``zero point one two one'', ``4.16 kV'' as ``four point one six
kilovolts'', ``400E'' as ``four hundred E'', and ``CTI'' as the three letters.}}
\vspace{4pt}

MAIN

\newpage
\begin{center}
{\Large\bfseries\color{navy} Appendix slides --- use only if you are asked}\\[3pt]
{\small Slides 28 to 31 come after the references. Do not present them; open one when a question needs it.}
\end{center}

APPENDIX
\end{document}
"""
doc = DOC.replace("MINUTES", "%.0f" % round(minutes)).replace("COREMIN", "%d" % main_words).replace("MAIN", "\n".join(main_blocks)) \
         .replace("APPENDIX", "\n".join(app_blocks))
open(os.path.join(HERE, "DSDR_Presentation_Script.tex"), "w", encoding="utf-8").write(doc)
print("main talk: %d words, about %.1f minutes at %d words per minute; without the optional paragraphs "
      "%d words, %.1f minutes" % (main_words, minutes, WPM, core_words, core_words / WPM))
