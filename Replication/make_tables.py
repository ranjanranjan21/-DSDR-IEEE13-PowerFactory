"""
Tables I-IV of the paper, replicated, into results/database/:

  Table_I_DG_parameters.csv        paper value against the value read back from the PowerFactory model
  Table_II_branch_currents.csv     Inom, If,min, If,max of every protected branch
  Table_III_fuse_coefficients.csv  b_i of eq. (9), with the installed fuse and its melting time
  Table_IV_operating_times.csv     recloser fast / delayed times AND fuse t_MMT / t_TCT, DSDR, DG in
  Tables_I_to_IV.txt               the four tables as text (also printed)

Needs: Table_I_model.json (step 1 or 2), Table_II/III/IV.csv and settings.json (step 3).  No PowerFactory.
"""

import csv
import json
import os

from protection_data import NODES

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
DB = os.path.join(RES, "database")
os.makedirs(DB, exist_ok=True)

# Table I of the paper (the last four rows are from the text of section IV-A)
PAPER_TABLE1 = [
    ("Leakage reactance", "Xl", "xl", 0.05, "pu"),
    ("Stator resistance", "Ra", "rstr", 0.0014, "pu"),
    ("d-axis synchronous reactance", "Xd", "xd", 1.4, "pu"),
    ("d-axis transient reactance", "X'd", "xds", 0.231, "pu"),
    ("d-axis subtransient reactance", "X''d", "xdss", 0.118, "pu"),
    ("d-axis transient open-circuit time constant", "T'd0", "tds0", 5.5, "s"),
    ("d-axis subtransient open-circuit time constant", "T''d0", "tdss0", 0.05, "s"),
    ("q-axis synchronous reactance", "Xq", "xq", 1.372, "pu"),
    ("q-axis transient reactance", "X'q", "xqs", 0.8, "pu"),
    ("q-axis subtransient reactance", "X''q", "xqss", 0.118, "pu"),
    ("q-axis transient open-circuit time constant", "T'q0", "tqs0", 1.25, "s"),
    ("q-axis subtransient open-circuit time constant", "T''q0", "tqss0", 0.19, "s"),
    ("Mechanical starting time", "M = 2H", "M", 1.5, "s"),
    ("DG rating", "Sn", "sgn", 4.05, "MVA"),
    ("DG voltage", "Un", "ugn", 0.69, "kV"),
    ("Step-up transformer, HV side", "U_HV", "tr_hv", 4.16, "kV"),
    ("Step-up transformer leakage reactance", "x_T", "x_T", 0.15, "pu"),
]

lines = []


def say(text=""):
    lines.append(text)
    print(text)


def read(name):
    return list(csv.DictReader(open(os.path.join(RES, name))))


def write(name, header, rows):
    path = os.path.join(DB, name)
    try:
        fh = open(path, "w", newline="")
    except PermissionError:                         # open in Excel
        path = path.replace(".csv", "_new.csv")
        fh = open(path, "w", newline="")
    with fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def text_table(header, rows):
    cells = [[str(c) for c in r] for r in [header] + rows]
    width = [max(len(r[k]) for r in cells) for k in range(len(header))]
    for n, r in enumerate(cells):
        say("  " + " | ".join(c.ljust(w) for c, w in zip(r, width)).rstrip())
        if n == 0:
            say("  " + "-+-".join("-" * w for w in width))


def dev(model, paper):
    try:
        return "%+.0f %%" % (100.0 * (float(model) - float(paper)) / float(paper))
    except (ValueError, ZeroDivisionError):
        return "---"


# ---- Table I --------------------------------------------------------------------------------
say("TABLE I - short-circuit parameters of the synchronous DG (paper against the PowerFactory model)")
path1 = os.path.join(RES, "Table_I_model.json")
if os.path.isfile(path1):
    M = json.load(open(path1))
    M["M"], M["x_T"] = 2 * M["h"], M["tr_uk"] / 100.0
    head = ["Parameter", "Symbol", "Paper", "Model", "Unit", "Match"]
    rows = []
    for name, sym, key, paper, unit in PAPER_TABLE1:
        model = M[key]
        rows.append([name, sym, "%g" % paper, "%g" % round(model, 4), unit, "yes" if abs(model - paper) <= 0.005 * paper else "NO"])
    rows.append(["DG connected at node", "", "692", M["node"], "", "yes" if M["node"] in ("692", "DG") else "NO"])
    rows.append(["Rotor model in PowerFactory", "", "X'q, T'q0 given", "round rotor" if M["iturbo"] else "salient pole", "",
                 "yes" if M["iturbo"] else "NO"])
    write("Table_I_DG_parameters.csv", head, rows)
    text_table(head, rows)
    say("  The DG terminal 'DG' (0.69 kV) is connected to node 692 through the 4.16/0.69 kV transformer.")
else:
    say("  Table_I_model.json not found: run step1_build_model.py or step2_studies.py first.")

# ---- Table II -------------------------------------------------------------------------------
say("\nTABLE II - rated, minimum and maximum fault current of the protected branches (DG out)")
t2 = read("Table_II.csv")
head = ["From", "To", "Inom (A)", "paper Inom (A)", "dev.", "If,min (kA)", "paper If,min (kA)", "dev.",
        "If,max (kA)", "paper If,max (kA)", "dev."]
rows = [[r["From"], r["To"], r["Inom (A)"], r["paper Inom (A)"], dev(r["Inom (A)"], r["paper Inom (A)"]),
         r["If,min (kA)"], r["paper If,min (kA)"], dev(r["If,min (kA)"], r["paper If,min (kA)"]),
         r["If,max (kA)"], r["paper If,max (kA)"], dev(r["If,max (kA)"], r["paper If,max (kA)"])] for r in t2]
write("Table_II_branch_currents.csv", head, rows)
text_table(head, rows)
say("  Inom: unbalanced load flow, largest phase.  If,min: LG through 3 ohm at the farthest node.  If,max: bolted fault")
say("  at the nearest node.  The model's fault levels are those of the IEEE benchmark; the paper's are higher.")

# ---- Table III ------------------------------------------------------------------------------
say("\nTABLE III - fuse coefficient b_i of eq. (9), a_i = -1.8, at the maximum fault current below the fuse (DG out)")
t3 = read("Table_III.csv")
head = ["Fuse", "If (A)", "i/z", "R fast (s)", "R delayed (s)", "t_fuse eq.(9) (s)", "b_i", "b_i (i from source)",
        "paper b_i", "Fuse (design without DG)", "t_MMT at If (s)", "t_TCT at If (s)", "b_i of installed fuse"]
rows = [[r["Fuse"], r["If (A)"], r["i/z"], r["t_fast (s)"], r["t_delayed (s)"], r["t_fuse eq.(9) (s)"],
         r["b_i (i=1 closest to fault, ref. [25])"], r["b_i (i counted from source)"], r["paper b_i"],
         r.get("installed fuse", ""), r.get("t_MMT of installed fuse at If (s)", ""),
         r.get("t_TCT of installed fuse at If (s)", ""), r["b_i of installed fuse at If"]] for r in t3]
write("Table_III_fuse_coefficients.csv", head, rows)
text_table(head, rows)
say("  t_fuse eq.(9) = t_F + i/(z+1) (t_D - t_F) is the melting time the method asks for; t_MMT is what the installed")
say("  fuse gives at the same current (read from its minimum-melting curve).  Sizes: design without DG; Table IV")
say("  uses the sizes after step 9 (DG in service, DSDR).")

# ---- Table IV -------------------------------------------------------------------------------
say("\nTABLE IV - operating times with the DSDR, DG in service (bolted LLL; LL at 2-phase, LG at 1-phase nodes)")
S = json.load(open(os.path.join(RES, "settings.json")))["dsdr"]
t4 = read("Table_IV.csv")
head = ["Node", "Fault", "I R1 (A)", "R1 fast (s)", "R1 delayed (s)", "I R2 (A)", "R2 dir.", "R2 fast (s)",
        "R2 delayed (s)", "Fuse", "Size", "I fuse (A)", "Fuse t_MMT (s)", "Fuse t_TCT (s)", "Last fast trip (s)",
        "Margin t_MMT - fast (s)", "Status"]
phead = ["Node", "R1 fast paper / model", "dev.", "R1 delayed paper / model", "dev.", "R2 fast paper / model", "dev.",
         "R2 delayed paper / model", "dev.", "Fuse t_MMT paper / model", "dev."]
rows, prow, full = [], [], []
for r in t4:
    has = r["fuse"] != "---"
    # the fuse must outlast the fast trip of every recloser that feeds the fault through it
    fast = [float(r["R2 fast (s)"])] if NODES[r["node"]]["zone"] == "R2" else [float(r["R1 fast (s)"]), float(r["R2 fast (s)"])]
    last = max(fast)
    size = S["fuses"][r["fuse"]].replace("A055C", "") if has else "---"
    margin = "%+.3f" % (float(r["fuse MMT (s)"]) - last) if has else "---"
    row = [r["node"], r["fault"], r["I R1 (A)"], r["R1 fast (s)"], r["R1 delayed (s)"], r["I R2 (A)"], r["R2 unit"],
           r["R2 fast (s)"], r["R2 delayed (s)"], r["fuse"], size, r["I fuse (A)"] or "---", r["fuse MMT (s)"],
           r["fuse TCT (s)"], "%.3f" % last, margin, r["status"]]
    rows.append(row)
    pr = [r["node"]]
    for a, b in (("paper R1 fast", "R1 fast (s)"), ("paper R1 delayed", "R1 delayed (s)"), ("paper R2 fast", "R2 fast (s)"),
                 ("paper R2 delayed", "R2 delayed (s)"), ("paper fuse MMT", "fuse MMT (s)")):
        pr += ["%s / %s" % (r[a], r[b]), dev(r[b], r[a])]
    prow.append(pr)
    full.append(row + [r["paper R1 fast"], r["paper R1 delayed"], r["paper R2 fast"], r["paper R2 delayed"], r["paper fuse MMT"]])
write("Table_IV_operating_times.csv", head + ["paper R1 fast (s)", "paper R1 delayed (s)", "paper R2 fast (s)",
                                              "paper R2 delayed (s)", "paper fuse t_MMT (s)"], full)
text_table(head, rows)
say("  Fuse: the fuse between the reclosers and the fault that is nearest to the fault; it carries the grid and the DG")
say("  share, so its current differs from the reclosers'.  t_MMT / t_TCT: minimum-melting / total-clearing time of that")
say("  fuse at its own current.  Last fast trip: R2 for faults below R2; the later of R1 and R2 (reverse) above R2.")
say("  Nodes 632, 671 and 680 are on the main feeder: no fuse between the reclosers and the fault.")
say("\n  Table IV against the paper (s)")
text_table(phead, prow)
say("  The paper prints no fuse sizes and no R2 settings, so its t_MMT cannot be reproduced exactly; the fuses here are")
say("  the ones chosen by the method's step 9 for the model's fault levels.")

out = os.path.join(DB, "Tables_I_to_IV.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("\nSaved: " + DB + "  (Table_I ... Table_IV csv, Tables_I_to_IV.txt)")
