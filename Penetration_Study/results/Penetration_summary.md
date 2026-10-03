# DG penetration study - Fig. 7

Seven PowerFactory models (`pfd/IEEE13_DG_penetration_000.pfd` ... `_100.pfd`), copies of the main project with the DG at 692 set to 0 ... 100 % of 4.05 MVA and the conventional (single-setting) protection. The main project itself was not changed. Times are PowerFactory's own relay and fuse times.

| DG | DG MVA | 633: I F633 / I R1 (A) | 633: CTI (s) | 633 ring % | 671: I F671-2 / I R2 (A) | 671: CTI (s) | 671 ring % |
|---|---|---|---|---|---|---|---|
| 0 % | 0.00 | 4102 / 4162 | +0.004 | +2.1 | 2574 / 2711 | +0.403 | +26.0 |
| 10 % | 0.41 | 4256 / 4142 | -0.005 | -3.1 | 2715 / 2681 | +0.333 | +21.5 |
| 25 % | 1.01 | 4478 / 4111 | -0.017 | -9.6 | 2926 / 2636 | +0.254 | +16.4 |
| 37 % | 1.50 | 4648 / 4088 | -0.024 | -13.9 | 3094 / 2598 | +0.207 | +13.4 |
| 50 % | 2.02 | 4824 / 4062 | -0.031 | -17.9 | 3276 / 2557 | +0.166 | +10.7 |
| 75 % | 3.04 | 5140 / 4015 | -0.042 | -24.2 | 3623 / 2511 | +0.110 | +7.1 |
| 100 % | 4.05 | 5426 / 3970 | -0.051 | -29.2 | 3963 / 2543 | +0.075 | +4.9 |

Ring % = 100 x CTI / sum of |CTI| over the seven levels (each ring adds up to 100 %). Sum of |CTI|: 633 0.174 s, 671 1.548 s.

Zero crossing of the CTI: 633 at about 4 % penetration, 671 not reached up to 100 %.

