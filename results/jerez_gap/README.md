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

## Why CAP_H changes Vpi*L, and why less with the buffer (`cap_buffer_decomposition.csv`)
WG_TOP 1.0 um. Both cap heights, with and without the 200 nm buffer, at the same gaps (4.2 and 3.4 um).
The mean DC field Ex in the rib (1 V applied) is recorded with Vpi*L.

| | gap 4.2, no buffer | gap 3.4, no buffer | gap 4.2, buffer | gap 3.4, buffer |
|---|---|---|---|---|
| Vpi*L, CAP_H 1.4 -> 0.5 | -4.1 % | -3.4 % | -3.2 % | -2.7 % |
| Ex in the rib, CAP_H 1.4 -> 0.5 | +4.6 % | +3.8 % | +3.7 % | +3.1 % |

| | CAP_H 1.4 | CAP_H 0.5 |
|---|---|---|
| buffer penalty at gap 4.2 | +19.4 % (+0.372 V*cm) | +20.5 % (+0.377 V*cm) |
| buffer penalty at gap 3.4 | +25.6 % | +26.5 % |

- **The cap acts electrostatically.** neff changes by only 4e-4, and the Ex change in the rib accounts for the
  Vpi*L change. A lower SiO2 cap (eps_DC 3.75) leaves more air (eps 1) next to the rib, so more of the gap voltage
  drops across the rib.
- **The buffer penalty is the same for both caps** (within ~1 point).
- **The cap effect is smaller with the buffer** (-2.7 to -3.2 % instead of -3.4 to -4.1 %). With the buffer, the
  200 nm oxide fills the whole gap at rib level whatever CAP_H is, so the cap only changes the dielectric
  above that.
- **Consequence:** the Vpi*L that can be recovered (unbuffered gap 4.2 -> buffered gap 3.2) is 0.135 V*cm at CAP_H 1.4
  and 0.101 V*cm at CAP_H 0.5.
- **Not proportional to CAP_H:**
  - 0.101/0.135 = 0.75, while 0.5/1.4 = 0.36;
  - two cap heights cannot fix a law;
  - the cap effect should saturate once the cap is taller than the gap field near the rib.

## Why the matching gap is 3.47 um at CAP_H 1.4 but 3.41 um at CAP_H 0.5 (WG_TOP 1.0; WG_TOP 1.4 is the same)
- **Formula.** The buffered curve is linear to within 0.7 mV*cm, so the matching gap is g* = 4.2 - P/s:
  - P = buffered - unbuffered Vpi*L at gap 4.2;
  - s = slope of the buffered curve.

| | P (V*cm) | s (V*cm/um) | P/s (um) | g* (um) |
|---|---|---|---|---|
| CAP_H 1.4 | 0.372 | 0.508 | 0.732 | 3.468 |
| CAP_H 0.5 | 0.377 | 0.478 | 0.788 | 3.412 |

- **Slope (about 80 % of the 0.056 um shift).** With CAP_H 0.5, narrowing the gap recovers 6 % less Vpi*L per um.
  - About half of that is because all its values are ~3 % lower (Vpi*L ~ 1/E_rib).
  - The other half is because the low-cap advantage grows with the gap: cap0.5/cap1.4 = 0.976 at 3.2, 0.972 at 3.6, 0.969 at 4.0.
- **Penalty (about 20 %).** P is slightly larger at CAP_H 0.5.
- **Same thing in relative terms:**
  - The low cap lowers the unbuffered reference by 4.1 %.
  - Near the matching gap it lowers the buffered curve by only 2.7 %.
  - So the target falls 1.4 % (~0.026 V*cm) further below the buffered curve, and reaching it needs 0.026 / 0.478 = 0.055 um more narrowing.

## CAP_H sweep (`cap_sweep.py`, `cap_sweep.csv`, `jerez_cap_sweep.png`)
- **Setup:** WG_TOP 1.0 um; CAP_H 0.3 -> 1.9 um (0.2 um steps, plus 1.4).
- **Runs per CAP_H:**
  - unbuffered gap 4.2 reference;
  - buffered at gaps 3.3, 3.4, 3.5, 3.6 and 4.2.
- **Run count:** 48 new runs, plus the CAP_H 1.4 / 0.5 runs from before. No failures.

| CAP_H (um) | 0.3 | 0.5 | 0.7 | 0.9 | 1.1 | 1.3 | 1.4 | 1.5 | 1.7 | 1.9 |
|---|---|---|---|---|---|---|---|---|---|---|
| target: no buffer, gap 4.2 (V*cm) | 1.789 | 1.837 | 1.867 | 1.886 | 1.901 | 1.911 | 1.915 | 1.919 | 1.924 | 1.928 |
| matching gap g* (um) | 3.361 | 3.410 | 3.433 | 3.447 | 3.456 | 3.462 | 3.464 | 3.466 | 3.469 | 3.471 |
| slope s (V*cm/um) | 0.463 | 0.477 | 0.487 | 0.495 | 0.500 | 0.505 | 0.506 | 0.508 | 0.510 | 0.512 |
| penalty P at 4.2 (V*cm) | 0.388 | 0.377 | 0.373 | 0.372 | 0.372 | 0.372 | 0.372 | 0.372 | 0.373 | 0.373 |
| buffered IL at g* (dB/cm) | 0.017 | 0.015 | 0.014 | 0.013 | 0.013 | 0.012 | 0.012 | 0.012 | 0.012 | 0.012 |

- **g* saturates; it is not proportional to CAP_H.**
  - Fit: g* = 3.471 - 0.238 exp(-CAP_H / 0.38 um), max residual 3 nm.
  - Above CAP_H ~1.1 um, g* stays within 15 nm of 3.47 um.
  - Below ~0.7 um it drops quickly, to 3.36 um at 0.3 um.
- **What drives it:**
  - The slope s of the buffered curve does most of it: it falls from 0.51 to 0.46 V*cm/um as the cap is lowered.
  - P is constant (0.372 V*cm) down to CAP_H 0.7 and grows only for the lowest caps.
- **Cap effect vs absolute cap-top height (bottom-right panel):**
  - CAP_H is measured from the gold bottom, so with the buffer the cap top sits 0.2 um higher above the slab.
  - Plotted against the real cap-top height, buffered and unbuffered nearly overlap.
  - So most of "the cap matters less with the buffer" at equal CAP_H is this 0.2 um offset of the definition.
  - What remains is a slightly longer decay length with the buffer (0.65 vs 0.54 um in CAP_H).
