# DSDR recloser–fuse coordination on the IEEE 13-node feeder (DIgSILENT PowerFactory)

Replication of the IEEE 13-node part of

> M. Yousaf, A. Jalilian, K. M. Muttaqi, D. Sutanto, "An Adaptive Overcurrent Protection Scheme for
> Dual-Setting Directional Recloser and Fuse Coordination in Unbalanced Distribution Networks With
> Distributed Generation," *IEEE Trans. Ind. Appl.*, vol. 58, no. 2, pp. 1831–1842, 2022.
> doi:[10.1109/TIA.2022.3146095](https://doi.org/10.1109/TIA.2022.3146095)

in DIgSILENT PowerFactory 2021 SP2, driven by Python.

| Path | Content |
|---|---|
| `IEEE 13 Node Feeder.pfd` | PowerFactory model (imported by the scripts on the first run) |
| `Replication/` | All scripts, the results, the figures and the LaTeX report — see [`Replication/README.md`](Replication/README.md) |
| `Replication/results/` | Tables I–IV, figures 1–6 and 8–17, load-flow / short-circuit database, PDFs |
| `Replication/report/` | Project report (LaTeX source and figures) |

Run everything (PowerFactory closed, Python 3.9 with matplotlib, reportlab, PyMuPDF):

```
cd Replication
python run_all.py
```

The reference papers are not included (copyright).
