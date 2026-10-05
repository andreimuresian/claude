# Bend CPW: analytical model and its references

Cross-section of the electrode bend: Au 2 um (ground 50, gap 4.15, signal 35,
gap 4.15, ground 50 um) on 3.6 um SiO2 / 0.275 um LN slab (ribs removed) /
4.7 um SiO2 / 550 um Si, air above. Materials as in the user's FEM notebook
(Au 4.56e7 S/m, LN eps 28/44, SiO2 3.9, Si 11.7).

| file | what |
|---|---|
| `cpw_analytic.py` | the analytical model, `bend_cpw(f, S, W, Wg, t, layers)` -> Z0, n_m, alpha |
| `bend_fem.py` | the user's femwell/scikit-fem notebook (quasi-static + vector eigensolve, IBC loss), geometry changed to the bend; `qs_only=True` for the quasi-static part |
| `eddy_tensor.py` | reference series impedance R(f), L(f): eddy currents inside the gold, skin depth meshed, no IBC |
| `conv.py` | mesh convergence of `bend_fem.py` at 60 GHz |
| `doe_qs.py`, `doe_eddy.py` | 23-geometry validation set (S 8-70, W 2-16, t 0.5-4, buffer 1-6 um): FEM C, then eddy R, L |
| `sweep_eddy.py` | reference R, L of the bend from 0.1 to 200 GHz |
| `eval_final.py` | analytical model vs references, figures in `results/` |

Reference for Z0, n_m, alpha = eddy-current R, L + FEM quasi-static C
(quasi-TEM). Needs scikit-fem, femwell, gmsh, shapely.

Analytical model:
- C: air above (conformal map, finite grounds) + sidewall parallel plates
  (eps0 t/W per gap) + layers below by the spectral-domain variational method
  (layered admittance by transmission-line recursion, LN anisotropy exact,
  conformal-map slot field as trial function).
- L_ext = 1/(c^2 C_air); R = sqrt(R_dc^2 + (Rs G)^2) with G from Ghione's CPW
  conductor-loss formula; L_int = Rs G / omega.
- dielectric conductance from dC/d(eps) of each layer and its sigma / tan(delta).
