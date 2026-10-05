"""
Writes the project report as LaTeX:  report/main.tex  (+ report/figures/), from report_template.tex.in.

The layout follows DSDR_Final_Project_Progress_Report (title page, abstract, lists, eight chapters,
references, appendices A-D).  Every table is filled from the result files of run_all.py, so the
numbers in the report are the numbers of the model.  Compile with pdfLaTeX (twice), e.g. on Overleaf:
upload the folder `report`.

Needs: results of run_all.py.  No PowerFactory, no LaTeX installation.
"""

import csv
import json
import os
import re
import shutil

from protection_data import FUSES, PAPER_TABLE4, NODES

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
DB = os.path.join(RES, "database")
OUT = os.path.join(HERE, "report")
FIGS = os.path.join(OUT, "figures")
os.makedirs(FIGS, exist_ok=True)


def read(path):
    return list(csv.DictReader(open(path)))


def tex(s):
    """escape a table cell"""
    s = str(s)
    for a, b in (("\\", r"\textbackslash "), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        s = s.replace(a, b)
    return s


def num(s):
    """signed number in math mode, so that the minus sign is a real minus"""
    s = str(s).strip()
    return "$%s$" % s if re.fullmatch(r"[+-]?\d+(\.\d+)?", s) else tex(s)


def rows(lines):
    return " \\\\\n".join(" & ".join(r) for r in lines) + " \\\\"


def dev(model, paper, nd=0):
    try:
        return "$%+.*f$" % (nd, 100.0 * (float(model) - float(paper)) / float(paper))
    except (ValueError, ZeroDivisionError):
        return "--"


S = json.load(open(os.path.join(RES, "settings.json")))
CONV, DSDR = S["conventional"], S["dsdr"]
size = lambda t: t.replace("A055C", "")

T = {}

# ---- Table I ----------------------------------------------------------------------------------
t1 = read(os.path.join(RES, "comparison", "Table_I_vs_paper.csv"))
sym = {"Xl": "$X_l$", "Ra": "$R_a$", "Xd": "$X_d$", "X'd": "$X'_d$", "X''d": "$X''_d$", "T'd0": "$T'_{d0}$",
       "T''d0": "$T''_{d0}$", "Xq": "$X_q$", "X'q": "$X'_q$", "X''q": "$X''_q$", "T'q0": "$T'_{q0}$",
       "T''q0": "$T''_{q0}$", "M = 2H": "$M = 2H$", "Sn": "$S_n$", "Un": "$U_n$", "U_HV": "$U_{HV}$", "x_T": "$x_T$"}
T["TABLE_I"] = rows([[tex(r["Parameter"]), sym.get(r["Symbol"], tex(r["Symbol"])), tex(r["Paper"]), tex(r["Model"]),
                      tex(r["Unit"]) or "--"] for r in t1 if r["Symbol"]])

# ---- voltages ---------------------------------------------------------------------------------
v = read(os.path.join(DB, "BusVoltage_comparison.csv"))
vb = {}
for r in v:
    vb.setdefault(r["Bus"], {})[r["Phase"]] = (r["V without DG (pu)"], r["V with DG (pu)"])
order = ["650", "RG60", "632", "633", "634", "645", "646", "DL", "671", "692", "675", "680", "684", "652", "611"]
T["TABLE_VOLT"] = rows([[b] + [vb[b].get(p, ("--", "--"))[0] for p in "ABC"] + [vb[b].get(p, ("--", "--"))[1] for p in "ABC"]
                        for b in order if b in vb])

# ---- reclosers in the load flow ---------------------------------------------------------------
lf = read(os.path.join(DB, "LoadFlow_comparison.csv"))
T["TABLE_LF"] = rows([[r["Device"], num(r["Without DG (A)"]), r["Direction without DG"], num(r["With DG (A)"]),
                       r["Direction with DG"]] for r in lf])

# ---- Table II ---------------------------------------------------------------------------------
t2 = read(os.path.join(RES, "comparison", "Table_II_vs_paper.csv"))
T["TABLE_II"] = rows([["%s--%s" % (r["From"], r["To"]) if r["To"] != "side" else tex(r["From"] + " side"),
                       r["Inom (A)"], r["paper Inom (A)"], dev(r["Inom (A)"], r["paper Inom (A)"], 1),
                       r["If,min (kA)"], r["paper If,min (kA)"], r["If,max (kA)"], r["paper If,max (kA)"],
                       dev(r["If,max (kA)"], r["paper If,max (kA)"])] for r in t2])

# ---- fault levels with and without DG ---------------------------------------------------------
fc = read(os.path.join(DB, "Comparison_fault_current.csv"))
T["TABLE_FAULT"] = rows([[r["Bus"], tex(r["Fault with DG"]), "%.0f" % float(r["If,max without DG (A)"]),
                          "%.0f" % float(r["If,max with DG (A)"]),
                          "$%+.0f$" % float(r["R1 without DG (A)"]), "$%+.0f$" % float(r["R1 with DG (A)"]),
                          "$%+.0f$" % float(r["R2 without DG (A)"]), "$%+.0f$" % float(r["R2 with DG (A)"])] for r in fc])

# ---- Table III --------------------------------------------------------------------------------
t3 = read(os.path.join(RES, "comparison", "Table_III_vs_paper.csv"))
T["TABLE_III"] = rows([[r["Fuse"], r["If (A)"], r["i/z"], "%.3f" % float(r["t_fast (s)"]), "%.3f" % float(r["t_delayed (s)"]),
                        "%.3f" % float(r["t_fuse eq.(9) (s)"]), "%.2f" % float(r["b_i (i=1 closest to fault, ref. [25])"]),
                        "%.2f" % float(r["b_i (i counted from source)"]), "%.2f" % float(r["paper b_i"]),
                        size(r["installed fuse"]), r["t_MMT of installed fuse at If (s)"]] for r in t3])

# ---- fuses ------------------------------------------------------------------------------------
WHERE = {"F632": "lateral 632--645, at 632", "F633": "lateral 632--633, at 632", "F634": "XFM-1, 0.48 kV side",
         "F645": "load at 645", "F646": "line 645--646, at 645", "F-DL": "distributed-load lateral on 632--671",
         "F671": "load at 671", "F671-1": "671--692 (switch), at 671", "F692": "load at 692", "F692-R": "cable 692--675, at 692",
         "F675": "load at 675", "F671-2": "lateral 671--684, at 671", "F684": "line 684--611, at 684", "F611": "load at 611",
         "F652": "cable 684--652, at 684"}
fr = []
for n, (_, start, src) in FUSES.items():
    a, b = size(CONV["fuses"][n]), size(DSDR["fuses"][n])
    source = tex(src.split(" (")[0]).replace("[8]", r"Benchmark scheme~\cite{yousaf2020},").replace("2022 ", r"Ref.~\cite{yousaf2022}, ")
    fr.append([n, WHERE[n], size(start), a, r"\textbf{%s}" % b if b != a else b, source])
T["TABLE_FUSES"] = rows(fr)

# ---- Table IV ---------------------------------------------------------------------------------
t4 = read(os.path.join(RES, "comparison", "Table_IV_vs_paper.csv"))
T["TABLE_IVA"] = rows([[r["node"], r["fault"], r["I R1 (A)"], "%s / %.3f" % (r["R1 fast (s)"], float(r["paper R1 fast"])),
                        "%s / %.3f" % (r["R1 delayed (s)"], float(r["paper R1 delayed"])), r["I R2 (A)"], r["R2 unit"],
                        "%s / %.3f" % (r["R2 fast (s)"], float(r["paper R2 fast"])),
                        "%s / %.3f" % (r["R2 delayed (s)"], float(r["paper R2 delayed"]))] for r in t4])
ivb = []
for r in t4:
    if r["fuse"] == "---":
        continue
    last = float(r["R2 fast (s)"]) if NODES[r["node"]]["zone"] == "R2" else max(float(r["R1 fast (s)"]), float(r["R2 fast (s)"]))
    ivb.append([r["node"], r["fault"], r["fuse"], size(DSDR["fuses"][r["fuse"]]), r["I fuse (A)"], r["fuse MMT (s)"],
                "%.3f" % PAPER_TABLE4[r["node"]][4], r["fuse TCT (s)"], "%.3f" % last,
                "$%+.3f$" % (float(r["fuse MMT (s)"]) - last), r["status"]])
T["TABLE_IVB"] = rows(ivb)

# ---- coordination grids -----------------------------------------------------------------------
cl = read(os.path.join(RES, "comparison", "Fig14_Fig17_vs_paper.csv"))
gn = ["632", "633", "645", "646", "DL", "671", "692", "675", "680", "684", "611", "652"]
cell = {"held": r"\ok", "lost": r"\no", "n/a": "--"}


def grid(columns):
    out = []
    for ft in ("LG", "LL", "LLG", "LLL"):
        for label, col in columns:
            d = {r["node"]: r[col] for r in cl if r["fault"] == ft}
            out.append(["%s%s" % (ft, label)] + [cell[d[n]] for n in gn])
    return rows(out)


T["GRID_HEAD"] = " & ".join(gn)
T["GRID14"] = grid([(" (model)", "Fig14 model"), (" (paper)", "Fig14 paper")])
T["GRID17"] = grid([(", single setting", "final fuses, conventional R2"), (", dual setting", "Fig17 model")])
count = lambda col, val: sum(r[col] == val for r in cl)
T["N_CELLS"] = str(count("Fig14 model", "held") + count("Fig14 model", "lost"))
T["N14_HELD"] = str(count("Fig14 model", "held"))
T["N14_AGREE"] = str(sum(r["Fig14 model"] == r["Fig14 paper"] for r in cl if r["Fig14 model"] != "n/a"))
T["N17_HELD"] = str(count("Fig17 model", "held"))
T["N17_SINGLE"] = str(count("final fuses, conventional R2", "held"))

# ---- single against dual setting, nine faults -------------------------------------------------
ft = read(os.path.join(RES, "coordination_diagrams", "Fault_table.csv"))
first = lambda s: s.split(" / ")[0].replace(" s", "")
ca = []
for r in ft:
    fuse, times = r["Primary fuse melts / clears"].split(": ")
    ca.append([r["Case"], tex(r["Figure"]), tex(r["Fault"]), r["Zf (ohm)"], r["I R1 (A)"],
               "%s (%s)" % (r["I R2 (A)"], "fwd" if r["R2 direction"].startswith("for") else "rev"), first(r["R1 fast / delayed"]),
               first(r["R2 fast / delayed, single setting"]), first(r["R2 fast / delayed, dual setting"]),
               "%s: %s" % (fuse, first(times)), r["Fuse saving, single setting"].lower(), r["Fuse saving, dual setting"].lower()])
T["TABLE_CASES"] = rows(ca)


def case_rows(cid):
    """quantity / single setting / dual setting of one case, for the table under its TCC figure"""
    out = []
    for r in read(os.path.join(RES, "coordination_diagrams", "Case_%s_table.csv" % cid)):
        cells = [tex(r[k]).replace("->", r"$\rightarrow$").replace(" ohm", r"\ohm{}").replace("Zf", "$Z_f$")
                 for k in ("Quantity", "Single setting", "Dual setting (DSDR)")]
        if cells[2] == "same":
            cells = [cells[0], r"\multicolumn{2}{l}{%s}" % cells[1]]
        out.append(cells)
    return rows(out)


T["CASE05_TABLE"] = case_rows("05")

# ---- fault levels against the IEEE short-circuit benchmark (Appendix) -----------------------
_fb = read(os.path.join(RES, "Fault_level_benchmark.csv"))
T["TABLE_BENCH"] = rows([[r["Node"], "%.2f" % float(r["IEEE benchmark (kA)"]), "%.2f" % float(r["This study (kA)"]),
                          "$%+.1f$" % float(r["Study vs benchmark (%)"]),
                          "%.2f" % float(r["Paper Table II If,max of the branch (kA)"]),
                          "$%+.1f$" % float(r["Paper vs benchmark (%)"])] for r in _fb])
_dev = [abs(float(r["Study vs benchmark (%)"])) for r in _fb]
T["BENCH_N2"] = str(sum(d <= 2.0 for d in _dev))
T["BENCH_N"] = str(len(_dev))
T["BENCH_MAX"] = "%.1f" % max(_dev)
T["CASE07_TABLE"] = case_rows("07")

# ---- Fig. 10 ----------------------------------------------------------------------------------
f10 = json.load(open(os.path.join(RES, "Fig10_summary.json")))
ev = lambda tag, k: "%.3f" % f10[tag]["events"][k][0]
emt_rows = [
    ["Fault initiated", "0.30", "%.2f" % f10["DG out"]["t_fault"], "%.2f" % f10["DG in"]["t_fault"]],
    ["R2 fast trip 1", r"$\approx$0.46", ev("DG out", 0), ev("DG in", 0)],
    ["R2 reclose 1", r"$\approx$0.65", ev("DG out", 1), ev("DG in", 1)],
    ["R2 fast trip 2", r"$\approx$0.80", ev("DG out", 2), ev("DG in", 2)],
    ["R2 reclose 2", r"$\approx$1.00", ev("DG out", 3), ev("DG in", 3)],
    ["Fuse F671-2 melts", "--", "%.3f" % f10["DG out"]["t_melt"], "%.3f" % f10["DG in"]["t_melt"]],
    ["Fuse operation / clears", "1.21", "%.3f" % f10["DG out"]["t_clear"], "%.3f" % f10["DG in"]["t_clear"]],
    ["Fuse heat after the fast shots", "--", r"%.0f\,\%%" % (100 * f10["DG out"]["heat_after_fast_shots"]),
     r"%.0f\,\%%" % (100 * f10["DG in"]["heat_after_fast_shots"])],
]
T["TABLE_EMT"] = rows(emt_rows)
n = f10["DG out"]["node632"]
T["EMT_PRE"] = "%.0f / %.0f" % (n["prefault_rms_a"], n["prefault_rms_c"])
T["EMT_RMS"] = "%.0f / %.0f" % (n["fault_rms_a"], n["fault_rms_c"])
T["EMT_PEAK"] = "%.0f / %.0f" % (n["steady_peak_a"], n["steady_peak_c"])

# ---- appendix D: the Python scripts of the study -----------------------------------------------
SCRIPTS = [("show_progress.py", "Script of the PowerFactory script object Final(1): runs the load flows, the "
                                "short-circuit database and the coordination study, and prints the report in the Output Window"),
           ("pf_setup.py", "Connection to PowerFactory and helper functions"),
           ("protection_data.py", "Feeder, device and fault data"),
           ("curves.py", "Relay and fuse time--current curves"),
           ("step1_build_model.py", "Builds the protection devices and the DG in the model"),
           ("step2_studies.py", "Unbalanced load flow and short-circuit studies"),
           ("step3_design_and_evaluate.py", "Settings, fuse coefficients and classification of the coordination"),
           ("step4_apply_settings.py", "Writes the settings into the relay and fuse elements of the model"),
           ("step5_fig10_emt.py", "EMT simulation of the reclosing sequence")]
ASCII = {"\u2013": "-", "\u2212": "-", "\u2713": "held", "\u2717": "lost", "\u00d7": "x", "\u03a9": "ohm",
         "\u2192": "->", "\u00b0": "deg", "\u2264": "<=", "\u2265": ">="}
parts, tab = [], []
for name, purpose in SCRIPTS:
    code = open(os.path.join(HERE, name), encoding="utf-8").read().replace("\r\n", "\n").replace("\t", "    ")
    for a, b in ASCII.items():
        code = code.replace(a, b)
    code = code.encode("ascii", "replace").decode()              # pdflatex listings: ASCII only
    assert "\\end{lstlisting}" not in code and "<<" not in code, name
    tex_name = name.replace("_", "\\_")
    tab.append("\\texttt{%s} & %s \\\\ \\hline" % (tex_name, purpose))
    parts.append("\\subsection*{C.%d\\quad \\texttt{%s}}\n%s.\n\\begin{lstlisting}\n%s\n\\end{lstlisting}\n" % (
        len(parts) + 1, tex_name, purpose, code.rstrip()))
T["SCRIPT_TABLE"] = "\n".join(tab)
T["SCRIPT_LISTINGS"] = "\n".join(parts)

# ---- the study's own tables (chapters 4 and 5); the *_vs_paper versions above are for Appendix C -------------
t1o = read(os.path.join(DB, "Table_I_DG_parameters.csv"))
T["TABLE_I_OWN"] = rows([[tex(r["Parameter"]), sym.get(r["Symbol"], tex(r["Symbol"])), tex(r["Value"]), tex(r["Unit"]) or "--"]
                         for r in t1o if r["Symbol"]])
T["TABLE_II_OWN"] = rows([["%s--%s" % (r["From"], r["To"]) if r["To"] != "side" else tex(r["From"] + " side"),
                           r["Inom (A)"], r["If,min (kA)"], r["If,max (kA)"]] for r in read(os.path.join(RES, "Table_II.csv"))])
T["TABLE_III_OWN"] = rows([[r["Fuse"], r["If (A)"], r["i/z"], "%.3f" % float(r["t_fast (s)"]), "%.3f" % float(r["t_delayed (s)"]),
                            "%.3f" % float(r["t_fuse eq.(9) (s)"]), "%.2f" % float(r["b_i (eq. 9, i=1 closest to fault)"]),
                            size(r["installed fuse"]), r["t_MMT of installed fuse at If (s)"]]
                           for r in read(os.path.join(RES, "Table_III.csv"))])
T["TABLE_IVA_OWN"] = rows([[r["node"], r["fault"], r["I R1 (A)"], r["R1 fast (s)"], r["R1 delayed (s)"], r["I R2 (A)"], r["R2 unit"],
                            r["R2 fast (s)"], r["R2 delayed (s)"]] for r in t4])
T["TABLE_IVB_OWN"] = rows([row[:6] + row[7:] for row in ivb])
T["GRID14_OWN"] = grid([("", "Fig14 model")])
T["TABLE_EMT_OWN"] = rows([[r[0]] + r[2:] for r in emt_rows])

# ---- DG penetration study (Penetration_Study/) ---------------------------------------------------------
PEN = os.path.join(os.path.dirname(HERE), "Penetration_Study")
PD = {int(k): v for k, v in json.load(open(os.path.join(PEN, "results", "penetration_results.json"))).items()}
PL = sorted(PD)
pf = lambda p, k: PD[p]["faults"][k]
cti = {n: [pf(p, k)["CTI_s"] for p in PL] for n, k in (("633", "633 LLL"), ("671", "671 LL"))}
ring = {n: [100.0 * c / sum(abs(x) for x in v) for c in v] for n, v in cti.items()}
T["PEN_CTI"] = rows([["%d" % p, "%.2f" % PD[p]["loadflow"]["dg_rating_MVA"],
                      "%.0f / %.0f" % (pf(p, "633 LLL")["I_fuse"], pf(p, "633 LLL")["I_R1"]),
                      "%.3f / %.3f" % (pf(p, "633 LLL")["t_fuse_MMT"], pf(p, "633 LLL")["t_rec_fast"]),
                      "$%+.0f$" % (1000 * cti["633"][k]), "$%+.1f$" % ring["633"][k],
                      "%.0f / %.0f" % (pf(p, "671 LL")["I_fuse"], pf(p, "671 LL")["I_R2"]),
                      "%.3f / %.3f" % (pf(p, "671 LL")["t_fuse_MMT"], pf(p, "671 LL")["t_rec_fast"]),
                      "$%+.0f$" % (1000 * cti["671"][k]), "$%+.1f$" % ring["671"][k]] for k, p in enumerate(PL)])
lf = {p: PD[p]["loadflow"] for p in PL}
pk = {int(r["DG penetration %"]): r for r in read(os.path.join(PEN, "results", "Pickup_vs_penetration.csv"))}
mn = {int(r["DG penetration %"]): r for r in read(os.path.join(PEN, "results", "Ifmin_vs_pickup.csv"))}
T["PEN_LF"] = rows([["%d" % p, "%.2f" % lf[p]["dg_P_MW"], "%.1f" % lf[p]["R1_A"], "%.1f" % lf[p]["R2_A"],
                     tex(pk[p]["R2 load direction"]), "%.3f" % lf[p]["V"]["671"][0], "%.1f" % float(pk[p]["R1 Ip = 1.25 Inom (A)"]),
                     "%.1f" % float(pk[p]["R2 Ip = 1.25 Inom (A)"]),
                     "%.0f%s" % (float(mn[p]["lowest R1 current, LG 3 ohm (A)"]), "" if mn[p]["R1 sees it?"] == "yes" else r"$^\ast$"),
                     "%.0f%s" % (float(mn[p]["lowest R2 current in its zone, LG 3 ohm (A)"]), "" if mn[p]["R2 sees it?"] == "yes" else r"$^\ast$")]
                    for p in PL])
sc = read(os.path.join(PEN, "results", "SC_levels_vs_penetration.csv"))
T["PEN_SC"] = rows([[r["Node"], tex(r["Fault (largest)"]), r["If,max 0 % (A)"], r["If,max 25 % (A)"], r["If,max 50 % (A)"],
                     r["If,max 75 % (A)"], r["If,max 100 % (A)"], "$%s$" % r["change 0 -> 100 %"].replace(" %", r"\,\%")] for r in sc])
pc = read(os.path.join(PEN, "comparison", "Penetration_CTI_vs_paper.csv"))
T["PEN_VS_PAPER"] = rows([[r["DG penetration %"], "$%s$" % r["633 CTI ring % (model)"], "$%+d$" % int(r["633 paper %"]),
                           "$%s$" % r["671 CTI ring % (model)"], "$%+d$" % int(r["671 paper %"])] for r in pc])
f0, f100 = pf(0, "633 LLL"), pf(100, "633 LLL")
g0, g100 = pf(0, "671 LL"), pf(100, "671 LL")
T["PEN_633_TXT"] = ("the fuse current rises from %.0f\\,A to %.0f\\,A while R1's current falls from %.0f\\,A to %.0f\\,A; "
                    "the CTI falls from $%+.0f$\\,ms to $%+.0f$\\,ms" % (f0["I_fuse"], f100["I_fuse"], f0["I_R1"], f100["I_R1"],
                                                                     1000 * f0["CTI_s"], 1000 * f100["CTI_s"]))
T["PEN_671_TXT"] = ("the fuse current rises from %.0f\\,A to %.0f\\,A while R2's current stays at about %.0f\\,A; "
                    "the CTI falls from $%+.0f$\\,ms to $%+.0f$\\,ms" % (g0["I_fuse"], g100["I_fuse"], g100["I_R2"],
                                                                     1000 * g0["CTI_s"], 1000 * g100["CTI_s"]))
PFIGS = {"pen_ring.png": ("results", "Fig07_penetration.png"), "pen_currents.png": ("results", "Fig07_penetration_currents.png"),
         "pen_tcc.png": ("results", "TCC_penetration_overview.png"), "pen_tcc633.png": ("results", "TCC_penetration_633.png"),
         "pen_ring_vs_paper.png": ("comparison", "Fig07_penetration_vs_paper.png")}
for dst, (sub, src) in PFIGS.items():
    shutil.copyfile(os.path.join(PEN, sub, src), os.path.join(FIGS, dst))

# ---- figures ----------------------------------------------------------------------------------
F = os.path.join(RES, "figures")
C = os.path.join(RES, "coordination_diagrams")
COPY = {"flowchart.png": (F, "Fig05_method_flowchart.png"), "sld.png": (F, "Fig06_IEEE13_with_devices.png"),
        "fig01.png": (F, "Fig01_conventional_TCC.png"), "fig03.png": (F, "Fig03_DSDR_TCC.png"),
        "fig08.png": (F, "Fig08_LG_611.png"), "fig09.png": (F, "Fig09_LLG_692-675.png"),
        "fig10.png": (F, "Fig10_EMT_LL_684.png"), "fig11.png": (F, "Fig11_LL_646_R1.png"),
        "fig12.png": (F, "Fig12_LL_645_conventional_R2.png"), "fig13.png": (F, "Fig13_LLL_632-633_conventional_R2.png"),
        "fig14.png": (F, "Fig14_without_DSDR.png"), "fig15.png": (F, "Fig15_LL_646_DSDR.png"),
        "fig16.png": (F, "Fig16_LL_646_R1.png"), "fig17.png": (F, "Fig17_with_DSDR.png"),
        "cd_summary.png": (C, "00_Summary.png"), "cd_sequence.png": (C, "10_Sequence_check.png"),
        "case05.png": (C, "Case_05_3-phase_fault_at_10_pct_of_632-633.png"),
        "case07.png": (C, "Case_07_LG_fault_at_646_phase_c.png")}
for dst, (folder, src) in COPY.items():
    shutil.copyfile(os.path.join(folder, src), os.path.join(FIGS, dst))

# all pictures in one PDF, one per page: a single file to upload to Overleaf
import fitz
PICS = sorted(f for f in os.listdir(FIGS) if f.endswith(".png"))
doc = fitz.open()
for f in PICS:
    img = fitz.open(os.path.join(FIGS, f))
    rect = img[0].rect
    page = doc.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, filename=os.path.join(FIGS, f))
doc.save(os.path.join(OUT, "report_pictures.pdf"), deflate=True)
T["PICTURE_PAGES"] = "\n".join(r"\expandafter\def\csname pic@%s\endcsname{%d}" % (f, k) for k, f in enumerate(PICS, 1))

template = open(os.path.join(HERE, "report_template.tex.in"), encoding="utf-8").read()
for k, val in T.items():
    assert "<<%s>>" % k in template, k
    template = template.replace("<<%s>>" % k, val)
left = re.findall(r"<<[A-Z0-9_]+>>", template)
assert not left, left
from table_style import excel_tables             # spreadsheet-style tables (all cells framed)
template = excel_tables(template)
with open(os.path.join(OUT, "main.tex"), "w", encoding="utf-8") as fh:
    fh.write(template.replace("3-phase fault", "Three-phase fault"))
print("written", os.path.join(OUT, "main.tex"), "(%d lines)" % template.count("\n"))
print("figures:", ", ".join(sorted(os.listdir(FIGS))))

# one file to upload to Overleaf (New Project -> Upload Project): main.tex and the figures folder
import zipfile
ZIP = os.path.join(HERE, "report_overleaf.zip")
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(OUT, "main.tex"), "main.tex")
    for f in sorted(os.listdir(FIGS)):
        z.write(os.path.join(FIGS, f), "figures/" + f)
print("zip for Overleaf:", ZIP)
# the same files in one flat folder: select all and drag into Overleaf's upload box
FLAT = os.path.join(os.path.dirname(HERE), "UPLOAD_TO_OVERLEAF")
os.makedirs(FLAT, exist_ok=True)
for f in os.listdir(FLAT):
    os.remove(os.path.join(FLAT, f))
shutil.copyfile(os.path.join(OUT, "main.tex"), os.path.join(FLAT, "main.tex"))
shutil.copyfile(os.path.join(OUT, "report_pictures.pdf"), os.path.join(FLAT, "report_pictures.pdf"))
for f in os.listdir(FIGS):
    shutil.copyfile(os.path.join(FIGS, f), os.path.join(FLAT, f))
print("flat upload folder:", FLAT)
