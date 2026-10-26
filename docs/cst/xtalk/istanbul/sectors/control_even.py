import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import two_wave_fit as T
f, data = T.load()
prev = np.load("sector_fit.npz"); ev1 = prev["even"]
fsel = np.arange(10e9, 50.01e9, 2.5e9); idx = [int(np.argmin(abs(f - x))) for x in fsel]
get = lambda i: (np.array([data[L]["even"][0][i] for L in T.LS]), np.array([data[L]["even"][1][i] for L in T.LS]))
init = lambda i: (np.interp(f[i], ev1[:, 0], ev1[:, 2]), np.interp(f[i], ev1[:, 0], ev1[:, 3]))
one = [T.fit_freq(f[i], *get(i), *init(i))[0] for i in idx]
print(f"EVEN one mode lossless: median {np.median(one):.4f};  general junction: {np.median(np.interp(f[idx], ev1[:,0], ev1[:,1])):.4f}")
for nx in (2.0, 2.4, 2.6, 2.7, 3.0):
    e = [T.fit_freq(f[i], *get(i), *init(i), nx=nx, starts=16)[0] for i in idx]
    print(f"EVEN two modes n_x={nx}: median {np.median(e):.4f}", flush=True)
