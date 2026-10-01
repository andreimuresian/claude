# Lifted electrodes with a fully etched LN slab: slab_w sweep

**Design point:** 1575 nm wavelength, 550 nm LN film with a 275 nm etch (rib 275 nm, slab 275 nm). Bottom gap 4.2 µm, top gap 10 µm, so x_lift = 7.0 µm. The slab is removed outside a width `slab_w`. The material above fills the etched zone:
- air in the gap;
- gold under the lower blocks (the gold wraps the slab end);
- SiO₂ under the lifted pads.

**Notebook:** `VPI_interface_optimized_Lisbona_lifted_etched_slab.ipynb` in the repo root. It runs a single design point and is executed at `SLAB_W = 3.2`. The geometry cell source is `cells/cell0_etched.py`.

**Materials:** computed at `wl` by functions in cell 0, with no hard-coded indices.

| material | source | value at 1575 nm |
|---|---|---|
| LN | Zelmon 1997 | ne 2.136842, no 2.210268 (the old values) |
| SiO₂ | Malitson 1965 | 1.443723 (the old notebook had 1.438749) |
| Au | Johnson & Christy table, ε interpolated linearly in photon energy | ε = −120.37 − 11.93j (old anchor −120.7 − 11.9j) |

Gold has no Sellmeier form.

## Sweep convention

d is the position of the slab edge beyond the gold inner edge, per side: `slab_w = 4.2 + 2d`.

| regime | d range | slab_w range (µm) |
|---|---|---|
| slab ends in the air gap | d < 0 | 2.4–4.0 |
| slab ends inside the gold | 0.5 ≤ d < 4.9 | 5.2–13.95 |
| slab ends at the gold/SiO₂ interface | d = 4.9 | 14.0 |
| slab runs past the interface | 4.9 < d ≤ 9.9 | up to 24.0 |

The step in slab_w is 0.2 µm, refined to 0.05 µm around every ripple peak. There are 132 points in total.

## Results

| slab_w (µm) | regime | IL (dB/cm) | Vπ·L (V·cm) |
|---|---|---|---|
| 2.4 | air gap | 1.7e-5 | 5.39 |
| 3.2 | air gap | 1.6e-4 | 4.25 |
| 4.0 | air gap | 2.9e-3 | 3.06 |
| 5.2–13.95 | inside the gold | **0.038 – 2.88 (rippled)** | 2.265–2.267 |
| ≥ 15.6 | past the interface | 0.2278 ± 0.001 (flat) | 2.2668 |
| unetched slab (reference) | — | 0.2295 | 2.2668 |

**Slab ends inside the gold.** The standing wave is still there, and stronger than before. The slab wave under the gold (n ≈ 2.07 > n_rib) is now reflected by the gold-wrapped slab facet instead of the gold/SiO₂ interface.

The Airy model fits the data with an rms error of 0.0095 dB/cm (`fabry_perot_fit_slab_in_gold.json`). The cavity runs from the rib to the slab facet, L = d:

| fit parameter | slab facet as mirror | previous x_lift fit (gold/SiO₂ interface as mirror) |
|---|---|---|
| IL∞ (dB/cm) | 0.417 | 0.412 |
| round-trip decay 2α (µm⁻¹) | 0.180 | 0.175 |
| period (µm of edge position) | 0.895 | 0.895 |
| mirror reflectance ρ₀ | 0.944 | 0.908 |

The cavity is the same; only the mirror changed, and the gold-wrapped facet reflects better. The peaks are about 0.1 µm wide in edge position, so the slab-etch position becomes the fragile parameter.

**Slab runs past the interface.** IL equals the unetched value within 1%. Under SiO₂ the slab wave is evanescent (n 1.60–1.75 < n_rib), so slab beyond about 0.8 µm past the interface is invisible to the mode. The cavity, and its sensitivity to x_lift, is exactly the original one.

**Slab ends in the air gap.** There is no slab under the gold, so there is no leaky channel and IL is essentially zero. But the DC field must cross the air pocket between the slab end and the gold, in series with the high-ε LN, so the field in the LN drops. Vπ·L rises from 2.27 to 3.06–5.39 V·cm (+35% to +138%).

## Mesh check

The reference mesh is about twice as dense: every near-mode size is ×0.7 and the skin and corner meshes are ×0.67. The production mesh differs from it by at most 1.7% in IL and 0.1% in Vπ·L (`mesh_check.csv`).

## Files

- `slab_w_sweep.csv`: every point, with regime, neff, IL and Vπ·L.
- `IL_VpiL_vs_slab_w.png`: the plot.
- `fabry_perot_fit_slab_in_gold.json`, `mesh_check.csv`.
- `analysis_script.py`: the script that produced them from the run logs.
