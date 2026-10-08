# Full-wave periodic cell (work in progress)

## FW1: 2D full-wave mode solver of the plain line (`fw2d.py`, `run_fw1.py`)
Transverse-E FDFD, PML, PMC symmetry plane.  Row 49, PEC, converged (grid and PML):

| GHz | n (CST) | Z ohm (CST) | alpha dB/cm (CST) |
|---|---|---|---|
| 20 | 1.952 (1.969) | 36.39 (36.40) | 0.009 (0.000) |
| 60 | 1.954 (1.972) | 36.37 (36.33) | 0.051 (0.109) |
| 100 | 1.959 (1.972) | 36.33 (36.12) | 0.153 (0.144) |

## FW2: 3D periodic cell (`fw3d.py`, `run_fw2.py`)
Yee FDFD on one 200 um period, Bloch phase along z, PML on the open sides, complex
PARDISO (`pardiso_c.py`).  Real beta -> complex frequency (n, Q).

- Plain cell: reproduces the 2D mode (n 1.9486 vs 1.9542; leakage ~0.052 vs 0.0505 dB/cm).
- Bug found and fixed: the stem slot kept a line of metal nodes on the gap edge,
  a zero-thickness bridge across the cut (tee had no effect, n ~ 1.97).
- Tee cell at 20 GHz (coarse grid, ~310k unknowns, 7 GB, 4 min):
  n = 2.610, tee/plain ratio 1.3485 (CST 1.3484, static cell 1.3498).
- **Open problem: the loss and part of n depend on the domain truncation.**
  - At 20 GHz the tee mode has Q 11-15 (about 3 dB/cm) where CST has ~0.
  - Finer PML does not change it.
  - A larger domain does (n 2.610 -> 2.554, Q 15 -> 11).
  - A second strongly gap-coupled, very lossy mode (n ~ 2.8, signal + pads) sits close by.
  - 60 GHz: n 2.593, Q 10.3; not trustworthy until the 20 GHz loss is fixed.
- Size limit: a 765k-unknown cell needs > 25 GB for the factorization (OOC run filled the disk).

## EME (`eme.py`): abandoned
Bi-orthogonality and junction checks pass, but the quasi-static near field at the slot edges
would need thousands of evanescent modes.
