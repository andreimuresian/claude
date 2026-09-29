# Quasi-static 3D unit cell: ΔL, ΔC of the tee-loaded CPW

`qs3d.py` builds one 200 µm cell exactly as the CST Multilayer model: thick metal,
LN slab (0.460 − ETCH) with (lateral 28, vertical 43, along-line 43), SiO₂ 3.9,
Si 11.7, tees in both 70 µm grounds. Two solves per geometry:

- electrostatic → C′;
- high-frequency magnetostatic → L′ (current detour around the tees).

The cell's own L and C distribution (energy per slice) is cascaded into its ABCD
matrix, and the author's extractor (L = Im B/ω, C = Im C/ω) is applied to it.

```
python run5.py          # 5 reference rows -> run5.json   (~3 min, 4 cores)
python conv.py          # grid refinement check on rows 38, 118
```

Checks:
- L′·C′_air·c² = 1.006–1.010 on unetched cells (TEM identity).
- Unetched C′ agrees with the 2D solver to 0.2%.
- The slice cascade equals the uniform formula to 2e-16.
- Doubling the grid moves ΔC and ΔL by ≤ 0.1%.

Results vs the dataset (CST Multilayer lumped deltas):

| row | ΔC err | ΔL err | n_final err | Z₀_final err | time (1 core) |
|---|---|---|---|---|---|
| 118 | −22.9% | −7.1% | −0.13% | −2.16% | 142 s |
| 416 | −14.7% | −2.8% | +0.09% | −0.58% | 145 s |
| 121 | −35.7% | −10.0% | −0.20% | −3.18% | 115 s |
| 38 | −44.3% | −12.3% | −0.60% | −4.58% | 144 s |
| 49 | −46.9% | −14.8% | −0.91% | −6.08% | 51 s |

## Second-order (coupled) correction and open boundary — tested, not sufficient

`coupled.py` adds the magnetic energy of the charging currents of the open
half cell (displacement currents plus conduction to every metal surface,
fingers included) to the lumped C. `python run5_coupled.py` (~9 min, 4 cores):

| row | ΔC err, cascade | ΔC err, coupled | n_final err | Z₀_final err |
|---|---|---|---|---|
| 118 | −22.9% | −19.2% | −0.13% → −0.30% | −2.16% → −2.00% |
| 416 | −14.7% | −14.6% | +0.09% → +0.09% | −0.58% → −0.58% |
| 121 | −35.7% | −30.5% | −0.20% → −0.42% | −3.18% → −2.97% |
| 38 | −44.3% | −36.7% | −0.60% → −0.94% | −4.58% → −4.25% |
| 49 | −46.9% | −38.8% | −0.91% → −1.35% | −6.08% → −5.65% |

The term enters as ω²C_h(L_e − L_h) ≈ 0.05–0.07 of C, so it cannot supply the
~5% of the cell C missing on row 49. On the no-slot cells L_e/L_h = 0.364–0.391
instead of 1/3 (box charge and non-TEM field of the stack); the etched − no-slot
difference removes this.

`python frame_check.py 49 118`: floating (open-equivalent) far frame instead of
the grounded box, which holds 13% of the signal charge. ΔC err: row 49
−46.9% → −47.1%, row 118 −22.9% → −18.9%.

Open: the ΔC gap (15–47%, growing with finger size) is zeroth order. Candidate
on the reference side: D2 in `../validation/GEOMETRY_SPEC.md` (etched grounds
not in the 5 µm mesh group).
