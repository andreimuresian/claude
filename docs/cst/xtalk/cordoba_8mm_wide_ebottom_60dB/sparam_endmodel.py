"""
Multimode line with end junctions, fitted to the S-parameters (-44.5 dB run). Pre-registered test (stated before
running): fit on the 12 monitor frequencies only, predict NEXT (S31) and FEXT (S41) on the dense grid 1-60 GHz;
success = median complex relative error < 0.3 for both AND below half that of a cubic spline through the same 12 points.

Symmetric 4-port (ports 1 A near, 2 A far, 3 B near, 4 B far): even/odd 2-ports
  S11 = (Se11 + So11)/2, S31 = (Se11 - So11)/2, S21 = (Se21 + So21)/2, S41 = (Se21 - So21)/2.
Each 2-port: port -- junction -- three modes (even: cpw, slot, strips-bottom; odd: cpw, slot, A-vs-B) propagating
with the eigen gamma(f) (+ a constant index correction dn per mode, fitted) -- the same junction (z-symmetric) -- port.
Junction (reciprocal): port reflection rho, port-to-mode coupling t (3), mode-to-mode reflection R (3x3 symmetric);
each a polynomial of order K in f. With P = diag(exp(-gamma L)):
  a+ = (I - R P R P)^-1 t,  a- = R P a+,  S21 = t . P a+,  S11 = rho + t . P a-.
Residuals: complex errors of S11, S21, S31, S41, each divided by that parameter's magnitude (B quantities count as
much as A's). Multi-start Levenberg-Marquardt.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../cordoba_8mm/eigen_w2mm_mag_ebottom_sweep"))
import numpy as np, skrf as rf
from scipy.optimize import least_squares
from scipy.interpolate import CubicSpline
import sweepfit as S

K = int(os.environ.get("K", "0"))
net = rf.Network(os.path.join(HERE, "LINEA_8MM_625UM_PITCH_CORDOBA_OAD_1port_E-fondo_-minus_60_dB.s4p"))
fG = net.f / 1e9; sel = fG >= 1.0; fG = fG[sel]; Sm = net.s[sel]
MEAS = {"S11": Sm[:, 0, 0], "S21": Sm[:, 1, 0], "S31": Sm[:, 2, 0], "S41": Sm[:, 3, 0]}
BLK = {"e": ["e_cpw", "e_slot", "e_sb"], "o": ["o_cpw", "o_slot", "o_AvsB"]}
GAM0 = {m: np.array([S.DISP[m].alpha(f) + 1j * 2 * np.pi * f * 1e9 * S.DISP[m].n_of(f) / S.C0 for f in fG])
        for b in BLK.values() for m in b}
IU = np.triu_indices(3)
NPB = (1 + 3 + 6) * (K + 1)            # complex params per block
NP = 2 * 2 * NPB + 6                   # real params: two blocks (re, im) + 6 index corrections


def unpack(p, idx_f):
    t = (fG[idx_f] - 30.0) / 30.0
    out = {}; k = 0
    for b in ("e", "o"):
        c = p[k:k + 2 * NPB].reshape(2, NPB); k += 2 * NPB; c = c[0] + 1j * c[1]
        c = c.reshape(10, K + 1); poly = sum(c[:, j][None, :] * t[:, None] ** j for j in range(K + 1))  # (nf,10)
        rho = poly[:, 0]; tv = poly[:, 1:4]; R = np.zeros((len(t), 3, 3), complex)
        R[:, IU[0], IU[1]] = poly[:, 4:10]; R[:, IU[1], IU[0]] = poly[:, 4:10]
        out[b] = (rho, tv, R)
    dn = p[k:k + 6]
    return out, dn


def model(p, idx_f):
    blocks, dn = unpack(p, idx_f); res = {}; i = 0
    for b, modes in BLK.items():
        rho, tv, R = blocks[b]
        g = np.stack([GAM0[m][idx_f] + 1j * 2 * np.pi * fG[idx_f] * 1e9 * dn[i + j] / S.C0 for j, m in enumerate(modes)], 1)
        i += 3
        P = np.exp(-g * S.L * 1e0)
        PR = P[:, :, None] * np.eye(3)[None]
        M = np.eye(3)[None] - R @ PR @ R @ PR
        ap = np.linalg.solve(M, tv[:, :, None])[:, :, 0]
        am = (R @ (P * ap)[:, :, None])[:, :, 0]
        res[b + "21"] = np.sum(tv * P * ap, 1); res[b + "11"] = rho + np.sum(tv * P * am, 1)
    return {"S11": 0.5 * (res["e11"] + res["o11"]), "S31": 0.5 * (res["e11"] - res["o11"]),
            "S21": 0.5 * (res["e21"] + res["o21"]), "S41": 0.5 * (res["e21"] - res["o21"])}


def resid(p, idx_f):
    m = model(p, idx_f); r = []
    for k in MEAS:
        d = MEAS[k][idx_f]; e = (m[k] - d) / abs(d); r += [e.real, e.imag]
    return np.concatenate(r)


def fit(idx_f, starts=30, seed=0):
    rng = np.random.default_rng(seed); best = None
    for s in range(starts):
        p0 = rng.standard_normal(NP) * 0.1; p0[-6:] = 0.0
        # sensible start: CPW couples strongly to the port, other couplings small
        for b in range(2):
            base = b * 2 * NPB; p0[base + 1 * (K + 1)] = 0.9
        try:
            r = least_squares(resid, p0, args=(idx_f,), method="lm", max_nfev=4000)
        except Exception:
            continue
        if best is None or r.cost < best.cost:
            best = r
    return best


def err(pred, k, idx):
    d = MEAS[k][idx]; return np.median(abs(pred - d) / abs(d))


if __name__ == "__main__":
    mon = np.array([np.argmin(abs(fG - f)) for f in S.FTD])
    dense = np.setdiff1d(np.arange(len(fG)), mon)
    print(f"K = {K}: {NP} real parameters; 12-point fit has {12*8} real data; dense grid {len(dense)} points")
    for lab, idx in (("fit on 12 monitor frequencies", mon), ("fit on every 4th point (descriptive check)", np.arange(0, len(fG), 4))):
        r = fit(idx, starts=30 if len(idx) < 50 else 8)
        m = model(r.x, np.arange(len(fG)))
        print(f"\n{lab}: cost {r.cost:.3g}; index corrections dn = " + " ".join(f"{v:+.4f}" for v in r.x[-6:]))
        print("   median complex rel. error   on fitted points | on the other dense points | spline from the same points")
        for k in MEAS:
            sp = CubicSpline(fG[idx], MEAS[k][idx])(fG[np.setdiff1d(np.arange(len(fG)), idx)]) if len(idx) < 400 else None
            other = np.setdiff1d(np.arange(len(fG)), idx)
            print(f"   {k}: {err(m[k][idx], k, idx):.3f} | {err(m[k][other], k, other):.3f} | "
                  f"{err(sp, k, other):.3f}")
        if len(idx) == 12:
            np.save(os.path.join(HERE, f"sparam_endmodel_K{K}_params.npy"), r.x)
            import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 2, figsize=(11, 4))
            for a, k in zip(ax, ("S31", "S41")):
                a.plot(fG, 20 * np.log10(abs(MEAS[k])), color="0.6", lw=1, label="TD (dense)")
                a.plot(fG, 20 * np.log10(abs(m[k])), color="#2a78d6", lw=1.3, label=f"end model, fitted at 12 points (K={K})")
                a.plot(fG, 20 * np.log10(abs(CubicSpline(fG[idx], MEAS[k][idx])(fG))), "--", color="#eb6834", lw=1, label="spline through 12 points")
                a.plot(fG[idx], 20 * np.log10(abs(MEAS[k][idx])), "o", color="k", ms=4)
                a.set_title({"S31": "NEXT", "S41": "FEXT"}[k], fontsize=10); a.set_xlabel("f (GHz)"); a.set_ylabel("dB"); a.grid(alpha=0.3)
            ax[0].legend(fontsize=7, frameon=False); fig.tight_layout()
            fig.savefig(os.path.join(HERE, f"sparam_endmodel_K{K}.png"), dpi=150)
