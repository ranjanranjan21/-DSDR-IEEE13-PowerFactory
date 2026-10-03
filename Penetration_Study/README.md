# DG penetration study (Fig. 7 of Yousaf et al. 2022)

Separate from the replication: the project "IEEE13 Yousaf2022 Replication" and the `Replication/` folder are not changed.

| File | Content |
|---|---|
| `make_penetration_models.py` | Copies the replication project 7 times in PowerFactory (DG at 692 = 0, 10, 25, 37, 50, 75, 100 % of 4.05 MVA, conventional protection), runs load flow and faults, reads PowerFactory's relay/fuse times, exports each copy to `pfd/` (PowerFactory closed) |
| `analyse_penetration.py` | CTI per level, ring % (each ring = 100 %), comparison with the paper, figures (Python only) |
| `pfd/IEEE13_DG_penetration_XXX.pfd` | The seven PowerFactory models (import with File > Import > PFD) |
| `results/` | `penetration_results.json`, `Penetration_CTI.csv`, `Penetration_loadflow.csv`, `Fig07_penetration.png`, `Fig07_penetration_currents.png`, `Penetration_summary.md` |

Cases: 633 = LLL fault at 633, fuse F633 against R1 fast; 671 = LL fault at 684 on the lateral that leaves 671 through fuse F671-2, against R2 fast.
CTI = t_MMT(fuse) - t_fast(recloser); ring % = 100 x CTI / sum of |CTI| over the seven levels.
