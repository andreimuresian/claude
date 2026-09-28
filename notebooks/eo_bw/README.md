# 2.5 mm vs 14 mm CST lines — EO bandwidth discrepancy

Design `DESIGN_JEREZ_V1_suspe_siliconetch_275`, CST time domain, two lengths.
Settings: device L = 14 mm, R_t = 55 Ω, Z_s = 50 Ω, n_g = 2.27.

```
python test_tline.py            # exactness checks on synthetic lines
python compare_2p5_vs_14mm.py   # report + eo_bw_2p5_vs_14mm.png/.json
```

The runs differ in more than `w` (file headers):

| | L | NCELL | START_POSITION | w | unloaded share |
|---|---|---|---|---|---|
| short | 2.5 mm | 11 | 0.15 mm | 180 µm | 12 % |
| long | 14 mm | 69 | 0.10 mm | 200 µm | 1.4 % |

## Result

| source of γ, Z_c | EO 3 dB BW at 14 mm |
|---|---|
| 2.5 mm line, extrapolated | 26.9 GHz |
| 14 mm line | 56.1 GHz |
| 2.5 mm line, ends de-embedded, extrapolated | > 80 GHz |
| two-line (2.5, 14) γ + 14 mm Z_c | 55.5 GHz |

## Diagnosis — two separate effects

**1. The collapse to 26.9 GHz is an extraction artefact (certain).**
The 2.5 mm line has half-wave resonances (βL = kπ) at 26.4, 52.8, 79.2 GHz.
There B and C of the ABCD matrix both go to zero, so Z_c = √(B/C) and
acosh((A+D)/2) are 0/0. For a *uniform* line this is still exact
(`test_tline.py` passes through those resonances at 1e-12). For this line it
isn't: 12 % of it is unloaded CPW plus the junctions to the loaded section.
At each resonance that non-uniformity takes over Z_c, which swings from
77 to 35 Ω around 27 GHz. Extrapolated to 14 mm, that swing becomes a fake
notch at 27 GHz, and the notch is the "bandwidth".

- Attribution: the 2.5 mm Z_c alone gives 26.8–26.9 GHz whichever line α
  and β come from.
- Model check: the 14 mm line's γ, Z_c plus 0.15 mm unloaded ends
  regenerate the same glitches, and 26.8 GHz.
- De-embedding: removing the ends from the 2.5 mm file alone (smoothness
  criterion, no 14 mm input) removes the glitches. Z_c std falls from
  10.9 to 2.2 Ω.

The 14 mm line has the same mechanism: Z_c dips every ~4.7 GHz. It is
damped by the line's own loss, but still moves its BW between 51.5 and
56.4 GHz depending on how the ends are de-embedded.

**2. The α per unit length genuinely differs between the two runs (unresolved).**
After de-embedding, the 2.5 mm α is 30–55 % *lower* than the 14 mm α
(40 GHz: 1.5 vs 3.3 dB/cm; 70 GHz: 2.9 vs 5.9 dB/cm). Four different end
models all leave it there, and the 14 mm α moves by at most 1 %. So the
gap is in the raw |S21| of the two simulations, not in the extrapolation
math. Two lengths cannot say which run is right. The candidates:

- the 14 mm run is over-lossy (for example a coarser mesh in the longer
  model);
- the short run under-captures loss (radiated or leaky energy not yet
  built up or re-captured — the same direction as the thesis's own TD test,
  where 400 µm → 600 µm → N+1−N gave 1.83 → 2.19 → 2.93 dB/cm);
- the w = 180 vs 200 µm difference.

## Next atomic checks (in CST)

1. Compare the mesh summaries of the two projects: cell count, smallest and
   largest step, lines per wavelength, mesh line ratio limit.
2. Re-run one length so that the two runs differ only in L: same `w`, same
   `START_POSITION`, same fixed absolute mesh steps.
3. Run a third length (e.g. 5 or 7 mm) with those identical settings. Then
   check whether αL is linear in L.
