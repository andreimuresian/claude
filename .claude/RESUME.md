# RESUME (Phase 3, TFLN RF MoM) — branch 2D-+-2.5D

## Done
- Ph1 layered Green's fn: 6/6 gates. TE0=2.54141, TM0=3.31373.
- Ph2 finite-line MoM: ABANDONED by user (ill-posed: short unterminated lines,
  no wave ports, zero-thickness vs thick metal). KEPT+validated: assemble()
  reciprocal 1e-16; quasi-static C matches C_base 4-10%; CCW-winding fix;
  vertex-NaN fix; analytic coplanar integrals ~1e-13.
- Ph3 built: mesh_generator.build_unit_cell/rwg_basis_cell (gmsh-periodic,
  Bloch-wrapped RWG); floquet_greens.py (spectral Gaussian Ewald split);
  bloch_solver.py (periodic MPIE + secant eigenvalue on 1/(x^H Z^-1 y)).

## Ph3 blocker (V3.1b: 1e-3 vs 1e-4 target)
Bug FOUND+FIXED: surface-wave poles razor sharp (TM0 k=4163.6, FWHM 0.05,
rel 1.2e-5, sigma_Si=2.5e-4); uniform ku grid (dk=200) stepped over them,
dropped ~40% of spectral integral, looked like E-dependence. Resolving them:
2.8 -> 1e-3 (3000x). Build 280x faster.
Remaining: sensitivity sweep -> harmonics x2 = 0.00, du grid x2 = 1e-6
(spectral side exact), but n_sharp 4->8 moves G_A 1040% => sharp image sum
NOT convergent. Cause: Gaussian split suppresses pole only ~200x
(damp=0.0048 at k_pole), residual surface wave keeps the 1/sqrt(rho) tail;
G_sharp=G_full-G_soft compounds it at large rho. Cannot rebuild sharp from
asymptote either: LN 0.3um => G~ not asymptotic until k>>3e6 >> kmax.
Fix = extract surface-wave residues, sum that lattice part in closed form
(periodic Hankel/H0 Ewald).

## Awaiting user decision
(1) implement residue extraction, or (2) run V3.3 on current ~1e-3 kernel as
cheap reality check (unetched beta_r vs nm_baseline_val, 3%). I recommend (2).

## Rules
Dev+push branch 2D-+-2.5D only; no PR unless asked; commits end with
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com> +
Claude-Session: https://claude.ai/code/session_01HHGr1oNAycW4Z63NZEgXN1
No model id in pushed artifacts. Dataset = test fixture only, never calibrate.
Stop at end of each phase; don't start Phase 4.
