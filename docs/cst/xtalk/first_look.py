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
f, S = load4("LINEA0_1MM_200UM_PITCH.s4p")
k = lambda GHz: np.argmin(abs(f-GHz*1e9))
db = lambda x: 20*np.log10(abs(x))
print("ports: |S21|, |S43| at 30 GHz:", abs(S[k(30),1,0]), abs(S[k(30),3,2]))
for G in (1, 10, 30, 60):
    i = k(G); s = S[i]
    print(f"{G:3d} GHz  S31 {db(s[2,0]):6.1f} dB  S41 {db(s[3,0]):6.1f} dB  "
          f"S32 {db(s[2,1]):6.1f}  S42 {db(s[3,1]):6.1f}   S11 {db(s[0,0]):6.1f}  S21 {db(s[1,0]):6.3f}")
# symmetry checks
print("max |S - S^T|:", np.max(abs(S-np.transpose(S,(0,2,1)))))
print("max |S11-S33|, |S21-S43|:", np.max(abs(S[:,0,0]-S[:,2,2])), np.max(abs(S[:,1,0]-S[:,3,2])))
np.savez("s4p.npz", f=f, S=S)
