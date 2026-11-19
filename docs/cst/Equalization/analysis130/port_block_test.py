"""Are the touchstone ripples in alpha / Zc a line property or a port effect?
Test: line = uniform section with gamma from the FIELD route (smooth) and Zc = smooth physical fit of the touchstone Zc.
Port = lumped block at each end: series inductance Ls then shunt capacitance Cp (mirrored at port 2), 2 real
parameters fitted to the measured L+S touchstone (complex S11, S21, 1-130 GHz). The model S-matrix is then put through
the SAME ABCD extraction as the touchstone (uniform-line assumption). If the ripples and the n_m offset reappear, they
come from the ports, not from the line.  Outputs: port_block_test.png, printed numbers."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from mzm_interconnect.physics import C0, fit_impedance_physical, fit_impedance_imag
from mzm_interconnect.extractor import extract_line_fit
d = np.load(os.path.join(HERE, "ls_extraction_130.npz")); L = 3.24e-3
net = rf.Network(os.path.join(HERE, "..", "L+S", "130 GHz", "BASELINE - L+S - 130 GHz.s2p"))
ts = extract_line_fit(os.path.join(HERE, "..", "L+S", "130 GHz", "BASELINE - L+S - 130 GHz.s2p"), 3.24)
f = net.f / 1e9; k = (f >= 1); f = f[k]; Sm = net.s[k]; w = 2 * np.pi * f * 1e9
g = np.interp(f, d["F"], d["aF"]) * 100 / 8.686 + 1j * np.interp(f, d["F"], d["nF"]) * w / C0
Z = fit_impedance_physical(f, *ts.popt_zre) + 1j * fit_impedance_imag(f, *ts.popt_zim)
def abcd(Ls, Cp, gg=g):
    one, zero = np.ones_like(f), np.zeros_like(f)
    Pser = np.array([[one, 1j * w * Ls], [zero, one]]).transpose(2, 0, 1)
    Psh = np.array([[one, zero], [1j * w * Cp, one]]).transpose(2, 0, 1)
    T = np.array([[np.cosh(gg * L), Z * np.sinh(gg * L)], [np.sinh(gg * L) / Z, np.cosh(gg * L)]]).transpose(2, 0, 1)
    return Pser @ Psh @ T @ Psh @ Pser
def resid(p):
    S = rf.network.a2s(abcd(p[0] * 1e-12, p[1] * 1e-15), 50.0)
    e = np.concatenate([(S[:, 0, 0] - Sm[:, 0, 0]), (S[:, 1, 0] - Sm[:, 1, 0])]); return np.r_[e.real, e.imag]
p = least_squares(resid, [5, 5]).x
print(f"fitted port block: Ls = {p[0]:.2f} pH, Cp = {p[1]:.2f} fF;  rms |S error| {np.sqrt(np.mean(resid(p)**2)):.4f}"
      f"  (line alone: {np.sqrt(np.mean(resid([0,0])**2)):.4f})")
def extract(T):
    A, B, C = T[:, 0, 0], T[:, 0, 1], T[:, 1, 0]; Zc = np.sqrt(B / C); Zc = np.where(Zc.real < 0, -Zc, Zc); e = A + B / Zc
    return np.log(abs(e)) / L * 8.686 / 100, np.unwrap(np.angle(e)) / L * C0 / w, Zc
aM, nM, ZM = extract(abcd(p[0] * 1e-12, p[1] * 1e-15))
aT, nT, ZT = np.interp(f, d["fT"], d["aT"]), np.interp(f, d["fT"], d["nT"]), np.interp(f, d["fT"], d["ZT"].real)
print(f"n_m offset of the model extraction vs line n_m: {np.mean(nM - np.interp(f, d['F'], d['nF'])):+.4f} (touchstone: {np.mean(nT - np.interp(f, d['F'], d['nF'])):+.4f})")
print(f"alpha: rms (model extraction - touchstone extraction) {np.sqrt(np.mean((aM-aT)**2)):.3f} dB/cm; rms (fields - touchstone) {np.sqrt(np.mean((np.interp(f,d['F'],d['aF'])-aT)**2)):.3f}")
print(f"Re Zc: rms (model extraction - touchstone extraction) {np.sqrt(np.mean((ZM.real-ZT)**2)):.3f} ohm")
np.savez(os.path.join(HERE, "port_block_test.npz"), f=f, aM=aM, nM=nM, ZM=ZM, p=p)
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
for a, (ym, yt, yf, lab) in zip(ax, ((aM, aT, d["aF"], "α (dB/cm)"), (nM, nT, d["nF"], "n_m"), (ZM.real, ZT, d["ZF"].real, "Re Zc (Ω)"))):
    a.plot(f, yt, "k-", lw=1.2, label="touchstone extraction"); a.plot(f, ym, "--", color="#2a78d6", lw=1.3, label="smooth line + port blocks, same extraction")
    a.plot(d["F"], yf, "o", ms=2.5, color="#eb6834", label="fields"); a.set_ylabel(lab); a.set_xlabel("frequency (GHz)"); a.grid(alpha=0.3)
ax[1].set_ylim(2.2, 2.3); ax[2].set_ylim(41, 45); ax[0].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "port_block_test.png"), dpi=200)
