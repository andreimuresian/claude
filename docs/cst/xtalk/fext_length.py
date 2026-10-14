"""Far-end crosstalk vs length with loss: |V_B(L)| = 1/2 |e^{-g_e L} - e^{-g_o L}| ~ (dB L/2) e^{-aL}."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
c0 = 299792458.0; Np = np.log(10)/20
Lmm = np.linspace(0.01, 120, 4000); L = Lmm*1e-3
fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
for f, adb, dn, col in ((30e9, 2.95, 2e-4, "C0"), (60e9, 4.4, 1e-3, "C1")):
    a = adb*100*Np; db = 2*np.pi*f*dn/c0           # alpha Np/m, beta_o - beta_e
    ge = a + 1j*2*np.pi*f*1.95/c0; go = ge + 1j*db
    VB = 0.5*abs(np.exp(-ge*L) - np.exp(-go*L))       # victim far end (matched, weak coupling)
    VA = 0.5*abs(np.exp(-ge*L) + np.exp(-go*L))       # aggressor far end
    lab = f"{f/1e9:.0f} GHz (α = {adb} dB/cm, Δn = {dn:g})"
    ax[0].plot(Lmm, 20*np.log10(VB), col, label=lab)
    ax[0].axvline(1/a*1e3, color=col, ls=":", lw=1)
    ax[1].plot(Lmm, 20*np.log10(VB/VA), col, label=lab)
for x in (1, 5, 14):
    for a_ in ax: a_.axvline(x, color="gray", lw=0.6)
ax[0].set_title("Victim far-end voltage |V_B(L)|  (per volt launched on A)\npeaks at L = 1/α (dotted), then → 0 for an infinite line")
ax[1].set_title("Victim relative to what arrives on the aggressor |V_B/V_A|\ngrows ∝ L: loss attenuates both equally")
for a_ in ax: a_.set_xlabel("line length (mm)   grey: 1, 5, 14 mm"); a_.set_ylabel("dB"); a_.grid(alpha=0.3); a_.legend(fontsize=8.5)
ax[0].set_ylim(-80, -30); ax[1].set_ylim(-80, -10)
plt.tight_layout(); plt.savefig("fext_vs_length.png", dpi=140)
for f, adb in ((30e9, 2.95), (60e9, 4.4)): print(f"{f/1e9:.0f} GHz: peak length 1/alpha = {1/(adb*100*Np)*1e3:.1f} mm")
