# Buffered Jerez lifted, 1360 nm: how far can the bottom gap be relaxed?

## Design (formerly "Lisbon lifted"; renamed Jerez lifted for the O-band technology)
- 400 nm LN film, 170 nm rib etch (230 nm slab), 60 deg sidewalls.
- 200 nm SiO2 buffer under the electrodes and across the gap.
- 2 um thick electrodes; pad on a 3.6 um SiO2 lift.
- GAP_TOP 8 um (x_lift = 6.0 um); CAP_W 2.0 um.
- Materials are computed at `wl`:
  - LN: Zelmon (ne 2.143411, no 2.217969 at 1360 nm);
  - SiO2: Malitson (1.446237);
  - Au: Johnson & Christy, interpolated in photon energy (-86.39 - 7.77j). Gold has no Sellmeier form.

## Notebook
`VPI_interface_optimized_Jerez_lifted_buffer.ipynb` (repo root) is the attached Lisbon-lifted-buffer notebook with cell 0
replaced by `cells/cell0_jerez_lifted_buffer.py`. `build_nb_j.py` regenerates it. Changes:
- `wl = 1.360`; no hard-coded optical constant is left.
- TECN 0.400, WG_H 0.170, BUFFER_H 0.200, CAP_W 2.0, GAP_TOP 8.0.
- n_guess 1.86.
- Cap fix: a cap lower than the 0.6 um fine-mesh band (e.g. CAP_H 0.5) was stretched to 0.6 um by the old geometry
  code. It now ends at CAP_H.
- Cells 1-5 are unchanged.

## Sweep (`jerez_gap_sweep.csv`, `jerez_VpiL_IL_vs_gap.png`)
- 200 nm buffer, GAP_BOT 3.2 -> 4.0 um in 0.1 um steps.
- For each CAP_H in {1.4, 0.5} um and WG_TOP in {1.0, 1.4} um.
- Plus the unbuffered GAP_BOT 4.2 um reference of each case (BUFFER_H = 0, same everything else).
- 40 runs, no failures.

| case | unbuffered gap 4.2 Vpi*L (V*cm) | buffered gap 3.2 Vpi*L | buffered gap with the same Vpi*L (um) | buffered IL there (dB/cm) | unbuffered IL at x_lift 6 (dB/cm) |
|---|---|---|---|---|---|
| CAP_H 1.4 / WG_TOP 1.0 | 1.915 | 1.780 | **3.46** | 0.0124 | 0.313 |
| CAP_H 1.4 / WG_TOP 1.4 | 1.840 | 1.706 | **3.47** | 0.0130 | 0.188 |
| CAP_H 0.5 / WG_TOP 1.0 | 1.837 | 1.736 | **3.41** | 0.0147 | 0.311 |
| CAP_H 0.5 / WG_TOP 1.4 | 1.768 | 1.666 | **3.42** | 0.0155 | 0.196 |

- **Validation:** CAP_H 1.4 / WG_TOP 1.0 reproduces the earlier 1360 nm results (GAP_TOP 9, anchor-scaled gold):
  - buffered gap 3.2: 1.780 vs 1.779 V*cm, IL 0.0286 vs 0.0284 dB/cm;
  - unbuffered gap 4.2: 1.915 vs 1.916 V*cm.
- **Vpi*L** rises linearly with the gap, about +0.05 V*cm per 0.1 um.
- **IL** falls exponentially with the gap, about x0.73 per 0.1 um (0.029 -> 0.0022 dB/cm). It is the same within
  0.4 % for both cap heights, and within 13 % for both rib widths.
- The unbuffered IL is one point on its x_lift ripple: the earlier 1360 nm x_lift sweep gave a ripple range of 0.075-0.269 dB/cm
  (WG_TOP 1.0, CAP_H 1.4).

## x_lift flatness check (`xlift_flatness_check.csv`)
At the matching gaps (CAP_H 1.4 / WG_TOP 1.0, gap 3.5; CAP_H 0.5 / WG_TOP 1.4, gap 3.4), GAP_TOP was stepped
8 -> 10 um, i.e. x_lift 6.0 -> 7.0 um:
- buffered IL changes by less than 0.1 %;
- Vpi*L changes by less than 0.03 %.

So the buffered numbers do not depend on GAP_TOP / x_lift, as expected with the buffer above cutoff (~46 nm at 1360 nm).
