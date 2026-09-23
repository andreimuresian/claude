"""Eigenvalue-search diagnostic for the periodic Bloch solver (Gate 3R.2).

The remediation prompt specified sweeping sigma_min(Z(beta)).  That diagnostic
does not work here and Phase 3 already established why: the EFIE carries a
large loop (divergence-free) near-null subspace whose singular values are O(w)
and almost independent of beta.  With sigma_Si = 2.5e-4 it pins sigma_min at
~4.7e-11 flat from n = 0.5 all the way to n = 232, so a sigma_min(beta) sweep
returns a horizontal line and diagnoses nothing.

The diagnostic that does work is the quantity the solver already root-finds on,

    g(beta) = 1 / (y^T Z(beta)^-1 y),      y = transmission-line test vector,

which projects out the loop subspace and is zero exactly at a mode that carries
longitudinal current.  Sweeping |g| along real n therefore shows one dip per
guided mode in the window.  It is also nearly free: it is the same bracketing
scan the driver runs anyway, just on a finer grid.
"""
import numpy as np
from bloch_solver import assemble_periodic, tl_test_vector


def gscan(cell, fk, Zs, n_lo=1.30, n_hi=3.15, npts=14, y=None, **kw):
    """|g| along real n.  Returns (n, |g|).

    The default window stops at n = 3.15, safely below the TM0 surface-wave
    index (3.309): above it the mode is no longer the guided CPW mode and the
    secant can be dragged into the pole.  Phase 3 scanned to n = 3.40, i.e.
    PAST TM0, which is the flagged risk on row 49."""
    if y is None:
        y = tl_test_vector(cell)
    ns = np.linspace(n_lo, n_hi, npts)
    g = np.empty(npts)
    for i, n in enumerate(ns):
        Z = assemble_periodic(cell, fk, Zs, n*fk.k0, **kw)
        g[i] = abs(1.0/(y @ np.linalg.solve(Z, y)))
    return ns, g


def minima(ns, g, rel=3.0):
    """Interior local minima of |g|, deepest first.

    `rel` keeps only dips that are at least `rel` times below the larger of
    their two neighbours, so a flat shoulder is not reported as a mode."""
    out = []
    for i in range(1, len(ns)-1):
        if g[i] < g[i-1] and g[i] < g[i+1]:
            nb = max(g[i-1], g[i+1])
            if nb/g[i] >= rel:
                out.append((float(ns[i]), float(g[i]), float(nb/g[i])))
    return sorted(out, key=lambda t: t[1])


def fmt(ns, g, label=""):
    L = [f"  {label}"] if label else []
    L.append("      n       |g|")
    for n, v in zip(ns, g):
        L.append(f"   {n:5.3f}  {v:.4e}")
    m = minima(ns, g)
    L.append(f"   local minima (>=3x deep): "
             + (", ".join(f"n={a:.3f} |g|={b:.2e} depth={c:.1f}x" for a, b, c in m)
                if m else "none"))
    return "\n".join(L)
