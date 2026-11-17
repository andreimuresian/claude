"""Full equalizer run (L1 2.7 mm +, bend, L2 1.44 mm +, bend, L3 1.44 mm -): analysis of the gap fields.

1. Reference EO response. V_k(z) = GAP/2 (E_y(gap+) - E_y(gap-)) on the buried metal of each line
   (L1 z 0..2.70, light and RF along +z; L2 z 2.70..1.26, along -z; L3 z 1.26..2.70, along +z).
   H = sum_k p_k int V_k(s) exp(j w t_opt(s)) ds, p = (+1, +1, -1), t_opt = n_g s / c inside a line.
   Bends: light assumed matched to the RF transit time of each bend block (taper + arc + taper), taken from
   the phase of the forward wave on both sides of the bend (step 3). n_g = 2.27. Normalised to 1 GHz.
   Compared with the single 2.7 mm line (line formula, L+S touchstone parameters, 50 ohm source/load).
2. Line parameters of each fold: two-wave fit V = A exp(-g z) + B exp(+g z) of the pitch-averaged V(z),
   0.18 mm cut at each end of the buried metal; compared with the L+S fields fit (ls_extraction.csv).
3. Bend blocks as 2-ports referenced to the line (voltage waves, Zc of the line on both sides), reference
   planes at the ends of the buried metal (bend 1: z = 2.70 on L1 and L2; bend 2: z = 1.26 on L2 and L3).
   Reciprocal + symmetric block (S11 = S22, S21 = S12): b1 = S11 a1 + S21 a2, b2 = S21 a1 + S11 a2,
   solved from the two waves on each side (one excitation is enough).
Outputs: full_eq_fields.png, full_eq_fields.csv, printed tables."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, ROOT)
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import eo_transfer, C0

D = os.path.join(HERE, "..", "full equalizer"); GAP = 4.45e-6; NG = 2.27; PITCH = 0.18e-3; CUT = 0.18e-3
LINES = {"L1": (0.0, 2.70e-3, +1), "L2": (1.26e-3, 2.70e-3, -1), "L3": (1.26e-3, 2.70e-3, +1)}   # buried metal, RF direction
POL = {"L1": +1, "L2": +1, "L3": -1}
LS = np.genfromtxt(os.path.join(HERE, "ls_extraction.csv"), delimiter=",", names=True)

def load_gap(fn):
    a = np.loadtxt(os.path.join(D, fn), comments="#", skiprows=2); out = {}
    for f in np.unique(a[:, 0]):
        b = a[a[:, 0] == f]; o = np.argsort(b[:, 3]); out[f] = (b[o, 3] * 1e-3, b[o, 6] + 1j * b[o, 7])
    return out

data = {}
for ln in LINES:
    gp, gm = load_gap(f"{ln}_gap+.txt"), load_gap(f"{ln}_gap-.txt")
    F = np.array(sorted(gp)); z = gp[F[0]][0]
    data[ln] = (z, np.array([0.5 * GAP * (gp[f][1] - gm[f][1]) for f in F]))
w = 2 * np.pi * F * 1e9

# ---- step 2: two-wave fit per line
def two_wave(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
fitp = {}
for ln, (z0, z1, _) in LINES.items():
    z, V = data[ln]; dz = z[1] - z[0]; k = int(round(PITCH / dz)); ker = np.ones(k) / k
    zs = np.convolve(z, ker, "valid"); m = (zs >= z0 + CUT) & (zs <= z1 - CUT)
    G, C, R = [], [], []
    for i in range(len(F)):
        vs = np.convolve(V[i], ker, "valid")[m]
        g0 = [np.interp(F[i], LS["f_GHz"], LS["alpha_fields_dB_cm"]) * 100 / 8.686, np.interp(F[i], LS["f_GHz"], LS["nm_fields"]) * w[i] / C0]
        res = lambda p: np.concatenate([(e := two_wave(p[0] + 1j * p[1], zs[m], vs)[1]).real, e.imag])
        p = least_squares(res, g0, x_scale=[max(g0[0], 1), g0[1]]).x; g = p[0] + 1j * p[1]
        c, e = two_wave(g, zs[m], vs); G.append(g); C.append(c); R.append(np.linalg.norm(e) / np.linalg.norm(vs))
    fitp[ln] = (np.array(G), np.array(C), np.array(R))

print("STEP 2  line parameters (fields): alpha dB/cm | n_m      L+S fields shown for reference")
print(" f GHz |      L1       |      L2       |      L3       |     L+S")
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(F - q)); s = f"{F[i]:5.0f}  |"
    for ln in LINES:
        g = fitp[ln][0][i]; s += f" {g.real*8.686/100:4.2f} {g.imag*C0/w[i]:.3f} |"
    j = np.argmin(abs(LS["f_GHz"] - F[i])); s += f" {LS['alpha_fields_dB_cm'][j]:4.2f} {LS['nm_fields'][j]:.3f}"
    print(s)
print(" max fit residual per line (%):", {ln: round(100 * fitp[ln][2].max(), 2) for ln in LINES})

# ---- step 3: bend blocks
def waves(ln, zp):
    """(incident on the bend, leaving the bend) voltage waves at plane zp of line ln."""
    g, c, _ = fitp[ln]; fw = c[:, 0] * np.exp(-g * zp); bw = c[:, 1] * np.exp(g * zp)   # +z and -z travelling
    return fw, bw
def bend(lin, lout, zp):
    f1, b1_ = waves(lin, zp); f2, b2_ = waves(lout, zp)
    # side 1 = lin; side 2 = lout. Incident on bend: from lin travelling toward zp, from lout travelling toward zp.
    if LINES[lin][2] > 0: a1, b1 = f1, b1_            # lin carries RF along +z, bend at its +z end
    else:                a1, b1 = b1_, f1              # lin along -z, bend at its -z end
    if LINES[lout][2] > 0: a2, b2 = b2_, f2           # lout along +z, starts at the bend: incident = -z wave
    else:                 a2, b2 = f2, b2_             # lout along -z, starts at the bend: incident = +z wave
    S11 = (b1 * a1 - b2 * a2) / (a1**2 - a2**2); S21 = (b2 * a1 - b1 * a2) / (a1**2 - a2**2)
    return S11, S21
B1 = bend("L1", "L2", 2.70e-3); B2 = bend("L2", "L3", 1.26e-3)
tau = {}
print("\nSTEP 3  bend blocks (taper + arc + taper), referenced to the line, planes at the ends of the buried metal")
print(" f GHz | bend 1: |S21| dB  delay ps  |S11| | bend 2: |S21| dB  delay ps  |S11|")
for nm, (S11, S21) in (("b1", B1), ("b2", B2)):
    ph = -np.unwrap(np.angle(S21)); tau[nm] = ph / w
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(F - q))
    print(f"{F[i]:5.0f}  | {20*np.log10(abs(B1[1][i])):+.3f} {tau['b1'][i]*1e12:7.2f} {abs(B1[0][i]):.3f} |"
          f" {20*np.log10(abs(B2[1][i])):+.3f} {tau['b2'][i]*1e12:7.2f} {abs(B2[0][i]):.3f}")
Lb = 2 * (0.22434e-3 + 0.05e-3) + np.pi * 0.1025e-3
print(f" bend block centre-line length ~ {Lb*1e3:.3f} mm (2 tapers incl. 50 um transitions + half circle) -> "
      f"group index from the delay at 30 GHz: {tau['b1'][np.argmin(abs(F-30))]*C0/Lb:.2f}")

# ---- step 1: reference EO response
def eo(pols, use=("L1", "L2", "L3")):
    H = np.zeros(len(F), complex)
    for i in range(len(F)):
        t0 = 0.0
        for ln in ("L1", "L2", "L3"):
            z, V = data[ln]; z0, z1, d = LINES[ln]; m = (z >= z0 - 1e-9) & (z <= z1 + 1e-9)
            s = (z[m] - z0) if d > 0 else (z1 - z[m])
            if ln in use:
                H[i] += pols[ln] * np.trapezoid(V[i][m] * np.exp(1j * w[i] * (t0 + NG * s / C0)), s) * (1 if d > 0 else 1)
            t0 += NG * (z1 - z0) / C0
            if ln == "L1": t0 += tau["b1"][i]
            if ln == "L2": t0 += tau["b2"][i]
    return H
# s integration reversed for L2: np.trapezoid over decreasing s gives a negative sign -> fix by ordering
def eo_sorted(pols):
    H = np.zeros(len(F), complex)
    for i in range(len(F)):
        t0 = 0.0
        for ln in ("L1", "L2", "L3"):
            z, V = data[ln]; z0, z1, d = LINES[ln]; m = (z >= z0 - 1e-9) & (z <= z1 + 1e-9)
            s = (z[m] - z0) if d > 0 else (z1 - z[m]); o = np.argsort(s)
            H[i] += pols[ln] * np.trapezoid((V[i][m] * np.exp(1j * w[i] * (t0 + NG * s / C0)))[o], s[o])
            t0 += NG * (z1 - z0) / C0 + (tau["b1"][i] if ln == "L1" else tau["b2"][i] if ln == "L2" else 0)
    return H
H_full = eo_sorted(POL)
H_noeq = eo_sorted({"L1": 1, "L2": 0, "L3": 0})                  # line 1 alone, inside the full run (loaded by the rest)
fit = extract_line_fit(os.path.join(HERE, "..", "L+S", "BASELINE_LS.s2p"), 3.24)
H_27, _ = eo_transfer(F, fit.alpha_dB_cm(F), fit.nm(F), fit.Zc(F), 2.70e-3, NG, 50.0, 50.0)   # bare 2.7 mm line, 50/50
db = lambda h: 20 * np.log10(abs(h) / abs(h[0]))
def cross(y, lev=-3.0):
    k = np.where(y <= lev)[0]
    if not len(k): return "> 60"
    i = k[0]; return f"{F[i-1] + (lev - y[i-1]) * (F[i] - F[i-1]) / (y[i] - y[i-1]):.1f}"
print("\nSTEP 1  EO response (re 1 GHz), n_g 2.27, bends matched for the light")
print(" case                                | 20 GHz | 40 GHz | 60 GHz | -3 dB")
for lab, H in (("full equalizer (+ + -)", H_full), ("line 1 only, inside the full run", H_noeq), ("bare 2.7 mm line, L+S params", H_27)):
    y = db(H); print(f" {lab:36s}| {y[np.argmin(abs(F-20))]:+.2f}  | {y[np.argmin(abs(F-40))]:+.2f}  | {y[np.argmin(abs(F-60))]:+.2f}  | {cross(y)}")
print(f" DC-like efficiency (1 GHz): |H_full| / |H_line1| = {abs(H_full[0])/abs(H_noeq[0]):.3f}  (ideal 1: added sections cancel)")

np.savetxt(os.path.join(HERE, "full_eq_fields.csv"),
           np.column_stack([F, db(H_full), db(H_noeq), db(H_27),
                            20*np.log10(abs(B1[1])), tau["b1"]*1e12, abs(B1[0]), 20*np.log10(abs(B2[1])), tau["b2"]*1e12, abs(B2[0])]
                           + [fitp[ln][0].real*8.686/100 for ln in LINES] + [fitp[ln][0].imag*C0/w for ln in LINES]),
           delimiter=",", fmt="%.5g", comments="",
           header="f_GHz,EO_full_dB,EO_line1_in_full_dB,EO_bare_2p7mm_dB,bend1_S21_dB,bend1_delay_ps,bend1_S11,bend2_S21_dB,bend2_delay_ps,bend2_S11,"
                  "alpha_L1,alpha_L2,alpha_L3,nm_L1,nm_L2,nm_L3")

fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
ax[0].plot(F, db(H_full), "o-", ms=3, color="#eb6834", label="full equalizer (+ + −), fields")
ax[0].plot(F, db(H_27), "k--", label="bare 2.7 mm line (L+S parameters)")
ax[0].axhline(-3, color="0.4", lw=0.8, ls=":"); ax[0].set_ylabel("EO response re 1 GHz (dB)"); ax[0].set_ylim(-4, 1)
c = {"L1": "#2a78d6", "L2": "#1baa7d", "L3": "#7a4bd1"}
for ln in LINES:
    ax[1].plot(F, fitp[ln][0].imag * C0 / w, "o", ms=2.5, color=c[ln], label=f"{ln}")
ax[1].plot(LS["f_GHz"], LS["nm_fields"], "k-", lw=1, label="L+S"); ax[1].set_ylabel("n_m (fields)"); ax[1].set_ylim(2.15, 2.4)
ax[2].plot(F, 20*np.log10(abs(B1[1])), "-", color="#2a78d6", label="bend 1 |S21|"); ax[2].plot(F, 20*np.log10(abs(B2[1])), "--", color="#1baa7d", label="bend 2 |S21|")
ax[2].plot(F, 20*np.log10(abs(B1[0])) / 10, ":", color="#2a78d6", label="bend 1 |S11| (dB / 10)")
ax[2].plot(F, 20*np.log10(abs(B2[0])) / 10, "-.", color="#1baa7d", label="bend 2 |S11| (dB / 10)")
ax[2].set_ylabel("bend block (dB)")
for a_ in ax: a_.set_xlabel("frequency (GHz)"); a_.grid(alpha=0.3); a_.legend(frameon=False, fontsize=8)
fig.suptitle("Full equalizer run: EO response, line parameters per fold, bend blocks (from the gap fields)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "full_eq_fields.png"), dpi=200)
