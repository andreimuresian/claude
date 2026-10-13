"""Renormalise the 1 mm and 5 mm CST runs to each line's own Zc, cascade the
1 mm run five times in that reference, and compare with the 5 mm run."""
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
src = open('cascade_extract.py').read()
exec(src.split("idx=")[0]); exec("def ext" + src.split("def ext")[1].split("w=2*np.pi")[0])

def renorm(S, Zr):
    """50-ohm S-matrix -> S-matrix referenced to Zr(f) on both ports (exact)."""
    I = np.eye(2); out = np.empty_like(S)
    for k in range(len(S)):
        Z = 50 * (I + S[k]) @ np.linalg.inv(I - S[k])
        out[k] = (Z - Zr[k] * I) @ np.linalg.inv(Z + Zr[k] * I)
    return out

def cascade_s(Sa, Sb):
    """Connect port 2 of Sa to port 1 of Sb (same reference on both sides)."""
    d = 1 - Sa[:, 1, 1] * Sb[:, 0, 0]
    S = np.empty_like(Sa)
    S[:, 0, 0] = Sa[:, 0, 0] + Sa[:, 0, 1] * Sb[:, 0, 0] * Sa[:, 1, 0] / d
    S[:, 0, 1] = Sa[:, 0, 1] * Sb[:, 0, 1] / d
    S[:, 1, 0] = Sb[:, 1, 0] * Sa[:, 1, 0] / d
    S[:, 1, 1] = Sb[:, 1, 1] + Sb[:, 1, 0] * Sa[:, 1, 1] * Sb[:, 0, 1] / d
    return S

_, _, Z1 = ext(T1, 1e-3)          # each file's own Zc
_, _, Z5 = ext(T5, 5e-3)
S1z, S5z = renorm(S1, Z1), renorm(S5, Z5)
Sc = S1z
for _ in range(4):
    Sc = cascade_s(Sc, S1z)

F = f / 1e9
for x in [0.06, 1, 10, 30, 40, 55, 60]:
    i = np.argmin(abs(F - x))
    print(f"{F[i]:5.2f} GHz  |S21| 5mm {db(S5z[i,1,0]):7.3f}  casc {db(Sc[i,1,0]):7.3f}  "
          f"d {db(Sc[i,1,0])-db(S5z[i,1,0]):+6.3f} dB | ang 5mm {np.rad2deg(np.unwrap(np.angle(S5z[:,1,0])))[i]:8.1f} "
          f"casc {np.rad2deg(np.unwrap(np.angle(Sc[:,1,0])))[i]:8.1f} | |S11| 5mm {db(S5z[i,0,0]):6.1f} casc {db(Sc[i,0,0]):6.1f}")

fig, ax = plt.subplots(1, 3, figsize=(14, 4))
ax[0].plot(F, db(S5z[:, 1, 0]), lw=1.8, color='#1f4e9a', label='5 mm, own Zc')
ax[0].plot(F, db(Sc[:, 1, 0]), '--', lw=1.8, color='#d9541e', label='1 mm × 5, own Zc')
ax[0].set_ylabel('|S21| (dB)')
ax[1].plot(F, np.rad2deg(np.unwrap(np.angle(Sc[:, 1, 0])) - np.unwrap(np.angle(S5z[:, 1, 0]))), color='#444')
ax[1].set_ylabel('∠S21 cascade − 5 mm (deg)')
ax[2].plot(F, db(S5z[:, 0, 0]), lw=1.8, color='#1f4e9a'); ax[2].plot(F, db(Sc[:, 0, 0]), '--', lw=1.8, color='#d9541e')
ax[2].set_ylabel('|S11| (dB)')
for a in ax: a.set_xlabel('Frequency (GHz)'); a.grid(alpha=.3)
ax[0].legend()
fig.suptitle('Renormalised to each line\'s own Zc: 1 mm × 5 cascade vs 5 mm')
fig.tight_layout(); fig.savefig('cascade_Zc_renorm.png', dpi=150)
