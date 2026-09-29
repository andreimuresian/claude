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
