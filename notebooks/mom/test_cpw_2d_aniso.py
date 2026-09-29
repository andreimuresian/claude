"""Exactness checks for the anisotropic 2D FV solver (cpw_2d_static).

T1  lateral plates, two layers: C = sum_k ex_k H_k / d, whatever ez is.
T2  vertical plates, layered:   1/C = (1/W) sum_k dz_k / ez_k, whatever ex is.
T3  (a, a) as a tuple equals the scalar a.
T4  regression: isotropic 34.7 reproduces the pre-change solver bit-for-bit
    (reference values saved from git HEAD before the edit).
Run: python test_cpw_2d_aniso.py
"""
import numpy as np

import cpw_2d_static as cs
import stack_params as sp

rng = np.random.default_rng(1)


def t1_lateral():
    dx = rng.uniform(0.5, 2.0, 40); dz = np.array([1.0]*6 + [2.5]*4)
    nz, nx = len(dz), len(dx)
    ex = np.where(np.arange(nz)[:, None] < 6, 28.0, 3.9) * np.ones((nz, nx))
    ez = rng.uniform(1, 1000, (nz, nx))                # must not matter
    sig = np.zeros((nz, nx), bool); gnd = np.zeros((nz, nx), bool)
    sig[:, 0] = True; gnd[:, -1] = True
    C = cs.fv_capacitance(dx, dz, ex, ez, sig, gnd, frame_dirichlet=False)
    d = dx.sum() - dx[0]/2 - dx[-1]/2                  # between conductor centres
    exact = (28.0*6*1.0 + 3.9*4*2.5)/d
    return abs(C/exact - 1)


def t2_vertical():
    dx = np.full(30, 1.0); dz = rng.uniform(0.3, 2.0, 25)
    nz, nx = len(dz), len(dx)
    ezc = np.where(np.arange(nz) < 12, 43.0, 3.9)       # LN-like over SiO2-like
    ez = ezc[:, None]*np.ones((nz, nx))
    ex = rng.uniform(1, 1000, (nz, nx))                # must not matter
    sig = np.zeros((nz, nx), bool); gnd = np.zeros((nz, nx), bool)
    sig[0, :] = True; gnd[-1, :] = True
    C = cs.fv_capacitance(dx, dz, ex, ez, sig, gnd, frame_dirichlet=False)
    path = dz.copy(); path[0] /= 2; path[-1] /= 2
    exact = dx.sum()/np.sum(path/ezc)
    return abs(C/exact - 1)


def geom(row):
    import pandas as pd
    d = pd.read_excel('data/EVALUATED_FULL_LHS_DATASET.xlsx')
    r = d.loc[row]
    return (r.WS*1e-6, r.GAP*1e-6, 70e-6, r.MTX*1e-6, sp.TFLN - r.ETCH_DEPTH*1e-6,
            sp.BOX_H, sp.SI_H)


KW = dict(hmax=6e-6, pad_x=1200e-6, pad_up=800e-6)


def t3_tuple():
    g = geom(118)
    a = cs.solve_cs(*g, 34.7, sp.EPS_SIO2, sp.EPS_SI, **KW)[:2]
    b = cs.solve_cs(*g, (34.7, 34.7), sp.EPS_SIO2, sp.EPS_SI, **KW)[:2]
    return max(abs(a[0]/b[0] - 1), abs(a[1]/b[1] - 1))


REF = {118: (1.6969143108992776e-10, 4.3349937092562706e-11),
       416: (1.9113818915728476e-10, 6.432812462493364e-11),
       49: (1.797358679772253e-10, 4.7279308144539e-11)}


def t4_regression():
    err = 0.0
    for row, (C0, Ca0) in REF.items():
        C, Ca = cs.solve_cs(*geom(row), sp.EPS_LN, sp.EPS_SIO2, sp.EPS_SI, **KW)[:2]
        err = max(err, abs(C/C0 - 1), abs(Ca/Ca0 - 1))
    return err


if __name__ == '__main__':
    for name, fn, tol in (('T1 lateral plates, ex only', t1_lateral, 1e-10),
                          ('T2 vertical plates, ez only', t2_vertical, 1e-10),
                          ('T3 (a,a) == a', t3_tuple, 1e-12),
                          ('T4 regression vs pre-change solver', t4_regression, 1e-10)):
        e = fn()
        print(f'{name:38s} rel. error {e:.1e}  {"PASS" if e < tol else "FAIL"}')
        assert e < tol, name
