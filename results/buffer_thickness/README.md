# Vπ·L and IL vs SiO2 buffer thickness: buffered lifted designs

Motivation: lab measurements of the 200 nm buffer (three wafers, about 40 chips each). The best
wafer (sil-A) gives a spread of about ±20 nm, and ±40 nm in extreme cases. This sweep covers
BUFFER_H = 130–270 nm in 10 nm steps.

| | Lisbon lifted | Jerez lifted |
|---|---|---|
| band / λ | C, 1575 nm | O, 1360 nm |
| LN film / etch / slab | 550 / 275 / 275 nm | 400 / 170 / 230 nm |
| common | gap 3.4 µm, GAP_TOP 10 µm, CAP_W 2.0, CAP_H 1.4 µm (from the buffer top), ALPHA 60° | same |
| widths | WG_TOP 1.0 and 1.4 µm | same |

Both designs run on `cells/cell0_jerez_lifted_buffer.py`, with the converged mesh. It has the
same geometry as the Lisbon buffered cell, and uses Sellmeier dispersion (LN Zelmon, SiO2
Malitson) and J&C gold for both bands. For Lisbon this replaces the legacy hard-coded
n_SiO2 = 1.438749 with 1.44372; Vπ·L at 150 nm moves from 2.1996 to 2.2016 V·cm.
CAP_H is kept at 1.4 µm, so the cap top moves with the buffer.
Reference (dashed lines): the unbuffered design (BUFFER_H = 0) at gap 4.2 µm.

Files: `buffer_thickness_sweep.csv` (64 runs), `summary.json`, `raw_solver_log.txt`,
`buffer_thickness_WG1.0.png`, `buffer_thickness_WG1.4.png`, `buffer_thickness_both_widths.png`,
`analysis.py` (`python3 analysis.py raw_solver_log.txt`).

## Results

| case | Vπ·L @200 nm (V·cm) | slope (mV·cm/nm) | Vπ·L ±20 nm | Vπ·L ±40 nm | IL @200 nm (dB/cm) | IL ±20 nm | IL ±40 nm | unbuffered gap 4.2 (V·cm) | buffer at which Vπ·L = ref |
|---|---|---|---|---|---|---|---|---|---|
| Lisbon WG 1.0 | 2.2727 | 1.34 | −1.2 / +1.1 % | −2.5 / +2.2 % | 0.0269 | +14 / −13 % | +31 / −24 % | 2.2668 | 196 nm |
| Lisbon WG 1.4 | 2.1747 | 1.30 | −1.2 / +1.2 % | −2.5 / +2.3 % | 0.0287 | +14 / −12 % | +30 / −23 % | 2.1734 | 199 nm |
| Jerez WG 1.0 | 1.8821 | 1.02 | −1.1 / +1.0 % | −2.3 / +2.0 % | 0.0152 | +17 / −15 % | +37 / −27 % | 1.9154 | 235 nm |
| Jerez WG 1.4 | 1.8062 | 0.99 | −1.1 / +1.1 % | −2.3 / +2.1 % | 0.0163 | +17 / −15 % | +37 / −27 % | 1.8405 | 236 nm |

(The ± columns give the change at −Δ / +Δ buffer thickness.)

- **Vπ·L is almost linear** in the buffer thickness: the largest deviation from a straight line
  is 6 mV·cm over 130–270 nm, with slightly less sensitivity at thicker buffers. It is about
  ±1.1 % at ±20 nm and about ±2.3 % at ±40 nm, for both designs and both widths.
- **IL decays exponentially** with the buffer thickness: e-folding length 150 nm (Lisbon) and
  125 nm (Jerez). That is about ±15 % at ±20 nm and +30–37 % / −24–27 % at ±40 nm. In absolute
  terms it stays at or below 0.035 (Lisbon) and 0.022 dB/cm (Jerez) inside the ±40 nm window.
- **Margin against the unbuffered gap-4.2 reference:**
  - Jerez at gap 3.4 stays below the reference up to a buffer of about 235 nm, so the whole
    ±20 nm window and most of the ±40 nm window is covered.
  - Lisbon at gap 3.4 crosses the reference at 196–199 nm, so it has no margin: a thicker
    buffer (+20 nm gives +1.1 %) makes it slightly worse than the unbuffered 4.2 µm design.
