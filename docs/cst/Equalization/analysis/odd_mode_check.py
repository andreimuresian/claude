"""Ground-to-ground (odd, slotline-like) content of the gap fields: rms(E+ + E-) / rms(E+ - E-) per frequency.
E+ and E- are E_y in the two gaps; the CPW mode gives E+ = -E- (ratio 0), a ground-to-ground mode E+ = +E-.
Run from this folder."""
import numpy as np, os
def load(d, fn):
    a = np.loadtxt(os.path.join(d, fn), comments="#", skiprows=2); out = {}
    for f in np.unique(a[:, 0]):
        b = a[a[:, 0] == f]; o = np.argsort(b[:, 3]); out[f] = b[o, 6] + 1j * b[o, 7]
    return out
for run, lines in (("../L+B+S", ("L1", "L2")), ("../full equalizer", ("L1",)), ("../L+S", ("L1",))):
    for ln in lines:
        p, m = load(run, f"{ln}_gap+.txt"), load(run, f"{ln}_gap-.txt")
        F = np.array(sorted(p))
        r = [np.sqrt(np.mean(abs(p[f] + m[f])**2)) / np.sqrt(np.mean(abs(p[f] - m[f])**2)) for f in F]   # odd (ground-ground) / even (CPW)
        print(run, ln, "odd/even rms ratio at", " ".join(f"{F[i]:.0f}:{r[i]:.3f}" for i in range(len(F)) if F[i] in (5,10,14,15,16,17,20,25,30,31,32,40,46,47,48,55)))
