# Dual-Setting Directional Recloser and Fuse Coordination in Unbalanced Distribution Networks With Distributed Generation

> M. Yousaf, A. Jalilian, K. M. Muttaqi, D. Sutanto, "An Adaptive Overcurrent Protection Scheme for
> Dual-Setting Directional Recloser and Fuse Coordination in Unbalanced Distribution Networks With
> Distributed Generation," *IEEE Trans. Ind. Appl.*, 58(2), 1831–1842, 2022.

A fresh, fully scripted replication in DIgSILENT PowerFactory 2021 SP2. Every table and figure of
the IEEE 13-node part (Tables I–IV, Figs. 1–6 and 8–17, including the time-domain Fig. 10) is regenerated
from the model by one command. The earlier scripts in the parent folder are not used.

## Run

```
python run_all.py          # ~5 min, plain Python 3.9, PowerFactory closed; needs matplotlib, reportlab, PyMuPDF
```

| Step | Script | What it does |
|---|---|---|
| 1 | `step1_build_model.py` | Imports `IEEE 13 Node Feeder.pfd` as project *IEEE13 DSDR Fuse Coordination* (first run only), removes all old protection, adds the DL lateral, sets the DG to Table I, places 15 fuses, R1 and R2 |
| 2 | `step2_studies.py` | Load flows and 273 short circuits (all nodes × LG/LL/LLG/LLL × phases, DG out/in, 3 Ω minimum faults, DG penetration sweep, the figures' faults) → `results/studies.json` |
| 3 | `step3_design_and_evaluate.py` | The paper's method (Fig. 5, eqs. 1–12), coordination classification, Tables II–IV, Figs. 8, 9, 11–17 (pure Python, same curves as PowerFactory) |
| 4 | `step4_apply_settings.py [conventional\|dsdr]` | Writes the settings into PowerFactory and checks PowerFactory's own trip times (`c:Ttrip`) against step 3 |
| 5 | `step5_fig10_emt.py` | Fig. 10 as a PowerFactory EMT simulation of the reclosing sequence |
| – | `make_tables.py` | Tables I–IV into `results/database/` (CSV and `Tables_I_to_IV.txt`); Table I is read back from the model, Table IV includes the fuse, its size, current, t_MMT, t_TCT and margin |
| – | `make_figures_1_to_6.py` | Figs. 1–6 (explanatory figures and the single-line diagram) redrawn from the model's curves and fault currents |

`protection_data.py` holds device locations, fuse sizes with their sources, and the paper's values.
`curves.py` holds the relay and fuse curves. Outputs are in `results/` (CSV tables, `settings.json`,
`summary.txt`, `figures/`).

## Model decisions and their sources

| Item | Choice | Source / reason |
|---|---|---|
| Network | IEEE 13-node feeder of the DIgSILENT example; loads, lines and regulator taps checked against Kersting [33] | – |
| Source | Study case **"Study with Substation Transformer"** (115/4.16 kV, 5 MVA) | Reproduces the IEEE short-circuit benchmark (Kersting & Shirek, quoted in [8]) within 1–2 % at every node (RG60 −6.7 %). The stiff-grid case used by the earlier attempt is 20–65 % too high. |
| DG | 4.05 MVA / 0.69 kV synchronous machine at 692, 0.15 pu transformer, Table I data | Paper. The machine type is set to round rotor, because Table I gives X′q and T′q0; the open-circuit time constants are converted to short-circuit values. All Table I values read back from the model match (`results/database/Table_I_DG_parameters.csv`). Until 2026-10-02 the type was salient pole, which made T″q0 0.33 s instead of 0.19 s; this affects the EMT run only. |
| Fault "DL" | Middle distributed-load lump moved behind a 10 ft lateral nDL–DL | So that a DL fault lies below F-DL, as drawn in Fig. 6 |
| Fuses | Gould-Shawmut **A055C** library fuses (and IEC gL-800A on the LV side) | The size drawn in the 2022 paper's figures where a figure shows the fuse (F632 400E, F633 250E, F646 300E, F671-1 300E, F671-2 300E, F684 200E, F692 200E, F692-R 250E; bands digitised and matched to the library within 2 %), otherwise [8] Table V. [8] names some devices differently: its REC1 / REC2 are R1 / R2 here, its relays R1, R2, R5 are not used, its F671 is F671-2 here and its F671-R is F671 here (250E). [8]'s own sizes for F646, F684, F671-2 (200E, 150E, 200E) were tried and rejected: with F671-2 = 200E the fuse melts in the second fast shot of Fig. 10 (0.62 s) instead of after both (paper 1.21 s). |
| R1 | GE **IAC77B801A**, extremely inverse, CT 900/5, tap 4 A = **720 A** (eq. 3 gives 734.6 A), TDS **0.5 / 10** | Paper. 720 A reproduces the paper's worked example (4219 A → 0.097 / 1.932 s) within 0.3 %. |
| R2 | GE/Alstom **CDG34** (CDG14 extremely-inverse table, curve starts at 2 × plug) | Paper. The fast curve starts at Ip = 1.25 Inom (plug Ip/2) and the delayed curve at 2 Ip (plug Ip), as the curve starts in Figs. 8 and 13 show. |
| DSDR | Same CDG curve in both directions, TMS 0.1–1.0; reverse setting group on CT 500/5 | Paper, Section IV-A. The CDG table is undefined below TMS 0.1 (PowerFactory's extrapolation even gives negative times). |
| Direction | PowerFactory's CDG34 is non-directional, so the four R2 units carry the two setting groups and direction is applied by fault location (upstream of R2 = reverse) | – |

## Results

### Table II – rated and fault currents (DG out)

Rated currents agree with the paper within 1.9 % on every branch (R2's branch: 470.0 vs 478.2 A).
Fault levels follow the IEEE benchmark and are therefore lower than the paper's If,max, some of which
are physically inconsistent (632–633: 6.73 kA, 692–675: 7.83 kA, both above the paper's own 5.41 kA
at the feeder head). Full table: `results/Table_II.csv`.

### Design (Fig. 5 steps)

| Stage | Result |
|---|---|
| A - no DG, starting fuse sizes | 35/39 fault cells coordinated. The series pair F692-R 250E / F671-1 300E breaks the 75 % rule (eq. 8) at 675. |
| A - after step 10 | **39/39** (F692-R 250E -> 200E). R2 forward: TMS 0.1 (fast) / 1.0 (delayed; the highest dial that keeps >= 10 cycles below R1) |
| B - DG 4.05 MVA added, conventional R2 (Fig. 14) | 24/39 held; **29/39 cells agree with the paper's Fig. 14** |
| C - R2 as DSDR (Fig. 17) | Ip,rv = 1.25 x 252.2 A reverse load current = 315 A (eq. 12). Fuse revisions (step 9): F632 -> 500E; F633, F646, F-DL and F671-1 -> 400E; F692-R -> 250E. **38/39 held with DG** |
| Same fuses, conventional R2 | 31/39, so the DSDR itself restores 7 cells |

Step 8 (revising the TMS by If,Rec/If,Fuse) could not help, because every lost case already had the
recloser at a dial limit: R1 at TDS 0.5 / 10, R2 at TMS 0.1 / 1.0. The paper's R1 settings are
exactly the IAC dial extremes.

**What remains lost, and why it cannot be fixed with these devices:** 692 LG. F671-1 must be 400E to
stay selective with F692-R (eq. 8), but then it clears after R2's delayed curve, which is already at
its maximum dial. Without DG, the revised fuses also lose 645 LG (R1 delayed at TDS 10 vs F632 500E).
The alternative priority (keep every no-DG case) gives 39/39 without DG but only 33/39 with DG.
Fuse sizes cannot adapt to the DG state, so this is a real trade-off.

### Table IV – operating times with the DSDR (`results/Table_IV.csv`)

R1 times are 13–78 % slower than the paper's (0.081 vs 0.070 s at 632, 0.222 vs 0.125 s at 684;
652 is the exception at −34 %). The model's fault currents follow the IEEE benchmark and are lower
than the paper's, and the paper does not state the fault type behind each row. The bolted fault used
here is LLL, LL at two-phase nodes, and LG at single-phase nodes. R2 and fuse times differ further
because the paper does not publish R2's settings.
The fuse column (t_MMT) is the minimum-melting time of the fuse nearest to the fault, read from its A055C
curve at the current through the fuse (grid plus DG share). It is between 65 % below and 200 % above the
paper's values, which cannot be reproduced without the paper's fuse sizes; in all nine rows with a fuse
t_MMT is longer than the last fast trip (smallest margin 6 ms at 675). The full table with size, current,
t_TCT and margin is `results/database/Table_IV_operating_times.csv`; the hand calculation is in
`results/Operating_Time_Calculation.pdf` (section 4.3 and the worked examples).
Fig. 15 (solid LL at 646): the fuses see 3.67 kA in the model against 3.64 kA in the paper. R2
reverse sees 1.11 kA (paper 1.54 kA) and trips on its fast curve in 0.086 s (paper 0.103 s), before
F646 melts.

### Fig. 10 – EMT

LL a–c fault at 684 through 0.2 Ω, applied at 0.30 s, two fast shots, 0.2 s dead time (both times read from the
paper's figure; until 2026-10-02 the run used 0.10 s and 0.3 s, which made the absolute times not comparable).
The plotted current is the feeder current arriving at node 632, phases a and c: 557 / 588 A RMS before the fault,
2362 / 2719 A RMS during it (peak 3338 / 3842 A; the paper's larger phase peaks at about 5000 A).
Results are in `results/Fig10_summary.json`.

* **DG out:** the fast shots use 45 % of F671-2's (300E) melting heat. The fuse melts at **1.25 s**
  and clears at 1.61 s, so fuse saving works. The paper's fuse operation is at 1.21 s: 0.04 s from our melting,
  0.4 s before our clearing; the paper does not say which of the two it marks.
* **DG in:** R2 opening does not de-energise the fault, because the DG at 692 keeps feeding it through 671
  during the dead times. F671-2 melts at 0.75 s, at the end of the second fast shot, and clears at 1.25 s. The paper's DSDR does not address DG infeed into faults downstream of R2.

### Verification

PowerFactory's own relay and fuse models (`c:Ttrip`) agree with the analysis on **1896 operating
times, maximum deviation 1.22 %** (`results/PF_vs_Python_times_*.csv`).

## Where the paper is inconsistent

1. **Table III vs eq. (9).** The paper computes b<sub>i</sub> with i counted from the *source*, the
   reverse of the definition it cites ([25]: i = 1 for the fuse closest to the fault). Recomputed
   with reversed indexing, the model matches the paper within 0.03–0.05 for the R1-zone fuses
   (F632 6.35 vs 6.38, F645 6.62 vs 6.65, F646 6.62 vs 6.67, F-DL 6.52 vs 6.54, F634 8.33 vs 8.32).
   With that indexing the upstream fuse is faster than the downstream one, so series coordination
   fails. `results/Table_III.csv` gives both versions.
2. **Figures vs Table III.** The fuse times in the figures come from A055C library fuses, not from
   eq. (6) with Table III (F646 at 3.6 kA: 0.18 s in Fig. 16 vs 1.85 s from eq. 6).
3. **Fuse sizes differ between figures.** F646 is 200E in Fig. 12 but 300E in Figs. 11 and 16; F632 is
   400E in Figs. 12, 15 and 16 but 500E in Fig. 11.
4. **R2's settings are not published**, and Table IV's fast/delayed ratios for R2 are not constant.
5. **Fig. 12** (LL at 645, 1.5 Ω) is lost in the paper but held in the model: here the conventional
   R2's delayed unit does not pick up the DG's 783 A at all.

## Load-flow and short-circuit database, and comparison PDFs (added 2026-10-01)

| Script | What it does | Output |
|---|---|---|
| `loadflow_all_buses.py` | Load flow on all buses and branches, "From node -> To node", DG out and in; closes any open feeder switch first and says so | `results/database/7_`-`10_*.csv`, `LoadFlow_AllBuses_Report.txt` |
| `database_study.py` | Load-flow and short-circuit database with current direction at R1 / R2, If,max, If,min and validation checks | `results/database/` |
| `show_progress.py` | The script behind PowerFactory's `Final(1)`: runs the two above, then (with `RUN_COORDINATION = True`) the coordination steps 2-4, `make_tables.py` (Tables I-IV printed in the report) and `make_figures_1_to_6.py` | Output Window, `results/Show_Progress_output.txt` |
| `make_loadflow_comparison_pdf.py` | Load flow with DG against the base case (DG out) | `results/LoadFlow_Comparison_Base_vs_DG.pdf` |
| `make_paper_vs_database_pdf.py` | Database against the paper: Table I, Table II, figure fault currents, direction at R2 | `results/Paper_vs_Our_Results.pdf` |
| `make_comparison_pdf.py` | Coordination against the paper: Tables III-IV, Figs. 8-17; appendix with the inventory of all tables and figures, Table I and Figs. 1-6 |
| `make_operating_time_pdf.py` | Hand calculation of Table IV: R1 (IAC equation), R2 (CDG table), fuse t_MMT / t_TCT (A055C curves), five worked examples | `results/Operating_Time_Calculation.pdf` | `results/Comparison_with_Reference_Paper.pdf` |
| `make_report_latex.py` | Project report as LaTeX (layout of `DSDR_Final_Project_Progress_Report`); tables filled from the results; text in `report_template.tex.in` (a template with placeholders: it does not compile on its own) | `report/main.tex`, `report/figures/` (compile with pdfLaTeX, e.g. upload the folder to Overleaf) |
| `make_coordination_diagrams.py` | Coordination diagrams, single setting vs dual setting on R2, same fuses in both; fault table with Zf, R1 / R2 current and direction | `results/coordination_diagrams/` (9 case PNGs, summary, `Fault_table.csv`, `Coordination_Diagrams.pdf`) |

Decisions taken for the database:

* **If,min** follows the paper's rule (LG through 3 ohm at the farthest node) for the comparison with Table II.
  The lowest LG-3-ohm current of a section can be lower (phase b fault at 680 or 675) and is the value used to
  check the pickups (Fig. 5 step 5).
* **Sensitivity with the DG.** Without the DG both pickups (R1 734.6 A, R2 587.5 A) are below the lowest
  minimum fault current (1074 A / 879 A). With the DG they are not (577 A / 368 A): the DG supplies part of the
  fault and of the load. The paper does not examine this.
* **Fuse revisions** prioritise coordination with the DG connected (Fig. 17: 38/39 with DG, 37/39 without).

Engine mode cannot start while the PowerFactory window is open; PowerFactory steps then have to be run through
`Final(1)`. The PDF scripts need only the result files.

## Known limitations

* Directional behaviour of the DSDR is applied by fault location, not by a PowerFactory directional element.
* Coordination is judged on initial symmetrical currents (complete method). Fuse pre-heating across
  reclosing shots is modelled only in Fig. 10.
* In the Fig. 10 DG-in case, the currents at 632 after the fuse clears are large and irregular. This
  is most likely the low-inertia DG (Table I, M = 1.5 s) swinging after a ~0.7 s fault; it was not
  investigated further.
* The IEEE 34-node part of the paper (Figs. 18–21, Table V) is not replicated.
