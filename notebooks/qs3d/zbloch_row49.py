"""Row 49: impedance of the tee cell measured on the CST multilayer lines (2 and 3 cells),
against the 3D quasi-static cell and the dataset.

The dataset's Z0 comes from ONE CST cell between two ports (L = Im B/w, C = Im C/w at
60 GHz). Here the tee cell's impedance is taken from the 400 and 600 um lines instead,
with the port transitions removed.

Model: a line of N cells is M_N = P T^N P~ (ABCD, 50 ohm ports):
  P  the port-1 transition, from the port to the first cell boundary (the ports sit on
     cell boundaries, midway between tees); P~ its mirror image;
  T  the symmetric cell, with Bloch impedance Z_B (at the cell boundary) and
     propagation constant g per cell.
For a symmetric line, M S (S = diag(1, -1)) has eigenvalues +1 and -1. Their eigenvectors
[V, I] are the even and odd excitations, with input impedances
    w_e = P( Z_B coth(N g/2) ),   w_o = P( Z_B tanh(N g/2) ),
where P(z) = (a z + b)/(c z + d) is the bilinear map of the port transition.

1. Calibration on the no-tee lines (uniform, Z_B = Z_u). g from the line-line eigenvalues
   of M3 M2^-1. P from 6 point pairs: the 4 mode impedances, and +-Z_u -> the impedances
   of the eigenvectors of M3 M2^-1 (travelling waves). Z_u = 1 in the fit; a lumped port
   transition has a = d up to (w^2 L C), so a/d of the fitted map is Z_u in ohm.
2. Tee lines. P^-1 maps their 4 mode impedances to Z_B coth(N g/2), Z_B tanh(N g/2),
   N = 2, 3: Z_B = sqrt(z_e z_o) for each N, and g from z_o/z_e, checked against the
   line-line g. Assumption: the port transition is the same with and without tees (the
   head slot ends 16.7 um from the port plane). The two N must agree if it holds.
3. 3D quasi-static cell: Z_B = sqrt(B/C) of its symmetric slice cascade (qs3d README) at
   the same frequency; PEC (L'(0)), and gold with the surface impedance (1 + j) R'.
4.-7. Frequency dependence, the 5 um ground mesh at 60 GHz, the dataset's one-cell extraction
   rebuilt from these pieces, and the port fit on the tee lines alone (no no-tee runs needed).
Run: python zbloch_row49.py > zbloch_row49.txt
"""
import cmath
import json
import math
import os

import numpy as np
import pandas as pd

import cst_row49 as cr
import loss as Lo
import qs3d as q

HERE = os.path.dirname(os.path.abspath(__file__))
C0, P = q.C0, q.P
S_ = np.diag([1.0, -1.0])


def modes(M):
    """Even (+1) and odd (-1) input impedances of a symmetric line, and |A - D|/|A|."""
    w, V = np.linalg.eig(M @ S_)
    z = V[0]/V[1]
    ie = int(np.argmin(abs(w - 1)))
    return z[ie], z[1 - ie], abs(M[0, 0] - M[1, 1])/abs(M[0, 0])


def line_line(M2, M3):
    """g per cell (Re >= 0) and the impedances of the eigenvectors of M3 M2^-1 (forward first)."""
    X = M3 @ np.linalg.inv(M2)
    w, V = np.linalg.eig(X)
    z = V[0]/V[1]
    i = int(np.argmax(w.imag))                 # forward wave: V1/V2 = e^g, 0 < Im g < pi here
    g = cmath.log(w[i])
    return g, z[i], z[1 - i]


def fit_mobius(zs, ws):
    """Bilinear map w = (a z + b)/(c z + d), det = 1, through the point pairs (least squares).
    Returns the matrix and s_min / s_next of the system (0 for exactly consistent pairs)."""
    A = np.array([[z, 1, -z*w, -w] for z, w in zip(zs, ws)], complex)
    A /= np.linalg.norm(A, axis=1, keepdims=True)
    _, s, Vh = np.linalg.svd(A)
    a, b, c, d = Vh[-1].conj()
    Pm = np.array([[a, b], [c, d]])/cmath.sqrt(a*d - b*c)
    return Pm, s[-1]/s[-2]


def inv_map(Pm, w):
    a, b, c, d = Pm.ravel()
    return (d*w - b)/(a - c*w)


def branch(g, f, n_ref):
    """g + 2 pi j k with the index n nearest n_ref (Im g >= 0 convention)."""
    k0 = 2*math.pi*f/C0*P
    best = min((g + 2j*math.pi*k for k in range(-3, 6)), key=lambda x: abs(x.imag/k0 - n_ref))
    return best, best.imag/k0


def cell_from_modes(ze, zo, N, f, n_ref):
    """Z_B and g from the de-embedded even/odd impedances of an N-cell line."""
    Z = cmath.sqrt(ze*zo)
    Z = Z if Z.real > 0 else -Z
    h = cmath.atanh(zo/Z)                     # = N g / 2  (mod j pi)
    k0 = 2*math.pi*f/C0*P
    best = min((2*(h + 1j*math.pi*k)/N for k in range(-3, 6)), key=lambda x: abs(x.imag/k0 - n_ref))
    return Z, best, best.imag/k0


def qs3d_ZB(c, f, gold):
    """Bloch impedance at the cell boundary of the slice cascade (edge -> centre -> edge)."""
    w = 2*math.pi*f
    Ls, Cs = np.array(c["ls"]), np.array(c["cs"])
    Ls = np.concatenate([Ls[::-1], Ls]); Cs = np.concatenate([Cs[::-1], Cs])
    # gold: series impedance per length jwL'(0) + (1 + j) R', R' from the cell average (Wheeler)
    corr = 1 + (1 - 1j)*c["R_wh"]*math.sqrt(f/Lo.F0)/(w*c["L"]) if gold else 1.0
    M = np.eye(2, dtype=complex)
    for Lk, Ck in zip(Ls, Cs):
        Zs, Yp = 1j*w*Lk*corr, 1j*w*Ck
        th, Z = cmath.sqrt(Zs*Yp), cmath.sqrt(Zs/Yp)
        M = M @ np.array([[cmath.cosh(th), Z*cmath.sinh(th)], [cmath.sinh(th)/Z, cmath.cosh(th)]])
    ZB = cmath.sqrt(M[0, 1]/M[1, 0])
    g = cmath.acosh((M[0, 0] + M[1, 1])/2)
    return ZB, g


def main():
    D = {}
    for m in ("GOLD", "PEC"):
        for t in ("TEE", "NO TEE"):
            for L in (400, 600):
                D[(m, t, L)] = cr.read(os.path.join(cr.DIR, f"{L} {t} {m}.s2p"))[0]
    freqs = sorted(D[("PEC", "TEE", 400)])
    o = json.load(open(os.path.join(HERE, "run_loss.json")))["49|base"]
    ds = pd.read_excel(os.path.join(HERE, "..", "mom", "data", "EVALUATED_FULL_LHS_DATASET.xlsx")).loc[49]

    print("Row 49: tee-cell impedance from the CST 400/600 um lines (2 and 3 cells), port transitions removed")
    print("with the no-tee lines.  Z in ohm; F_Z = Z_B(tee) / Z_u.\n")
    print("1. Calibration on the no-tee lines: port map P fitted to 6 point pairs (consistency s_min/s_next),")
    print("   Z_u = a/d of the fitted map, and the port transition as series L / shunt C (Im b / w, Im c / w)")
    print(f"   {'metal':5} {'GHz':>4} | {'|A-D|/|A|':>9} | {'n_u':>6} {'a_u dB/cm':>9} | {'consist.':>8} | {'Z_u':>15} |"
          f" {'L pH':>7} {'C fF':>7}")
    cal = {}
    for m in ("PEC", "GOLD"):
        for f in freqs:
            M2, M3 = cr.abcd(D[(m, "NO TEE", 400)][f]), cr.abcd(D[(m, "NO TEE", 600)][f])
            g, zf, zb = line_line(M2, M3)
            g, nu = branch(g, f, 2.0)
            e2, o2, as2 = modes(M2)
            e3, o3, as3 = modes(M3)
            zs = [1/cmath.tanh(g), cmath.tanh(g), 1/cmath.tanh(1.5*g), cmath.tanh(1.5*g), 1.0, -1.0]
            Pm, cons = fit_mobius(zs, [e2, o2, e3, o3, zf, zb])
            Zu = Pm[0, 0]/Pm[1, 1]
            # port transition in ohm units: P_true = P_fit diag(1/Z_u, 1) * sqrt(Z_u)
            Pt = Pm @ np.diag([1/Zu, 1.0])*cmath.sqrt(Zu)
            w = 2*math.pi*f
            cal[(m, f)] = (Pm, Zu, g)
            print(f"   {m:5} {f/1e9:4.0f} | {max(as2, as3):9.1e} | {nu:6.3f} {g.real/P/100*8.686:9.3f} | {cons:8.1e} |"
                  f" {Zu.real:7.3f}{Zu.imag:+7.3f}j | {Pt[0, 1].imag/w*1e12:7.2f} {Pt[1, 0].imag/w*1e15:7.2f}")

    print("\n2. Tee lines: de-embedded with the no-tee port map.  Z_B and n from the 2-cell and the 3-cell line")
    print("   separately, and from the line-line eigenvectors; they must agree if the model holds.")
    print(f"   {'metal':5} {'GHz':>4} | {'Z_B (2 cells)':>15} {'Z_B (3 cells)':>15} {'Z_B (line-line)':>15} |"
          f" {'n 2':>6} {'n 3':>6} {'n ll':>6} | {'F_Z':>6}")
    meas = {}
    for m in ("PEC", "GOLD"):
        for f in freqs:
            Pm, Zu, _ = cal[(m, f)]
            M2, M3 = cr.abcd(D[(m, "TEE", 400)][f]), cr.abcd(D[(m, "TEE", 600)][f])
            gl, zf, zb = line_line(M2, M3)
            gl, nl = branch(gl, f, 2.7)
            zfp, zbp = inv_map(Pm, zf)*Zu, inv_map(Pm, zb)*Zu
            Zll = (zfp - zbp)/2
            row = []
            for N, M in ((2, M2), (3, M3)):
                e, od, _ = modes(M)
                Z, g, n = cell_from_modes(inv_map(Pm, e)*Zu, inv_map(Pm, od)*Zu, N, f, nl)
                row.append((Z, n))
            meas[(m, f)] = (row, Zll, Zu, nl)
            c = lambda z: f"{z.real:7.3f}{z.imag:+7.3f}j"
            print(f"   {m:5} {f/1e9:4.0f} | {c(row[0][0])} {c(row[1][0])} {c(Zll)} |"
                  f" {row[0][1]:6.3f} {row[1][1]:6.3f} {nl:6.3f} | {abs(Zll/Zu):6.4f}")

    print("\n3. Comparison at 20 GHz (no radiation; the 3D quasi-static cell is valid there)")
    print(f"   {'':34} {'PEC':>16} {'GOLD':>16}")
    lines = {}
    for m in ("PEC", "GOLD"):
        f = 20e9
        row, Zll, Zu, nl = meas[(m, f)]
        ZBe, _ = qs3d_ZB(o["e"], f, m == "GOLD")
        ZBu, _ = qs3d_ZB(o["u"], f, m == "GOLD")
        lines[m] = dict(Zu=Zu, Zt=Zll, FZ=abs(Zll/Zu), Zu3=ZBu, Zt3=ZBe, FZ3=abs(ZBe/ZBu))
    fmt = lambda z: f"{abs(z):16.3f}" if isinstance(z, complex) else f"{z:16.4f}"
    for k, lab in (("Zu", "CST no-tee line Z_u (ohm)"), ("Zu3", "3D no-slot cell Z_u (ohm)"),
                   ("Zt", "CST tee cell Z_B (ohm)"), ("Zt3", "3D tee cell Z_B (ohm)"),
                   ("FZ", "CST F_Z = Z_B / Z_u"), ("FZ3", "3D F_Z")):
        print(f"   {lab:34} " + " ".join(fmt(lines[m][k]) for m in ("PEC", "GOLD")))
    FZds = ds.z0_final_val/ds.z0_baseline_val
    print(f"   {'dataset F_Z (1 cell, 60 GHz)':34} {FZds:16.4f}")
    print(f"   {'dataset Z0: baseline -> final':34} {ds.z0_baseline_val:7.3f} -> {ds.z0_final_val:6.3f}")

    print("\n4. Frequency dependence of the 3D cell's Z_B (static L', C'; only the cascade's phase changes)")
    for f in freqs:
        ZBe, _ = qs3d_ZB(o["e"], f, False)
        ZBu, _ = qs3d_ZB(o["u"], f, False)
        print(f"   {f/1e9:4.0f} GHz: Z_B tee {abs(ZBe):.3f}, no-slot {abs(ZBu):.3f}, F_Z {abs(ZBe/ZBu):.4f};"
              f"  cell average sqrt(L'/C'): F_Z {math.sqrt(o['e']['L']/o['e']['C']/(o['u']['L']/o['u']['C'])):.4f}")


def cell_T(Z, g):
    return np.array([[cmath.cosh(g), Z*cmath.sinh(g)], [cmath.sinh(g)/Z, cmath.cosh(g)]])


def mirror(Pm):
    return S_ @ np.linalg.inv(Pm) @ S_


def extra():
    """5. 60 GHz with the 5 um ground mesh (600, 1000 um).  6. The dataset's one-cell extraction rebuilt."""
    f = 60e9
    w = 2*math.pi*f
    rd = lambda name: cr.read(os.path.join(cr.DIR, name + ".s2p"))[0][f]
    D = {k: rd(k) for k in ("400 NO TEE PEC", "600 NO TEE PEC", "400 NO TEE GOLD", "600 NO TEE GOLD",
                            "400 TEE PEC", "600 TEE PEC", "600 TEE PEC MESH CORRECTED", "1000 TEE PEC",
                            "400 TEE GOLD", "600 TEE GOLD")}
    cal = {}
    for m in ("PEC", "GOLD"):
        M2, M3 = cr.abcd(D[f"400 NO TEE {m}"]), cr.abcd(D[f"600 NO TEE {m}"])
        g, zf, zb = line_line(M2, M3)
        g, _ = branch(g, f, 2.0)
        e2, o2, _ = modes(M2); e3, o3, _ = modes(M3)
        zs = [1/cmath.tanh(g), cmath.tanh(g), 1/cmath.tanh(1.5*g), cmath.tanh(1.5*g), 1.0, -1.0]
        Pm, _ = fit_mobius(zs, [e2, o2, e3, o3, zf, zb])
        Zu = Pm[0, 0]/Pm[1, 1]
        cal[m] = (Pm, Zu, g, Pm @ np.diag([1/Zu, 1.0])*cmath.sqrt(Zu))

    print("\n5. 60 GHz, PEC tee: the 5 um ground mesh (600 and 1000 um lines); Z_B, n from each line alone and")
    print("   from line-line pairs (eigenvectors of Mb Ma^-1 = P T^(Nb-Na) P^-1)")
    Pm, Zu, _, _ = cal["PEC"]
    c = lambda z: f"{z.real:7.3f}{z.imag:+7.3f}j"
    for name, N in (("400 TEE PEC", 2), ("600 TEE PEC", 3), ("600 TEE PEC MESH CORRECTED", 3), ("1000 TEE PEC", 5)):
        e, od, _ = modes(cr.abcd(D[name]))
        Z, g, n = cell_from_modes(inv_map(Pm, e)*Zu, inv_map(Pm, od)*Zu, N, f, 2.7)
        print(f"   {name:27} ({N} cells): Z_B {c(Z)}  n {n:.3f}  alpha {g.real/P/100*8.686:6.2f} dB/cm")
    for a, b, Na, Nb in (("400 TEE PEC", "600 TEE PEC", 2, 3), ("400 TEE PEC", "600 TEE PEC MESH CORRECTED", 2, 3),
                         ("600 TEE PEC MESH CORRECTED", "1000 TEE PEC", 3, 5)):
        X = cr.abcd(D[b]) @ np.linalg.inv(cr.abcd(D[a]))
        ww, V = np.linalg.eig(X)
        z = inv_map(Pm, V[0]/V[1])*Zu
        print(f"   line-line {Na} -> {Nb} cells{' (5 um)' if 'CORR' in a + b else '':8}: Z_B {c((z[0] - z[1])/2*np.sign((z[0] - z[1]).real))}"
              f"   (sum of the two wave impedances {abs(z[0] + z[1]):.3f}, 0 if the model holds)")

    print("\n6. The dataset's one-cell extraction rebuilt: M1 = P T P~ (one cell between the two ports),")
    print("   L = Im B / w, C = Im C / w, dL, dC = tee - no tee; Z0_final = sqrt((L_b + dL/P)/(C_b + dC/P)) on the")
    print("   COMSOL baseline (dataset convention).  Gold, 60 GHz.  Dataset: dL 43.20 pH, dC -3.782 fF, Z0 53.459")
    ds = pd.read_excel(os.path.join(HERE, "..", "mom", "data", "EVALUATED_FULL_LHS_DATASET.xlsx")).loc[49]
    Lb, Cb = ds.z0_baseline_val*ds.nm_baseline_val/C0, ds.nm_baseline_val/(ds.z0_baseline_val*C0)
    o = json.load(open(os.path.join(HERE, "run_loss.json")))["49|base"]
    Pm, Zu, gu, Pt = cal["GOLD"]
    Tu = cell_T(Zu, gu)
    # CST tee cell at 60 GHz, gold: line-line 2 -> 3 (Z_B from the eigenvectors, g from the eigenvalues)
    M2, M3 = cr.abcd(D["400 TEE GOLD"]), cr.abcd(D["600 TEE GOLD"])
    gt, zf, zb = line_line(M2, M3)
    gt, _ = branch(gt, f, 2.7)
    Zt = (inv_map(Pm, zf) - inv_map(Pm, zb))/2*Zu
    Tt = cell_T(Zt, gt)
    # 3D quasi-static cell, gold: slice cascades
    def casc(cc):
        Ls, Cs = np.array(cc["ls"]), np.array(cc["cs"])
        Ls = np.concatenate([Ls[::-1], Ls]); Cs = np.concatenate([Cs[::-1], Cs])
        corr = 1 + (1 - 1j)*cc["R_wh"]/(w*cc["L"])
        M = np.eye(2, dtype=complex)
        for Lk, Ck in zip(Ls, Cs):
            Zs, Yp = 1j*w*Lk*corr, 1j*w*Ck
            M = M @ cell_T(cmath.sqrt(Zs/Yp), cmath.sqrt(Zs*Yp))
        return M
    T3u, T3t = casc(o["u"]), casc(o["e"])
    I = np.eye(2)

    def lump(Tu_, Tt_, Pp):
        Mu, Mt = Pp @ Tu_ @ mirror(Pp), Pp @ Tt_ @ mirror(Pp)
        dL = (Mt[0, 1].imag - Mu[0, 1].imag)/w
        dC = (Mt[1, 0].imag - Mu[1, 0].imag)/w
        return dL, dC, math.sqrt((Lb + dL/P)/(Cb + dC/P)), C0*math.sqrt((Lb + dL/P)*(Cb + dC/P))
    print(f"   {'cells':42} {'ports':6} | {'dL pH':>7} {'dC fF':>7} | {'Z0_final':>8} {'n_final':>7}")
    for lab, A_, B_ in (("3D quasi-static (no-slot, tee)", T3u, T3t), ("CST, de-embedded (no-tee, tee 2->3)", Tu, Tt)):
        for pl, Pp in (("none", I), ("CST", Pt)):
            dL, dC, Z, n = lump(A_, B_, Pp)
            print(f"   {lab:42} {pl:6} | {dL*1e12:7.2f} {dC*1e15:7.3f} | {Z:8.3f} {n:7.4f}")
    print(f"   {'dataset (one CST cell)':42} {'':6} | {ds['deltaL lumped']*1e12:7.2f} {ds['deltaC lumped']*1e15:7.3f} |"
          f" {ds.z0_final_val:8.3f} {ds.nm_final_val:7.4f}")


def self_cal():
    """7. Tee lines alone: the same port fit with the tee cell as the line (Z_B = a/d), no no-tee runs."""
    print("\n7. Self-calibration on the tee lines alone (as section 1 with the tee cell in place of the uniform")
    print("   line): Z_B = a/d of the fitted port map; compare with section 2 and with the no-tee port values")
    print(f"   {'metal':5} {'GHz':>4} | {'consist.':>8} | {'Z_B tee':>15} {'n':>6} | {'L pH':>7} {'C fF':>7}")
    for m in ("PEC", "GOLD"):
        for f in (20e9, 60e9, 100e9):
            M2 = cr.abcd(cr.read(os.path.join(cr.DIR, f"400 TEE {m}.s2p"))[0][f])
            M3 = cr.abcd(cr.read(os.path.join(cr.DIR, f"600 TEE {m}.s2p"))[0][f])
            g, zf, zb = line_line(M2, M3)
            g, n = branch(g, f, 2.7)
            e2, o2, _ = modes(M2); e3, o3, _ = modes(M3)
            zs = [1/cmath.tanh(g), cmath.tanh(g), 1/cmath.tanh(1.5*g), cmath.tanh(1.5*g), 1.0, -1.0]
            Pm, cons = fit_mobius(zs, [e2, o2, e3, o3, zf, zb])
            Z = Pm[0, 0]/Pm[1, 1]
            Pt = Pm @ np.diag([1/Z, 1.0])*cmath.sqrt(Z)
            w = 2*math.pi*f
            print(f"   {m:5} {f/1e9:4.0f} | {cons:8.1e} | {Z.real:7.3f}{Z.imag:+7.3f}j {n:6.3f} |"
                  f" {Pt[0, 1].imag/w*1e12:7.2f} {Pt[1, 0].imag/w*1e15:7.2f}")


if __name__ == "__main__":
    main()
    extra()
    self_cal()
