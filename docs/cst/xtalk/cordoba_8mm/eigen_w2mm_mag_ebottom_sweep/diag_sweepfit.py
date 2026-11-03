"""Diagnostics of the sweep fit: (1) where the EO of the data comes from (ends, stems, interior);
(2) B' CPW residual with A's slot weight 1 and with B weighted alone; (3) hold-out: fit on one half of the
interior, predict B' CPW on the other half (residual and EO of the predicted half)."""
import numpy as np, sweepfit as S
db = lambda v: 20 * np.log10(abs(v))
print("(1) EO of the data (dB): full line | samples 0.31-7.69 mm all | interior without stems | ends only (z<0.31 or >7.69)")
for f in S.FTD:
    td = S.TDData(f); z = td.z_full; bo = 2*np.pi*f*1e9*S.NG_OPT/S.C0
    w = np.exp(1j*bo*(z - z[-1])); cb, ca = S.cpw(td.Bp_full), S.cpw(td.A_full)
    dz = np.gradient(z)
    def X(m): return np.sum(cb[m]*w[m]*dz[m]) / np.sum(ca*w*dz)       # B part over A full
    inner = (z >= 0.31e-3-1e-9) & (z <= 7.69e-3+1e-9)
    idx = np.round(((z*1e3-0.04) % 0.18)/0.005).astype(int) % 36; stem = (idx >= 13) & (idx <= 23)
    full = np.ones_like(z, bool)
    print(f"  {f:2d} GHz  {db(X(full)):7.2f} | {db(X(inner)):7.2f} | {db(X(inner & ~stem)):7.2f} | {db(X(~inner)):7.2f}"
          f"   |A| H full/interior-no-stem {abs(np.sum(ca*w*dz)/np.sum((ca*w*dz)[inner&~stem])):.3f}")
print("\n(2) B' CPW residual: weighting  line+Aslot x10 | line | B only (A not fitted)")
for f in S.FTD:
    td = S.TDData(f); r = []
    for ws in (10.0, 1.0):
        r.append(S.fit(f, td, wslotA=ws)["res"]["B CPW"])
    # B only: tiny weight on A
    o = S.fit(f, td, wslotA=1e-6)
    import types
    tdB = types.SimpleNamespace(**td.__dict__); tdB.A = td.A * 1e-6 + 0j
    ce, le, _ = S.basis(("e_cpw","e_slot","e_sb"), f, td); co, lo, _ = S.basis(("o_cpw","o_slot","o_AvsB"), f, td)
    cols = [S.cpw(0.5*c) for c in ce] + [S.cpw(-0.5*c) for c in co]
    M = np.array(cols).T; d = S.cpw(td.Bp); x, *_ = np.linalg.lstsq(M, d, rcond=None)
    rb = np.linalg.norm(d - M@x)/np.linalg.norm(d)
    print(f"  {f:2d} GHz  {r[0]:.3f} | {r[1]:.3f} | {rb:.3f}")
print("\n(3) hold-out (line weights, A slot x10): fit on one half, B' CPW on the other half")
print("   f | fit 1st half -> 2nd: resid, EO err dB | fit 2nd half -> 1st: resid, EO err dB | all-fit resid per half")
import copy
for f in S.FTD:
    td = S.TDData(f); out = []
    for train in (td.zz < 4e-3, td.zz >= 4e-3):
        tr = copy.copy(td); tr.zz, tr.A, tr.Bp, tr.idx = td.zz[train], td.A[:, train], td.Bp[:, train], td.idx[train]
        o = S.fit(f, tr); x = np.array(list(o["x"].values()))
        te = copy.copy(td); m = ~train; te.zz, te.A, te.Bp, te.idx = td.zz[m], td.A[:, m], td.Bp[:, m], td.idx[m]
        ce, _, _ = S.basis(("e_cpw","e_slot","e_sb"), f, te); co, _, _ = S.basis(("o_cpw","o_slot","o_AvsB"), f, te)
        mB = np.array([S.cpw(0.5*c) for c in ce] + [S.cpw(-0.5*c) for c in co]).T @ x
        dB_ = S.cpw(te.Bp); bo = 2*np.pi*f*1e9*S.NG_OPT/S.C0; w = np.exp(1j*bo*(te.zz - S.L))
        out.append((np.linalg.norm(dB_-mB)/np.linalg.norm(dB_), db(np.sum(mB*w)/np.sum(dB_*w))))
    o = S.fit(f, td); mb = o["model"]["B CPW"]; d = o["data"]["B CPW"]
    h = [np.linalg.norm((d-mb)[s])/np.linalg.norm(d[s]) for s in (td.zz < 4e-3, td.zz >= 4e-3)]
    print(f"  {f:2d} | {out[0][0]:6.3f} {out[0][1]:+6.2f} | {out[1][0]:6.3f} {out[1][1]:+6.2f} | {h[0]:.3f} {h[1]:.3f}")
