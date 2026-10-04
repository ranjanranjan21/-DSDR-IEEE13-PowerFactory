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
        (S, "Good afternoon, respected Head of the Department, respected coordinator, teachers and friends. "
            "My name is Jhala Nath Kafle, roll number 081 MSPSE 009."),
        (S, "My project is an adaptive overcurrent protection scheme for dual-setting directional recloser and "
            "fuse coordination in unbalanced distribution networks with distributed generation. In short: how to "
            "keep the recloser and the fuses of a feeder coordinated after a generator is connected to it."),
    ]),
    (2, "Presentation Outline", [
        (S, "This is the outline. I will start with the introduction and the problem, then the objectives and "
            "the scope. After that I explain the methodology, then the results, and I close with the "
            "conclusions and the references."),
        (O, "The comparison with the reference paper is kept in the appendix, after the last slide."),
    ]),
    (3, "1. Introduction: Recloser-Fuse Coordination", [
        (S, "Most faults on overhead distribution lines are temporary. In a fuse-saving scheme the recloser "
            "trips first, on its fast curve, so a temporary fault is cleared and the fuse is not lost. If the "
            "fault is permanent, the recloser moves to its delayed curve, and the fuse then clears only its "
            "own lateral."),
        (P, "the graph on the right: solid blue line = fast curve, green band = fuse, dashed blue = delayed curve"),
        (S, "On the graph, the fast curve of the recloser lies below the fuse band, and the delayed curve lies "
            "above it. Coordination exists only in the range of current between the two marked points."),
        (S, "This works only while the recloser and the fuse carry the same current. A distributed generator "
            "changes both the magnitude and the direction of the fault current, and that is where the problem "
            "starts."),
    ]),
    (4, "1. Introduction: Problem Statement", [
        (P, "the three boxes, from left to right"),
        (S, "Without DG, the fault current flows from the substation to the fault, so the recloser and the "
            "fuse see the same current. With a DG, the fuse carries the grid current plus the DG current, but "
            "the recloser carries only the grid share. A recloser in the middle of the line can even see "
            "current in the reverse direction."),
        (S, "The consequence is that the fuse can melt before the fast trip, and fuse saving is lost."),
        (S, "A single fixed setting cannot suit both the forward current from the grid and the reverse current "
            "from the DG. The solution studied here is the dual-setting directional recloser, in short DSDR. "
            "The mid-line recloser, R2, gets two independent groups of settings, one forward and one reverse, "
            "and the direction of the current selects the group."),
        (S, "In this project I implemented and tested this method on the IEEE 13-node feeder in DIgSILENT "
            "PowerFactory, with the manufacturers' characteristics of commercial relays and fuses."),
    ]),
    (5, "2. Objectives", [
        (S, "The general objective is to build and validate a PowerFactory implementation of the DSDR "
            "coordination method on the IEEE 13-node feeder, with and without distributed generation."),
        (S, "There are seven specific objectives. First, to build and verify the feeder model with its "
            "recloser and fuse protection. Second, to carry out unbalanced load-flow and short-circuit "
            "studies for all fault types. Third, to calculate the recloser pickups, the time dials and the "
            "fuse coefficients."),
        (S, "Fourth, to establish the coordination without DG, and then with a 4.05 MVA synchronous DG at node "
            "692. Fifth, to design the DSDR settings of R2 and classify the resulting coordination. Sixth, to "
            "verify the reclosing sequence in the time domain. And seventh, to study the effect of the DG "
            "penetration level."),
    ]),
    (6, "3. Scope and Limitations", [
        (P, "the left column, Scope"),
        (S, "The study covers the IEEE 13-node feeder at 4.16 kV, which is an unbalanced feeder. Four fault "
            "types are applied at twelve locations. Together this gives 39 combinations of node and fault "
            "type, which I call cells. The study also includes one EMT simulation of the reclosing sequence "
            "and a study of DG penetration from zero to 100 per cent."),
        (P, "the right column, Limitations"),
        (S, "There are four limitations. First, the method does not uniquely specify the settings of R2 or the "
            "fuse sizes, so these were defined in this study and documented. Second, the CDG34 relay model in "
            "the library is not directional, so the two setting groups are modelled as two relay units."),
        (O, "Third, the coordination is classified with a zero margin, and practical margins are evaluated "
            "separately. Fourth, only one DG location is studied, and the IEEE 34-node feeder is not "
            "modelled."),
    ]),
    (7, "4. Methodology: Coordination Method", [
        (P, "the flowchart on the right, top to bottom"),
        (S, "The method has three stages. Stage A is the conventional scheme without DG. The pickup of each "
            "recloser is 1.25 times the rated current of its branch, and the fuses are sized and checked."),
        (S, "Stage B keeps the same settings and connects the DG. All 39 cells are classified again. Stage C "
            "makes R2 a DSDR: the reverse pickup is taken from the reverse load current, and forward and "
            "reverse dials are set."),
        (S, "If coordination is lost, the time dial is revised first. If the dial is already at its limit, the "
            "fuse size is upgraded. The check is always the same: the fuse must not start to melt before the "
            "fast trip, and it must clear before the delayed trip."),
    ]),
    (8, "4. Methodology: Mathematical Formulation", [
        (P, "box 1, top left"),
        (S, "These are the equations of the method. Box one is the operating time of the recloser: one "
            "inverse-time curve, used with two time dials, one for the fast and one for the delayed "
            "operation, and written separately for the forward and the reverse direction."),
        (P, "box 2, top right"),
        (O, "Box two gives the pickup, which is the overload factor times the rated current, and the limits "
            "of the dial and of the pickup."),
        (P, "box 3, bottom left"),
        (S, "Box three is the fuse. On logarithmic axes the fuse curve is a straight line with slope a equal to "
            "minus 1.8. The coefficient b places the fuse between the fast and the delayed time of the "
            "recloser."),
        (P, "box 4, bottom right"),
        (S, "Box four gives the conditions for fuse saving. The coordination time interval, CTI, is the "
            "melting time of the fuse minus the fast time of the recloser, and it must be positive. The fuse "
            "must also clear before the delayed trip."),
    ]),
    (9, "4. Methodology: Operating Times from the Manufacturers' Curves", [
        (S, "The method writes the operating time as the time dial multiplied by a function of M, where M is "
            "the fault current divided by the pickup. The constants A, B and n describe only a generic "
            "curve."),
        (P, "the two blue boxes: R1 on the left, R2 on the right"),
        (S, "So I kept this structure, and used the manufacturer's curve of each relay. For R1 it is the GE "
            "IAC extremely inverse equation. For R2 it is the manufacturer's table of the CDG34 relay. The "
            "dial is called TDS for the IAC relay and TMS for the CDG34; both scale the curve in the same "
            "way."),
        (P, "bottom right, How we know it is right"),
        (O, "This was checked in two ways. R1 reproduces the worked example of the reference paper: 0.096 and "
            "1.926 seconds, against 0.097 and 1.932 seconds. And PowerFactory's own relay models confirm all "
            "1896 operating times within 1.22 per cent."),
    ]),
    (10, "4. Methodology: Test System in PowerFactory", [
        (P, "the single-line diagram on the left"),
        (S, "This is the model in PowerFactory. It is the IEEE 13-node feeder at 4.16 kV, supplied from a "
            "115 kV grid through a 5 MVA transformer."),
        (S, "The DG is a 4.05 MVA synchronous machine at node 692. R1 is a GE IAC relay at the head of the "
            "feeder. R2 is a CDG34 relay on the line from 632 to 671, and this is the recloser that becomes "
            "the DSDR. The laterals are protected by A055C fuses."),
        (O, "Unbalanced load flow, short-circuit and EMT studies were all carried out on this one model."),
    ]),
    (11, "4. Methodology: Parameters of the Synchronous DG", [
        (S, "These are the parameters of the synchronous DG. It is rated 4.05 MVA at 0.69 kV and is connected "
            "at node 692 through a step-up transformer of 0.69 to 4.16 kV."),
        (O, "It is modelled as a dynamic synchronous machine with its subtransient, transient and synchronous "
            "reactances, so its fault contribution is represented correctly. It operates at 3.24 megawatts."),
    ]),
    (12, "4. Methodology: Protection Settings", [
        (P, "the table, row by row"),
        (S, "These are the settings. R1 at the feeder head has a pickup of 720 amperes and time dials of 0.5 "
            "for the fast and 10 for the delayed operation. R2 forward uses plug settings of 300 and 600 "
            "amperes. The new reverse group of R2 uses 150 and 300 amperes."),
        (O, "With the DG connected, the load current through R2 reverses and becomes 252 amperes. With the "
            "overload factor this gives a reverse pickup of 315 amperes."),
        (S, "A revision of the dials could not help, because R1 and R2 are already at the ends of their dial "
            "ranges. So the fuse sizes were revised, which is step nine of the method, as listed in the last "
            "line."),
    ]),
    (13, "5. Results: Branch Currents and Fault Levels (DG out)", [
        (S, "Now the results. The first is the base case without DG."),
        (P, "the columns, from left to right"),
        (S, "For every protected branch the table gives the rated current from the load flow, the minimum "
            "fault current, and the maximum fault current. The minimum is a line-to-ground fault through "
            "3 ohms at the farthest node. The maximum is a bolted fault at the nearest node."),
        (O, "The feeder head carries 588 amperes of load, and its maximum fault current is 4.73 kiloamperes."),
    ]),
    (14, "5. Results: Fuse Coefficients", [
        (S, "This table gives the fuse coefficients from the equation of the method, with the slope a equal "
            "to minus 1.8."),
        (O, "For each fuse, the coefficient b follows from the fast and the delayed time of the recloser at "
            "the largest fault current below that fuse. The last two columns give the fuse that is actually "
            "installed and its melting time at the same current."),
    ]),
    (15, "5. Results: Coordination Without DG", [
        (S, "Without DG, the fault levels of the model agree with the IEEE benchmark within about 2 per cent. "
            "35 of the 39 cells are coordinated with the starting fuse sizes, and all 39 after one fuse is "
            "changed."),
        (P, "the left plot, then the right plot"),
        (S, "Two examples. On the left, a line-to-ground fault at node 611: R2 trips in 0.128 seconds, and the "
            "fuse would start to melt only at 0.271 seconds. On the right, a double line-to-ground fault "
            "between 692 and 675: R2 trips in 0.204 seconds, before the fuse melts at 0.331 seconds."),
        (O, "In both, the fast curve of R2 is below the fuses and its delayed curve is above them. So without "
            "DG the conventional scheme works."),
    ]),
    (16, "5. Results: DG Connected, Conventional R2", [
        (P, "the chart: green tick = coordination held, red cross = lost"),
        (S, "Now the DG is connected and the settings are not changed. Coordination holds in only 24 of the "
            "39 cells."),
        (S, "It is lost at nodes 633, 645, 646, the distributed load and 675. The reason is the one from the "
            "introduction: the fuse carries the grid and the DG current, and it melts before the fast trip. "
            "For some line-to-ground faults the single-setting R2 does not even pick up the reverse current "
            "from the DG."),
    ]),
    (17, "5. Results: Conventional R2 with DG - Three Faults", [
        (S, "These are three faults with the DG and the conventional settings."),
        (P, "the left plot, the middle plot, then the right plot"),
        (O, "On the left, a line-to-line fault at 646 through 1 ohm: R1 trips first, and coordination is "
            "held. In the middle, a line-to-line fault at 645: R2 carries 783 amperes in reverse and still "
            "trips first, so it is also held."),
        (S, "On the right, a three-phase fault close to node 632. R2 carries 1777 amperes in reverse and "
            "trips in 0.121 seconds. But the fuse F633 melts already at 0.039 seconds. The fuse melts first, "
            "and coordination is lost."),
    ]),
    (18, "5. Results: With the DSDR", [
        (P, "the chart: only one red cross is left"),
        (S, "Now R2 is a DSDR and the fuses are revised. Coordination is held in 38 of the 39 cells, under "
            "the zero-margin criterion."),
        (S, "With the same revised fuses but a single-setting R2, only 31 cells are held. So the dual setting "
            "itself restores seven cells: all the faults at 633, and the line-to-ground faults at 645, 646 "
            "and the distributed load. The DSDR with the old fuses gives only 25, so it needs the fuse "
            "revision."),
        (S, "One cell stays lost: the line-to-ground fault at 692. There the 400E fuse clears in 7.6 "
            "seconds, after R2's delayed trip at 4.0 seconds, and the delayed dial of R2 is already at its "
            "maximum."),
    ]),
    (19, "5. Results: Bolted LL Fault at 646 with the DSDR", [
        (S, "This is one fault in detail: a bolted line-to-line fault at 646, with the DSDR."),
        (P, "the left plot for R2, the right plot for R1"),
        (S, "The fuses carry 3.67 kiloamperes, which is the grid plus the DG current. R2 sees only the DG "
            "share, 1114 amperes in the reverse direction, and its reverse group trips in 0.086 seconds. R1 "
            "sees the grid share, 2785 amperes, and trips in 0.189 seconds."),
        (S, "Both reclosers trip before the fuse F646 starts to melt at 0.415 seconds. R2 removes the DG "
            "share and R1 removes the grid share, so the fuse is saved."),
    ]),
    (20, "5. Results: Operating Times with the DSDR", [
        (S, "This table gives the operating times with the DSDR and the DG in service, for a bolted fault at "
            "every node."),
        (P, "the R2 current column: rev for the upper rows, fwd for the lower rows"),
        (O, "R2 operates in the reverse direction for the nodes upstream of it, and in the forward direction "
            "for the nodes downstream."),
        (S, "In every row with a fuse, the fuse starts to melt after the last fast trip. The smallest margins "
            "are 6 milliseconds at node 675 and 15 milliseconds at the distributed load."),
    ]),
    (21, "5. Results: Single vs Dual Setting", [
        (S, "This slide compares the single setting and the dual setting on the same fault: the three-phase "
            "fault near node 632, with the revised fuses."),
        (P, "the table under the plots: middle column, then right column"),
        (S, "In both cases R2 carries 1777 amperes in reverse. With the single setting, R2 uses its forward "
            "plug and trips in 0.121 seconds, but the fuse starts to melt at 0.100 seconds: fuse saving is "
            "lost."),
        (S, "With the dual setting, R2 uses its reverse group and trips in 0.052 seconds, before the fuse: "
            "fuse saving is held. Only the setting group has changed."),
    ]),
    (22, "5. Results: Time-Sequence Check of All Faults", [
        (S, "As a second check, every fault was followed in time. The fuse heats while current flows, also "
            "after one recloser has opened."),
        (P, "the upper chart = single setting, the lower chart = DSDR"),
        (S, "For the 18 cells upstream of R2, the single setting holds 15, and the DSDR holds all 18. The "
            "three restored cells are the line-to-ground faults at 633, 645 and 646."),
        (O, "Downstream of R2 the DG feeds the fault directly, so the setting of R2 makes no difference "
            "there. This is a limit of the method."),
    ]),
    (23, "5. Results: Time-Domain (EMT) Verification", [
        (S, "This is the time-domain verification with an EMT simulation. The fault is line-to-line at node "
            "684 through 0.2 ohm, with the conventional settings."),
        (P, "the upper waveform = without DG, the lower waveform = with DG"),
        (S, "Without DG, R2 makes two fast shots. They use only 45 per cent of the fuse's melting heat, so "
            "the fuse survives. As the fault is permanent, the fuse then melts at 1.248 seconds and clears "
            "its lateral. This is the intended sequence."),
        (S, "With the DG, the fuse melts at 0.752 seconds, during the second fast shot. The fuse carries more "
            "current, and the DG keeps feeding the fault while R2 is open. Fuse saving is lost."),
    ]),
    (24, "5. Results: Effect of the DG Penetration Level", [
        (S, "The last result is the effect of the DG penetration level. Seven models were made, with the DG "
            "at 0, 10, 25, 37, 50, 75 and 100 per cent of 4.05 MVA. The settings of the design without DG "
            "were kept."),
        (P, "the ring chart: outer ring = node 671, inner ring = node 633"),
        (S, "The CTI is the melting time of the fuse minus the fast time of the recloser. At node 633 it "
            "falls from plus 4 milliseconds to minus 51 milliseconds. At node 671 it falls from plus 403 to "
            "plus 75 milliseconds."),
        (S, "The reason is that the fuse carries the grid and the DG current, while the recloser carries only "
            "the grid share. The fault level rises by up to 64 per cent, and above about 50 per cent "
            "penetration R2 stops detecting its weakest fault."),
    ]),
    (25, "5. Results: Summary and Verification", [
        (P, "the table, from the top row to the bottom row"),
        (S, "This table summarises the results. Without DG, 35 cells are held with the starting fuses and "
            "39 after the fuse revision. With the DG and a conventional R2, 24. With the DSDR alone, 25. "
            "With the fuse revision alone, 31. And with the DSDR and the fuse revision together, 38 of 39."),
        (S, "These counts use the zero-margin criterion. With a three-cycle breaker interrupting time, 31 "
            "cells are held, and with a fuse safety margin as well, 26."),
        (O, "As a verification, PowerFactory's own relay and fuse models reproduce the calculated operating "
            "times within 1.22 per cent, over 1896 operating times."),
    ]),
    (26, "6. Conclusions and Future Work", [
        (S, "To conclude. The DSDR method was implemented on the IEEE 13-node feeder in PowerFactory with "
            "manufacturer-based relay and fuse characteristics, and the model meets the IEEE benchmark within "
            "about 2 per cent."),
        (S, "With the DG, a conventional R2 keeps only 24 of 39 cells. The combined DSDR and fuse revision "
            "raises this to 38 of 39 under the zero-margin criterion. The remaining line-to-ground fault at "
            "692 is limited by the maximum delayed dial of R2."),
        (S, "The DSDR is necessary but not sufficient. Alone it gives only 25 cells; it needs the fuse "
            "revision, and faults downstream of R2 remain a limit. With practical margins the result becomes "
            "31 and 26 cells."),
        (P, "Future work, at the bottom"),
        (S, "For future work: the IEEE 34-node feeder, an explicit directional element for R2, practical "
            "margins, a change of setting group triggered by the state of the DG, inverter-based DG, and "
            "hardware-in-the-loop tests."),
    ]),
    (27, "7. References", [
        (S, "These are the main references. The method is from Yousaf and co-authors, published in 2022 in "
            "the IEEE Transactions on Industry Applications. The test feeder and its short-circuit benchmark "
            "are from Kersting."),
    ]),
    (32, "Thank You", [
        (S, "That completes my presentation. Thank you for your attention. I am happy to take your questions."),
    ]),
]

APPENDIX = [
    (28, "Appendix: Comparison with the Reference Paper", [
        (S, "This table compares my results with the reference paper. The rated branch currents agree within "
            "2 per cent, and the worked example of R1 agrees almost exactly."),
        (S, "My fault levels are lower: 4.73 kiloamperes at the feeder head against 5.41 in the paper, "
            "because I validated the model against the IEEE benchmark. With the DG and a conventional R2 the "
            "paper reports 30 coordinated cells and I obtained 24; 29 cells agree. With the DSDR the paper "
            "reports 39 and I obtained 38; the one cell is at the dial limit."),
        (S, "So the main finding is reproduced: the DSDR with the fuse revision restores the coordination "
            "between the grid and the DG."),
    ]),
    (29, "Appendix: Fault Levels - IEEE Benchmark, This Study and the Paper", [
        (S, "My fault levels are lower than the paper's, so I checked both against the IEEE short-circuit "
            "benchmark. My model agrees within 2 per cent at ten of the eleven nodes; the largest difference "
            "is 4.7 per cent at node 652."),
        (S, "The paper's values are 4 to 151 per cent higher than the benchmark. Two of them, 6.73 and 7.83 "
            "kiloamperes, are higher than the paper's own value at the feeder head, 5.41 kiloamperes. That is "
            "not possible in a radial feeder without DG. So I validated the model against the benchmark and "
            "did not tune it to the paper's table."),
    ]),
    (30, "Appendix: DSDR Operating Times - This Study and the Paper", [
        (S, "In this table each cell gives my value and then the paper's value. The behaviour is the same in "
            "both: in every row the fuse melts after the fast trip of the recloser that protects it."),
        (S, "For R1 the delayed time is twenty times the fast time in both studies, which confirms the dials "
            "of 0.5 and 10. The times differ because my fault levels are lower, so R1 is slower. The settings "
            "of R2 and the fuse sizes are not published in the paper, so those times are compared in trend "
            "only."),
    ]),
    (31, "Appendix: CTI with DG Penetration - Study and Paper", [
        (S, "The left ring is my study and the right ring is read from the paper's figure. Both show the CTI "
            "decreasing as the DG penetration rises."),
        (S, "The point where the sign changes depends on the starting margin, that is, on the fuse sizes and "
            "settings, which the paper does not publish. The central finding is the same in both."),
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
\newenvironment{slideblock}[4]{\par\needspace{11cm}\vspace{4pt}
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
\textbf{Timing.} Read everything: about \textbf{MINUTES minutes}. Skip every paragraph marked
\textit{optional} (printed in grey): about \textbf{COREMIN minutes}. Both are at a calm reading speed, for
slides 1 to 27 and the closing slide. The talk still makes sense without the optional paragraphs.
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
doc = DOC.replace("MINUTES", "%.0f" % round(minutes)).replace("COREMIN", "%.0f" % round(core_words / WPM)).replace("MAIN", "\n".join(main_blocks)) \
         .replace("APPENDIX", "\n".join(app_blocks))
open(os.path.join(HERE, "DSDR_Presentation_Script.tex"), "w", encoding="utf-8").write(doc)
print("main talk: %d words, about %.1f minutes at %d words per minute; without the optional paragraphs "
      "%d words, %.1f minutes" % (main_words, minutes, WPM, core_words, core_words / WPM))
