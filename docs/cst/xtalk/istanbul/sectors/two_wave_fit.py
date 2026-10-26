"""
Odd sector of the Istanbul pair: one mode vs two modes, jointly over 3, 5, 8.75 mm.

Model (per frequency): external port -- junction J -- line of length L -- J -- port.
J is a reciprocal, lossless 3-port (port, mode c, mode x): symmetric unitary,
J = Q diag(e^{j phi}) Q^T, Q real orthogonal (3 angles) -> 6 real parameters.
Line: diag(exp(-gamma_c L), exp(-gamma_x L)). Waves are power waves.

    a1 = (I - R P R P)^{-1} t,  S11 = r + t^T P R P a1,  S21 = t^T P a1
    (J = [[r, t^T], [t, R]], P = propagation, port 2 matched)

gamma_c: free per frequency (n_c, alpha_c). gamma_x: n_x one global constant
(scanned), alpha_x free per frequency. Unknowns per frequency: 6 + 2 + 1 = 9
real, data 12 real. Controls: the same with mode x removed (2-port junction,
3 + 2 = 5 real), and the earlier one-mode fit with a general reciprocal
junction (8 real; sector_fit.py).
"""
import os, sys, numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sector_fit import FILES, sectors, C0

LS = [3.0, 5.0, 8.75]
NP_DB = np.log(10) / 20

def junction(ang, ph):
    Q = Rotation.from_euler("xyz", ang).as_matrix() if len(ph) == 3 else \
        np.array([[np.cos(ang[0]), -np.sin(ang[0])], [np.sin(ang[0]), np.cos(ang[0])]])
    return Q @ np.diag(np.exp(1j * np.asarray(ph))) @ Q.T

def two_port(J, gammas, L):
    r, t, R = J[0, 0], J[1:, 0], J[1:, 1:]
    P = np.diag(np.exp(-np.asarray(gammas) * L * 1e-3))
    M = R @ P @ R @ P
    a1 = np.linalg.solve(np.eye(len(t)) - M, t)
    return r + t @ P @ R @ P @ a1, t @ P @ a1

def residual_vec(S11d, S21d, J, gammas):
    e = []
    for k, L in enumerate(LS):
        s11, s21 = two_port(J, gammas, L)
        e += [s11 - S11d[k], s21 - S21d[k]]
    return np.array(e)

def fit_freq(f, S11d, S21d, nc0, ac0, nx=None, starts=24, rng=None):
    """nx None: one mode. Returns (max |err|, params)."""
    k0 = 2 * np.pi * f / C0
    rng = rng or np.random.default_rng(0)
    two = nx is not None
    def unpack(x):
        if two:
            ang, ph, nc, ac, ax = x[:3], x[3:6], x[6], x[7], x[8]
            g = [ac * 100 * NP_DB + 1j * k0 * nc, ax * 100 * NP_DB + 1j * k0 * nx]
        else:
            ang, ph, nc, ac = x[:1], x[1:3], x[3], x[4]
            g = [ac * 100 * NP_DB + 1j * k0 * nc]
        return junction(ang, ph), g
    def r(x):
        e = residual_vec(S11d, S21d, *unpack(x))
        return np.concatenate([e.real, e.imag])
    best = None
    for s in range(starts):
        if two:
            x0 = np.concatenate([rng.uniform(-np.pi, np.pi, 3), rng.uniform(-np.pi, np.pi, 3),
                                 [nc0 + rng.normal(0, 0.003), ac0, rng.uniform(0.5, 8)]])
            lb = [-np.inf] * 6 + [nc0 - 0.05, 0.0, 0.0]; ub = [np.inf] * 6 + [nc0 + 0.05, 20, 60]
        else:
            x0 = np.concatenate([rng.uniform(-np.pi, np.pi, 1), rng.uniform(-np.pi, np.pi, 2),
                                 [nc0 + rng.normal(0, 0.003), ac0]])
            lb = [-np.inf] * 3 + [nc0 - 0.05, 0.0]; ub = [np.inf] * 3 + [nc0 + 0.05, 20]
        x0 = np.clip(x0, np.array(lb) + 1e-9, np.array(ub) - 1e-9)
        sol = least_squares(r, x0, bounds=(lb, ub), max_nfev=3000)
        if best is None or sol.cost < best.cost:
            best = sol
    e = r(best.x); e = e[:len(e) // 2] + 1j * e[len(e) // 2:]
    return float(np.max(np.abs(e))), best.x

def load():
    data = {}
    for L in LS:
        f, sec = sectors(FILES[L]); data[L] = sec
    return f, data

if __name__ == "__main__":
    f, data = load()
    prev = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sector_fit.npz"))
    odd1 = prev["odd"]                                 # f, maxerr, n, a(dB/cm) from sector_fit
    fsel = np.arange(10e9, 50.01e9, 2.5e9)
    idx = [int(np.argmin(abs(f - x))) for x in fsel]
    get = lambda i: (np.array([data[L]["odd"][0][i] for L in LS]),
                     np.array([data[L]["odd"][1][i] for L in LS]))
    init = lambda i: (np.interp(f[i], odd1[:, 0], odd1[:, 2]), np.interp(f[i], odd1[:, 0], odd1[:, 3]))
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if mode == "scan":
        nxs = np.round(np.arange(1.6, 3.21, 0.1), 2)
        one = [fit_freq(f[i], *get(i), *init(i))[0] for i in idx]
        gen = np.interp(f[idx], odd1[:, 0], odd1[:, 1])
        print(f"one mode, lossless junction (5 real):   median {np.median(one):.4f}")
        print(f"one mode, general junction  (8 real):   median {np.median(gen):.4f}")
        rows = []
        for nx in nxs:
            errs = [fit_freq(f[i], *get(i), *init(i), nx=nx, starts=16)[0] for i in idx]
            rows.append((nx, np.median(errs), np.percentile(errs, 90)))
            print(f"two modes, n_x = {nx:.2f} (9 real):   median {np.median(errs):.4f}  90% {np.percentile(errs, 90):.4f}", flush=True)
        np.savez("two_wave_scan.npz", rows=np.array(rows), one=np.array(one), gen=gen, f=f[idx])
