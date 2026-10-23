# Istanbul pair, 3-D CST at 1, 3, 5, 8.75 mm: what the four lengths say

Scripts: `four_lengths.py` (checks, per-mode gamma from every pair of lengths),
`cascade_test.py` (port + line model per mode, fitted per mesh family, cross-predicted).

## Data quality
| L (mm) | reciprocity | A-B symmetry max S21-S43 | ends |
|---|---|---|---|
| 1 | 2e-6 | -115 dB | asymmetric (S11 vs S22 rms 1.2 dB) |
| 3 | 2e-6 | -91 dB | symmetric |
| 5 | 2e-6 | -85 dB | symmetric |
| 8.75 | 2e-6 | -76 dB | symmetric |
Two mesh/port families: coarse (3, 5 mm; START_POSITION 0.1) and fine (1, 8.75 mm; 0.075).

## Index and index split
* n_even at 30 GHz: 2.104 (3+5) vs 2.080 (1+8.75): the coarse family is 1.2 % higher. Mixed-family pairs are not valid (different port regions).
* dn = n_e - n_o: (1, 8.75) gives 8-11e-3 at 30-50 GHz (dL = 7.75 mm). (3, 5) cannot resolve it: dL = 2 mm gives a phase of ~0.6 deg at 30 GHz, and the result swings by +-10e-3.

## Impedance split delta
Not identifiable from these runs. Per-mode port + line fits reproduce their two lengths exactly but give delta = -6 % ... +6 % with changing sign: with two lengths, the even and odd port regions absorb any difference, so delta and port coupling cannot be separated.

## Length scaling
* FEXT: S41/S21 = A + B L fits all four lengths to -11...-15 dB (25-60 GHz); |B| = 0.9-1.7 x dbeta/2 (dbeta from 1+8.75). Consistent with two modes + a constant port term (which cancels the line term at 1 mm).
* NEXT: |NEXT| ~ L^p with p = 1.9-2.2 from 10 to 35 GHz, over all four lengths and both families (spread of NEXT/L^2: 3-6 dB); it flattens above ~40 GHz. Its phase barely follows 2 beta L. A two-mode uniform line gives NEXT bounded by ~delta/2, oscillating with nulls every c/(2nL): incompatible.

## Can shorter lines model the longer one?
* Raw S-block chaining: no (port regions counted at every junction).
* De-embedded two-mode model (ports + line per mode): through path yes; FEXT within ~3 dB at 25-60 GHz; NEXT no (10-30 dB off outside the fitted lengths).
* Empirical NEXT ~ L^2 holds to 3-6 dB from 10 to 35 GHz only.

## Next
1. Field monitor at 30 GHz (5 or 8.75 mm): |E| in Si/BOX between the lines and around the near-end ports.
2. Boundary test: 5 mm with the model width w = 1 -> 2 mm (lateral PML only 37 um deep). A large NEXT change means substrate waves reflected at the side boundaries.
3. A third coarse-family length (e.g. 7 or 8.75 mm, same mesh and START_POSITION) to fit port term + line inside one family.
