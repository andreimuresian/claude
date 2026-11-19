"""Data check of the 0-130 GHz reruns (full equaliser, L+S, L+B+S).
1. every field file: frequency list (expected 1..60 step 1, 62..130 step 2 = 95), points per frequency, coordinates
   vs the header box; 2. bend zips: reassembly of the split parts and listing; 3. touchstones: frequency grid, and
   |S21|, |S11| vs the old 0-80 GHz runs over 0.5-80 GHz; 4. gap voltage V(z) = (GAP/2)(Ey+ - Ey-) of the buried lines
   vs the old runs at common frequencies (1..60 GHz): rms relative difference over the common z range."""
import os, glob, zipfile, io, numpy as np, skrf as rf
E = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FEXP = np.r_[np.arange(1, 61), np.arange(62, 131, 2)]
def load(p):
    d = np.loadtxt(p, skiprows=2); return d
def gapV(pp, pm, gap=0.00445e-3):
    a, b = load(pp), load(pm); assert np.allclose(a[:, [0, 3]], b[:, [0, 3]])
    V = gap / 2 * ((a[:, 6] + 1j * a[:, 7]) - (b[:, 6] + 1j * b[:, 7]))
    f = np.unique(a[:, 0]); z = a[a[:, 0] == f[0], 3]
    return f, z, V.reshape(len(f), len(z))
print("== 1. field files")
for run in ("full equalizer", "L+S", "L+B+S"):
    for p in sorted(glob.glob(os.path.join(E, run, "130 GHz", "*.txt"))):
        hdr = open(p).readline().strip(); d = load(p); f = np.unique(d[:, 0]); n = np.bincount(np.searchsorted(f, d[:, 0]))
        ok = np.array_equal(f, FEXP) and n.min() == n.max()
        print(f"{run:15s} {os.path.basename(p):24s} nf {len(f):3d} pts/f {n.min():4d} x {d[:,1].min():.4f}..{d[:,1].max():.4f} "
              f"y {d[:,2].min():+.6f}..{d[:,2].max():+.6f} z {d[:,3].min():.4f}..{d[:,3].max():.4f} {'OK' if ok else 'CHECK'} | {hdr[9:]}")
print("== 2. bend zips")
for run, stem in (("full equalizer", "bend_fields_full_eq"), ("L+B+S", "bend_fields_L+B+S")):
    parts = sorted(glob.glob(os.path.join(E, run, "130 GHz", stem + ".zip.0*")))
    z = zipfile.ZipFile(io.BytesIO(b"".join(open(q, "rb").read() for q in parts)))
    bad = z.testzip()
    print(f"{run}: {len(parts)} parts, CRC {'OK' if bad is None else 'BAD ' + bad}:", [(i.filename, i.file_size) for i in z.infolist()])
print("== 3. touchstones")
PAIRS = {"full equalizer": ("BASELINE_FULL_EQUALIZER.s2p", "BASELINE - FULL EQUALIZER_130 GHz.s2p"),
         "L+S": ("BASELINE_LS.s2p", "BASELINE - L+S - 130 GHz.s2p"), "L+B+S": ("BASELINE_LBS.s2p", "BASELINE - L+B+S - 130 GHz.s2p")}
for run, (o, n) in PAIRS.items():
    no, nn = rf.Network(os.path.join(E, run, o)), rf.Network(os.path.join(E, run, "130 GHz", n))
    fo, fn = no.f / 1e9, nn.f / 1e9; m = (fo >= 0.5) & (fo <= 80)
    d21 = 20 * np.log10(np.interp(fo[m], fn, abs(nn.s[:, 1, 0])) / abs(no.s[m, 1, 0]))
    d11 = np.interp(fo[m], fn, abs(nn.s[:, 0, 0])) - abs(no.s[m, 0, 0])
    dph = np.degrees(np.interp(fo[m], fn, np.unwrap(np.angle(nn.s[:, 1, 0]))) - np.unwrap(np.angle(no.s[m, 1, 0])))
    print(f"{run:15s} new grid {fn.min():.2f}..{fn.max():.0f} GHz, {len(fn)} pts (step {fn[1]-fn[0]:.3f}) | old {fo.max():.0f} GHz | "
          f"0.5-80 GHz: |S21| diff max {abs(d21).max():.3f} dB, S21 phase diff max {abs(dph).max():.2f} deg, |S11| diff max {abs(d11).max():.4f}")
print("== 4. gap voltage new vs old (1..60 GHz)")
for run, lines in (("full equalizer", ("L1", "L2", "L3")), ("L+S", ("L1",)), ("L+B+S", ("L1", "L2"))):
    for L in lines:
        fo, zo, Vo = gapV(*(os.path.join(E, run, f"{L}_gap{s}.txt") for s in "+-"))
        fn, zn, Vn = gapV(*(os.path.join(E, run, "130 GHz", f"{L}_gap{s}.txt") for s in "+-"))
        zc = zo[(zo >= zn.min() - 1e-9) & (zo <= zn.max() + 1e-9)]; err = []
        for i, f in enumerate(fo):
            j = np.where(fn == f)[0]
            if len(j) == 0: continue
            a = Vo[i][np.isin(np.round(zo, 6), np.round(zc, 6))]; b = Vn[j[0]][np.isin(np.round(zn, 6), np.round(zc, 6))]
            err.append((f, np.linalg.norm(b - a) / np.linalg.norm(a)))
        err = np.array(err); k = np.argmax(err[:, 1])
        print(f"{run:15s} {L}: z common {zc.min():.3f}..{zc.max():.3f} mm, {len(err)} freqs, rms rel diff median {100*np.median(err[:,1]):.2f} %, max {100*err[k,1]:.2f} % at {err[k,0]:.0f} GHz")
