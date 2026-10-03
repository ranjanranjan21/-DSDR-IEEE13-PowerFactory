# Dual-Setting Directional Recloser and Fuse Coordination in Unbalanced Distribution Networks With Distributed Generation

Study of dual-setting directional recloser (DSDR) and fuse coordination on the IEEE 13-node feeder,
following the method of

> M. Yousaf, A. Jalilian, K. M. Muttaqi, D. Sutanto, "An Adaptive Overcurrent Protection Scheme for
> Dual-Setting Directional Recloser and Fuse Coordination in Unbalanced Distribution Networks With
> Distributed Generation," *IEEE Trans. Ind. Appl.*, vol. 58, no. 2, pp. 1831–1842, 2022.
> doi:[10.1109/TIA.2022.3146095](https://doi.org/10.1109/TIA.2022.3146095)

in DIgSILENT PowerFactory 2021 SP2, driven by Python.

| Path | Content |
|---|---|
| `IEEE 13 Node Feeder.pfd` | PowerFactory model (imported by the scripts on the first run) |
| `DSDR_Study/` | All scripts, the results, the figures and the LaTeX report — see [`DSDR_Study/README.md`](DSDR_Study/README.md) |
| `DSDR_Study/results/` | Tables I–IV, figures 1–6 and 8–17, load-flow / short-circuit database, PDFs |
| `DSDR_Study/report/` | Project report (LaTeX source and figures) |
| `Fig10_EMT_Study/` | Fig. 10 EMT study in two separate PowerFactory projects (DG out / DG in) — see [`Fig10_EMT_Study/README.md`](Fig10_EMT_Study/README.md) |
| `Penetration_Study/` | DG penetration study (Fig. 7): seven PowerFactory models (0–100 % of 4.05 MVA), scripts and results — see [`Penetration_Study/README.md`](Penetration_Study/README.md) |

Run everything (PowerFactory closed, Python 3.9 with matplotlib, reportlab, PyMuPDF):

```
cd DSDR_Study
python run_all.py
```

The reference papers are not included (copyright).
