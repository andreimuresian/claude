# Bend CPW: analytical model and its references

Cross-section of the electrode bend: Au 2 um (ground 50, gap 4.15, signal 35,
gap 4.15, ground 50 um) on 3.6 um SiO2 / 0.275 um LN slab (ribs removed) /
4.7 um SiO2 / 550 um Si, air above. Materials as in the user's FEM notebook
(Au 4.56e7 S/m, LN eps 28/44, SiO2 3.9, Si 11.7).

## Files

| file | what |
|---|---|
| `cpw_analytic.py` | the analytical model, `bend_cpw(f, S, W, Wg, t, layers)` -> Z0, n_m, alpha (research version; the GUI uses the identical copy in `mzm_interconnect/bend_cpw/`) |
| `cpw_galerkin.py` | capacitance: spectral-domain Galerkin on zero-thickness strips with finite grounds, + thickness from boundary elements |
| `bem_pec.py` | boundary elements: exact PEC surface current of thick electrodes, C_air, converged IBC resistance, corner amplitudes |
| `corner_constant.py` | finite-skin-depth correction at a right-angle corner, from an isolated square bar (not from the CPW set) |
| `corner_reactance.py` | the same bar for the reactance: c_R = 0.70 is constant, c_X is not (an O(delta) term), so L_int is left at R_hf / w |
| `eddy_tensor.py` | reference series impedance R(f), L(f): current solved inside the gold (skin + proximity effect), no IBC |
| `peec2d.py` | independent check of `eddy_tensor.py`: partial-element (filament) integral equation, free-space Green's function, no mesh outside the metal |
| `verify_coax.py` | check of `eddy_tensor.py` against the exact Bessel-function impedance of a gold coax |
| `fullwave_metal.py` | the notebook's vector mode solver with the gold meshed as a conductor (eps = 1 - j sigma / w eps0): full-wave, no IBC, no quasi-static step |
| `bend_fem.py` | the user's femwell/scikit-fem notebook (quasi-static + vector eigensolve, IBC loss), geometry changed to the bend |
| `conv.py` | mesh convergence of `bend_fem.py` at 60 GHz |
| `doe_qs.py`, `doe_eddy.py` | 23-geometry validation set (S 8-70, W 2-16, t 0.5-4, buffer 1-6 um): FEM C, then reference R, L |
| `sweep_eddy.py` | reference R, L of the bend from 0.1 to 200 GHz |
| `comsol_rows.py` | reference R' for the 13 COMSOL rows of the notebook, vs their IBC attenuation |
| `eval_final.py` | analytical model vs references, figures in `results/` |
| `doe_design.py`, `eval_design.py` | the inverse-design space (S 30-40, W 4-5, Wg 50-60, t 2 um, 33 geometries, 1-200 GHz): reference, then line model vs reference |
| `notebook/unetched_nmZ0_aRF_Claude_v2.ipynb` | the user's notebook with cell [6]: R' and L_int from the current inside the gold |

Needs scikit-fem, femwell, gmsh, shapely (sympy only to re-derive the PEEC kernel).

## Reference

Z0, n_m, alpha = R, L from the current inside the gold (`eddy_tensor.py`)
+ C from the FEM quasi-static solve (quasi-TEM transmission line,
gamma = sqrt((R + jwL)(G + jwC))).

The conductor solve is Maxwell's equations in the cross-section with two
approximations, both quantified: displacement current inside the gold
(sigma / (w eps0) ~ 1e7 at 60 GHz) and propagation along z inside the metal
(beta^2 delta^2 ~ 1e-7) are dropped. Nothing is assumed about skin depth vs
thickness or corner radius. Checks:

1. exact solution (coax, Bessel functions): `verify_coax.py`;
2. independent numerical method (PEEC): `peec2d.py`, <= 0.13 % from 1 to 200 GHz;
3. full-wave with the gold meshed, in the notebook's own formulation:
   `fullwave_metal.py`, alpha 4.595 vs 4.598 dB/cm at 60 GHz (also 10, 160 GHz);
4. exact DC resistance; mesh convergence.

## Why the IBC under-estimates

The IBC loss integral needs the PEC surface current, which is singular at the
electrode corners (J/I ~ r^-1/3). The integral is finite, but on a volume
mesh it converges as h^(1/3): each halving of the corner element adds ~3 %.
At the notebook's corner mesh the result is 10-14 % low. Converged with
boundary elements graded to 1e-7 of the thickness, the IBC limit is 8 % HIGH
for the bend and 2 % high for the notebook geometry at 60 GHz: the IBC treats
the corner as two flat half-spaces and over-counts the corner current, which
in the real metal spreads over a skin depth. The two errors partly cancel at
practical meshes.

## Analytical model

- C: zero-thickness strips with finite grounds on the layered substrate by the
  spectral-domain Galerkin method (charge basis with the 1/sqrt edge
  singularity, layered Green's function by transmission-line recursion, LN
  anisotropy exact); exact in air (conformal map to 1e-8). Thickness:
  C += C_air,thick(BEM) - C_air,thin. Against the mesh-converged FEM of the
  bend: C -0.28 %, C_air -0.002 %. (The earlier conformal / single-trial
  spectral version, `capacitance_model="sd"`, was +0.05..+5 % high.) The
  notebook's default mesh gives C +0.18..+0.25 % high (FEM energy bound).
- R: exact surface current of the thick electrodes (top, bottom, sidewalls)
  from boundary elements, on the electrodes shrunk by delta/2 (receding wall),
  minus c K^2 delta^(1/3) per corner (c = 0.70 from the square bar);
  R = sqrt(R_dc^2 + R_hf^2), L_int = R_hf / w.
- Below t/delta ~ 6.5 (60 GHz for 2 um gold), where the skin depth is not small
  against the gold, R and L come from the current solved inside the electrodes
  by the filament (PEEC) integral equation of `peec2d.py`, coarse (~700
  filaments, one eigendecomposition then any number of frequencies); used
  alone below t/delta = 3.8, blended above. In the design space this took the
  alpha error at 1-20 GHz from 4-6 % to < 0.9 % (`eval_design.py`).
- Dielectric conductance from dC/d(eps) of each layer and its sigma / tan(delta).
