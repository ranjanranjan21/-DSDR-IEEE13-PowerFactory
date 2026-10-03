# Penetration study - pickups and short-circuit levels

## 1. Pickup currents (eq. 3, OLF = 1.25)

The models keep the pickups of the design without DG (R1 720 A; R2 forward plugs 300 / 600 A). The table shows what eq. (3) would give from each level's own load flow.

| DG | R1 Inom (A) | R1 1.25 Inom (A) | R1 tap (A) | R2 Inom (A) | R2 load flow | R2 1.25 Inom (A) | R2 plugs fast / delayed (A) |
|---|---|---|---|---|---|---|---|
| 0 % | 587.7 | 734.6 | 720 | 470.0 | forward (+2460 kW) | 587.5 | 300 / 600 |
| 10 % | 543.1 | 678.9 | 720 | 430.1 | forward (+2140 kW) | 537.6 | 240 / 480 |
| 25 % | 480.7 | 600.9 | 540 | 372.2 | forward (+1658 kW) | 465.2 | 240 / 480 |
| 37 % | 434.8 | 543.5 | 540 | 328.6 | forward (+1273 kW) | 410.8 | 200 / 400 |
| 50 % | 389.9 | 487.4 | 450 | 285.3 | forward (+855 kW) | 356.6 | 200 / 400 |
| 75 % | 321.2 | 401.5 | 360 | 222.4 | forward (+50 kW) | 278.0 | 200 / 300 |
| 100 % | 284.9 | 356.1 | 360 | 252.2 | reverse (-755 kW) | 315.2 | 150 / 300 (CT 500/5) |

Set in the models: R1 720 A, R2 300 / 600 A at every level.

## 2. Maximum short-circuit level at each node (bolted, largest fault type), A

| Node | Fault | 0 % | 10 % | 25 % | 37 % | 50 % | 75 % | 100 % | change |
|---|---|---|---|---|---|---|---|---|---|
| 632 | LLL | 4735 | 4935 | 5227 | 5453 | 5690 | 6123 | 6526 | +38 % |
| 633 | LLL | 4102 | 4256 | 4478 | 4648 | 4824 | 5140 | 5426 | +32 % |
| 634 | LLL | 15671 | 15941 | 16307 | 16570 | 16828 | 17257 | 17608 | +12 % |
| 645 | LLG | 3418 | 3526 | 3685 | 3807 | 3932 | 4149 | 4341 | +27 % |
| 646 | LLG | 3112 | 3203 | 3332 | 3429 | 3528 | 3701 | 3854 | +24 % |
| 671 | LLL | 3390 | 3600 | 3919 | 4178 | 4461 | 5010 | 5564 | +64 % |
| 692 | LLL | 3390 | 3600 | 3919 | 4178 | 4461 | 5010 | 5564 | +64 % |
| 675 | LLL | 3151 | 3335 | 3612 | 3840 | 4087 | 4557 | 5022 | +59 % |
| 680 | LLL | 2930 | 3087 | 3322 | 3510 | 3711 | 4091 | 4460 | +52 % |
| 684 | LLG | 2655 | 2802 | 3027 | 3204 | 3395 | 3756 | 4107 | +55 % |
| 652 | LG | 1874 | 1919 | 1983 | 2031 | 2080 | 2164 | 2239 | +19 % |
| 611 | LG | 1857 | 1906 | 1973 | 2023 | 2074 | 2161 | 2236 | +20 % |
| DL | LLL | 3946 | 4150 | 4454 | 4694 | 4952 | 5436 | 5902 | +50 % |

## 3. Current through the reclosers for the same faults, A (0 % -> 100 %)

| Node | R1 at 0 % | R1 at 100 % | R1 change | R2 at 0 % | R2 at 100 % | R2 direction at 100 % |
|---|---|---|---|---|---|---|
| 632 | 4735 | 4734 | -0 % | 0 | 1813 | rev |
| 633 | 4162 | 3970 | -5 % | 66 | 1500 | rev |
| 634 | 2034 | 1611 | -21 % | 298 | 618 | rev |
| 645 | 3528 | 3330 | -6 % | 478 | 1262 | rev |
| 646 | 3192 | 3000 | -6 % | 475 | 1135 | rev |
| 671 | 3413 | 3412 | -0 % | 3390 | 3391 | fwd |
| 692 | 3413 | 3412 | -0 % | 3390 | 3391 | fwd |
| 675 | 3202 | 3090 | -3 % | 3174 | 3050 | fwd |
| 680 | 3006 | 2789 | -7 % | 2976 | 2757 | fwd |
| 684 | 2836 | 2669 | -6 % | 2744 | 2651 | fwd |
| 652 | 2094 | 1795 | -14 % | 2059 | 1761 | fwd |
| 611 | 2084 | 1814 | -13 % | 1991 | 1718 | fwd |
| DL | 3959 | 3954 | -0 % | 1 | 1972 | rev |

## 4. Minimum fault (LG through 3 ohm) against the pickup

Lowest current through each recloser for an LG fault through 3 ohm anywhere in its zone. R2's fast curve starts at 2 x 300 A = 600 A (CDG curve starts at twice the plug).

| DG | R1 lowest (A) | node | R1 pickup 720 A | R2 lowest (A) | node | R2 fast start 600 A |
|---|---|---|---|---|---|---|
| 0 % | 1074 | 680 | **does not operate** | 878 | 680 | operates |
| 10 % | 1018 | 680 | **does not operate** | 821 | 680 | operates |
| 25 % | 937 | 680 | **does not operate** | 738 | 680 | operates |
| 37 % | 874 | 680 | **does not operate** | 673 | 680 | operates |
| 50 % | 809 | 680 | **does not operate** | 606 | 680 | operates |
| 75 % | 689 | 680 | **does not operate** | 483 | 675 | **does not operate** |
| 100 % | 577 | 675 | **does not operate** | 368 | 675 | **does not operate** |

R1's IAC curve starts at 1.5 x pickup = 1080 A, so R1 already misses the 3-ohm LG fault at 680 by 6 A without DG (1074 A); the margin then grows to 503 A short at 100 %. R2 still sees its zone's minimum fault up to 50 % (606 A against 600 A) and loses it just above 50 %.

