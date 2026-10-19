"""Line voltages and even/odd impedance ratio of CST port modes 5/6 at every
exported frequency (0.5 um sub-volume exports). See port_voltages_05um.py."""
import io, zipfile, glob, re, numpy as np
def lines(fn):
    z = zipfile.ZipFile(fn); A = np.loadtxt(io.TextIOWrapper(z.open(z.namelist()[0])), skiprows=2, usecols=(0, 1, 5, 6))
    out = []
    for xr in (0.0005, 0.0010, 0.0015, 0.0020):
        r = A[np.isclose(A[:, 0], xr)]; r = r[np.argsort(r[:, 1])]
        y = r[:, 1]*1e-3; e = r[:, 2] + 1j*r[:, 3]; zero = e == 0
        V = -np.concatenate([[0], np.cumsum(0.5*(e[1:]+e[:-1])*np.diff(y))])
        ed = np.flatnonzero(np.diff(np.r_[0, zero.astype(int), 0]))
        Vc = [V[a:b].real.mean() for a, b in zip(ed[::2], ed[1::2])]
        out.append((Vc[1]-(Vc[0]+Vc[2])/2, Vc[4]-(Vc[3]+Vc[5])/2))
    return np.array(out)
files = {5: {}, 6: {}}
for fn in glob.glob("2D port simulation/Port1_e[56]_*.zip"):
    if "1um" in fn: continue
    m = int(fn.split("_e")[1][0]); f = 30 if "0.5um" in fn else int(re.search(r"_(\d+)GHz", fn).group(1))
    files[m][f] = fn
res = {}
for f in sorted(files[5]):
    L5, L6 = lines(files[5][f]), lines(files[6][f])
    s5, s6 = (L5**2).sum(1), (L6**2).sum(1); ratio = s5/s6 - 1
    imb5 = L5[:, 1]/L5[:, 0]; imb6 = -L6[:, 1]/L6[:, 0]
    res[f] = ratio
    print(f"{f:3d} GHz  Ze/Zo-1 per row: {np.round(100*ratio,3)} %   B/A mode5 {imb5.mean():.3f}  mode6 {imb6.mean():.3f}")

