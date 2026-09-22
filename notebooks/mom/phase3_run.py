"""Phase 3 driver: periodic Floquet unit cell -> Bloch mode -> (n_m, alpha).

One geometry = one FloquetKernel (rebuilt at t_LN = TFLN - ETCH_DEPTH, per the
Phase 2 standing order -- never the median-etch table) + one meshed unit cell,
etched or unetched.  No fit, no surrogate, no lookup: the dataset is only ever
read to supply geometry and to score the answer.
"""
import time
import numpy as np
import pandas as pd
import stack_params as sp
import mesh_generator as mg
from floquet_greens import FloquetKernel
from bloch_solver import assemble_periodic, bloch_mode, tl_test_vector
from layered_greens import C0

ZS_AU = sp.RS_AU*(1 + 1j)          # good-conductor surface impedance
DATA = "/root/.claude/uploads/f069cebc-0d61-5069-a4b8-cc5b76a72567/51442c2b-FULL_DATASET.xlsx"


def load(path=DATA):
    return pd.read_excel(path)


def cell_for(row, h, etched):
    g = mg.geom_from_row(row)
    m = mg.build_unit_cell(g, h, etched=etched)
    return mg.rwg_basis_cell(m)


def kernel_for(row, du_max, EP=6.0, n_rad=200):
    t_LN = sp.TFLN - row["ETCH_DEPTH"]*1e-6
    return FloquetKernel(t_LN, P=mg.PITCH, EP=EP, n_rad=n_rad, du_max=du_max)


def solve(row, h, etched, fk=None, n0=None, verbose=True):
    """Return (beta, n_m, alpha_dB_cm, cell, fk, timings)."""
    t0 = time.time()
    cell = cell_for(row, h, etched)
    du_max = 1.05*(cell["cent"][:, 0].max() - cell["cent"][:, 0].min()) + 1e-5
    t_mesh = time.time() - t0
    t0 = time.time()
    if fk is None or fk.du_max < du_max:
        fk = kernel_for(row, du_max)
    t_kern = time.time() - t0
    if n0 is None:
        # Self-contained bracketing: scan |g| along real n with the physical
        # test vector and start the complex secant at the dip.  No dataset
        # value is used as a seed, and the converged root does not depend on
        # it in any case.  Cheap because the near-field block is cached after
        # the first assembly.
        y = tl_test_vector(cell)
        ns = np.linspace(1.6, 3.4, 7)
        gs = []
        for n in ns:
            Zt = assemble_periodic(cell, fk, ZS_AU, n*fk.k0)
            gs.append(abs(1.0/(y @ np.linalg.solve(Zt, y))))
        n0 = ns[int(np.argmin(gs))] - 0.02j
        if verbose:
            print("      scan |g|: " + " ".join(f"{n:.2f}:{g:.1e}"
                                                for n, g in zip(ns, gs)))
    b0 = complex(n0)*fk.k0
    t0 = time.time()
    b, hist = bloch_mode(cell, fk, ZS_AU, b0)
    t_eig = time.time() - t0
    nm = b.real*C0/fk.w
    al = abs(b.imag)*8.686/100.0
    if verbose:
        print(f"    {'etched ' if etched else 'unetched'} Nt={len(cell['tris']):5d} "
              f"Ne={len(cell['L']):5d} wrap={cell['n_wrapped']:3d}  "
              f"n_m={nm:.4f} alpha={al:.4f} dB/cm  "
              f"[mesh {t_mesh:.1f}s kern {t_kern:.1f}s eig {t_eig:.1f}s "
              f"{len(hist)} iters]")
    return dict(beta=b, nm=nm, alpha=al, cell=cell, fk=fk,
                t=(t_mesh, t_kern, t_eig), hist=hist)
