# Three sweeps (1575 nm)

Analysis: `analysis.py`. It reads the run logs and writes every CSV, PNG and `summary.json`.

## 1. Standard lifted design (no buffer): x_lift sweep at gap 3.9 and 5.0 µm
`sweep1_legacy_gap_xlift.csv`, `sweep1_IL_vs_xlift_gaps.png`

- x_lift runs from 6.5 to 11 µm in 0.1 µm steps, plus 12.1–30.1 µm. x_lift is changed through the top gap.
- Same code (`cell0_lifted.py`) and material values as the gap 4.2 µm reference (`../lift_sweep.csv`).

| gap (µm) | IL∞ (dB/cm) | IL, x_lift 6.5–11 µm (dB/cm) | period (µm) | 2α (/µm) | ρ₀ | Vπ·L (V·cm) |
|---|---|---|---|---|---|---|
| 3.9 | 1.103 | 0.47 – 2.16 | 0.895 | 0.180 | 0.93 | 2.08 |
| 4.2 | 0.412 | 0.18 – 0.88 | 0.895 | 0.177 | 0.92 | 2.26 |
| 5.0 | 0.030 | 0.013 – 0.074 | 0.896 | 0.179 | 0.93 | 2.76 |

- Plot IL/IL∞ against the cavity length L = x_lift − gap/2 and the three curves lie on top of each other: same period, same decay, same phase.
- Only IL∞ changes with the gap, roughly as exp(−3.3 µm⁻¹ · gap). The gap sets how strongly the rib couples into the wave under the gold; it does not change the cavity.

## 2. Buffered design (200 nm SiO₂, gap 3.4 µm, x_lift 7 µm): over-etch, slab 275 → 150 nm
`sweep2_buffered_slab_thickness.csv`, `sweep2_buffered_overetch.png`

- Film thickness is fixed at 550 nm and the rib top at 1.0 µm, with 60° walls, so the rib base widens with deeper etch.
- IL drops from 0.026 to 0.0024 dB/cm.
- Vπ·L rises from 2.27 to 2.89 V·cm: +2.6% per 15 nm at first, +27% at 150 nm.
- At 150 nm, IL is identical at x_lift 6.6, 7.0 and 7.4 µm, so there is still no ripple.

## 3. Full etch with no SiO₂ inside the electrodes (`GOLD_OUT = True` in `cells/cell0_etched.py`)
`sweep3_full_etch_gold_at_slab_level.csv`, `sweep3_IL_vs_slab_w_gold_at_slab_level.png`, `sweep3_cross_section_gold_at_slab_level.png`

**Geometry.** Lower block, column and pad form one solid stepped gold body:
- lower block from x = 2.1 to 32.1 µm, 2 µm tall;
- upper part from x = 5 µm, top at 5.875 µm;
- air outside the electrodes.

The slab always ends inside the gold. Gap 4.2 µm, top gap 10 µm.

**Results.**
- **Slab ends between the gap and 14 µm (old gold/SiO₂ edge):** the 28 shared points match the previous sweep with a median difference of 0.03%. The maximum is 2.1%, at slab_w 13.95 µm, right next to where the old SiO₂ started.
- **Past 14 µm:** no flat 0.228 dB/cm plateau any more. The ripples keep going and shrink with the same Airy envelope:
  - IL∞ 0.415 dB/cm, period 0.894 µm (slab-end position), 2α 0.179 /µm, ρ₀ 0.948;
  - at slab_w 40–50 µm, IL is 0.38–0.44 dB/cm.
- **Grid:** steps are 0.1–0.4 µm up to 30 µm, then 1.6 µm. Above 30 µm the 1.6 µm step is close to the 1.79 µm ripple period in slab_w, so the slow wave visible there is aliasing; the dotted envelope gives the true ripple range.
- **Not meshable:** slab_w 4.25 µm (slab end 25 nm from the gold edge).
