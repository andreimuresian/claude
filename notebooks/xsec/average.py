"""Length-weighted average of the section L, C, R, G (the author's slides).

    X_eff = (l_A X_A + l_B X_B + l_C X_C) / P,   X in {L, C, R, G}
    n = c sqrt(L C),  Z0 = sqrt(L / C),  alpha = R / (2 Z0) + G Z0 / 2

Section lengths are fixed by the tee (xsec2d.section_lengths); nothing is fitted.
Two ways to report the result:
  absolute : n, Z0, alpha of the averaged line, entirely from the 2D code;
  additive : the dataset baseline plus the 2D perturbation,
             L = L_base + (L_eff - L_C),  C = C_base + (C_eff - C_C),
             alpha = alpha_base + (alpha_eff - alpha_C),
             the same decomposition the dataset's final values use.
"""
import os

import numpy as np
import pandas as pd

import xsec2d as x

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "mom", "data", "EVALUATED_FULL_LHS_DATASET.xlsx")
_D = None


def load_rows():
    global _D
    if _D is None:
        _D = pd.read_excel(DATA)
    return _D


def combine(r, lines, P=200.0):
    """lines: {'A','B','C'} -> dict(L, C, R, G) per unit length (SI)."""
    ls = x.section_lengths(r.L1, r.L2, P)
    eff = {k: sum(ls[s] * lines[s][k] for s in "ABC") / P for k in ("L", "C", "R", "G")}
    n, Z, a = x.line_fom(**eff)
    nC, ZC, aC = x.line_fom(**lines["C"])
    Lb = r.z0_baseline_val * r.nm_baseline_val / x.C0
    Cb = r.nm_baseline_val / (r.z0_baseline_val * x.C0)
    L = Lb + eff["L"] - lines["C"]["L"]
    C = Cb + eff["C"] - lines["C"]["C"]
    return dict(n=n, Z0=Z, alpha=a,
                n_add=x.C0 * np.sqrt(L * C), Z0_add=np.sqrt(L / C),
                alpha_add=r.alpha_baseline_val + a - aC,
                nC=nC, Z0C=ZC, alphaC=aC, **{f"w{s}": ls[s] / P for s in "ABC"})


def average(r, qs, finger):
    """Quasi-static sections; finger = 'gnd' (slides: the section is a standalone
    line, the finger carries current) or 'float' (the finger carries no net
    current; its C stays grounded)."""
    lines = {s: x.qs_lines(qs[s], finger if s == "B" else "gnd") for s in "ABC"}
    return combine(r, lines)
