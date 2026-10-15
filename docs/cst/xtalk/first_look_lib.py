"""First look at the coupled 1 mm pair (LINEA0_1MM_200UM_PITCH.s4p). Unvalidated: one length."""
import sys, numpy as np


import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

def load4(fn):
    rows = [l.split() for l in open(fn) if l.strip() and l[0] not in "!#"]
    vals = np.array([float(x) for r in rows for x in r])
    vals = vals.reshape(-1, 1 + 32)
    f = vals[:, 0]*1e9
    m, p = vals[:, 1::2], np.deg2rad(vals[:, 2::2])
    S = (m*np.exp(1j*p)).reshape(-1, 4, 4)   # Touchstone 4-port: row-major
    return f, S
