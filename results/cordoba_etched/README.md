# Cordoba (non-lifted) electrodes with an etched LN slab vs the filled lifted design

Gap 4.2 um, 1575 nm, full slab etch, slab_w 4.4 -> 14.4 um in 0.1 um steps. The slab ends inside the gold
for slab_w > 4.2 um. The study adds 6.75 and 10.05 um as smoke tests, for 103 points in total.

## Notebook
`VPI_interface_optimized_Cordoba_etched_slab.ipynb` (repo root, executed at SLAB_W = 10 um) is the attached Cordoba
notebook with:
- **Cell 0** replaced by `cells/cell0_cordoba_etched.py`.
  - New parameter `SLAB_W`. The gold fills the etched region down to the BOX, and the electrode top stays at
    slab + 2 um. `SLAB_W >= DEV_W` (e.g. 1e3) gives the original unetched design.
  - GAP is now 4.2 um (it was 4.15).
  - Materials, mesher and refinement are the same as the etched lifted cell (`cell0_etched.py`), so
    electrode shape is the only difference:
    - materials: Sellmeier LN/SiO2, Johnson & Christy gold at `wl`;
    - femwell gmsh size-option fix;
    - 12 nm gold skin and 6 nm corner patches.
- **Cells 1, 2, 4** aligned with the etched lifted notebook: quadrature order 4, TE unipolarity filter 0.85.
- `build_nb_c.py` regenerates the notebook from the attached original.

## Results (`cordoba_etched_slab_w_sweep.csv`, `cordoba_vs_filled_lifted_IL_vs_slab_w.png`)
- **vs filled lifted** (no SiO2 in the electrodes, sweep 3), 19 shared slab_w:
  - IL: median |dIL| 0.04 %, max 0.28 %.
  - Vpi*L: max difference 0.03 %.
- **vs lifted etched slab with the SiO2 lift**, 60 shared points: median 0.05 %.
  - The max, 1.5 %, is at slab_w 13.8 um. There the slab end is less than 0.4 um from that design's
    gold/SiO2 edge at x = 7 um, which the Cordoba and filled designs do not have.
- **Ripple:** period 1.80 um in slab_w (0.898 um of cavity length), 2alpha 0.172/um.
  - Fitted IL_inf 0.415 dB/cm.
  - Cordoba without etch: 0.4163 dB/cm, Vpi*L 2.267 V*cm.
- **Cladding height:** 15 um vs 7.6 um air gives the same IL at slab_w 10.05 (0.3872 dB/cm).
- **Conclusion:** the shape of the electrode above the slab (flat 2 um block vs stepped/lifted) has no effect
  on the IL. Only the gold that meets the LN slab and the slab end matter.
- **Mesh note:** slab_w 6.1 um first failed in gmsh (corner-patch edge on the fine-BOX edge). The cell now shrinks
  the patch to 40 nm in that one case.
