# Final deck: `VPI_Lisbon_Lifted_final.pptx` (20 slides)

| slides | content | source |
|---|---|---|
| 1–5 | problem and buffered solution | the meeting deck, unchanged |
| 6–14 | slab etching (failed attempt) | slides 1–9 of the slab-etch deck, unchanged |
| 15 | section divider | |
| 16 | buffered design, over-etch: slab 275 → 150 nm, gap 3.4 µm | `../three_sweeps/` |
| 17 | standard lifted: x_lift sweep at gap 3.9 / 4.2 / 5.0 µm | `../three_sweeps/` |
| 18 | full etch with no SiO₂ inside the electrodes vs the previous geometry | `../three_sweeps/` |
| 19 | why the slab end and the gold edge act the same | 1D stack indices, `src/stack_idx.py` |
| 20 | conclusions | |

The appendix and the "Recommendation" slide of the slab-etch deck are left out. The recommendation used gap 3.2 µm and is replaced by the conclusions slide, which uses gap 3.4 µm.

Explanations are in the speaker notes. `src/build_final.py` rebuilds the deck from the two uploaded decks, the CSVs and the figures.
