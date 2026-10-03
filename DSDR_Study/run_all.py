"""
Runs the whole replication from a clean start (about 5 minutes).  PowerFactory must be closed
(engine mode cannot start while its window is open).

  step1  build the protection system in the IEEE 13-node feeder          (PowerFactory)
  step2  load flows and short circuits                                      (PowerFactory)
  step3  design by the paper's method, Tables II-IV, Figs. 8, 9, 11-17      (Python)
         Tables I-IV into results/database (Table IV with fuse t_MMT); Figs. 1-6  (Python)
  step4  settings into PowerFactory + check of PowerFactory's trip times    (PowerFactory)
  step5  Fig. 10 in EMT                                                     (PowerFactory)
  load flow on all buses and branches; load-flow / short-circuit database   (PowerFactory)
  the PDFs: load-flow comparison, paper vs database, paper vs replication,
  operating-time calculation (reclosers and fuses), coordination diagrams   (Python)
The model is left with the DSDR settings (Fig. 17).
"""

import subprocess
import sys

STEPS = [["step1_build_model.py"], ["step2_studies.py"], ["step3_design_and_evaluate.py"],
         ["make_tables.py"], ["make_figures_1_to_6.py"],
         ["step4_apply_settings.py", "conventional"], ["step5_fig10_emt.py"],
         ["step4_apply_settings.py", "dsdr"],
         ["loadflow_all_buses.py"], ["database_study.py"],
         ["make_loadflow_comparison_pdf.py"], ["make_paper_vs_database_pdf.py"],
         ["make_comparison_pdf.py"], ["make_operating_time_pdf.py"], ["make_coordination_diagrams.py"], ["build_report_pdf.py"], ["make_figure_guide.py"]]

for step in STEPS:
    print("\n" + "=" * 90 + "\n" + " ".join(step) + "\n" + "=" * 90, flush=True)
    rc = subprocess.call([sys.executable] + step)
    if rc:
        sys.exit("%s failed (exit code %d)" % (step[0], rc))
