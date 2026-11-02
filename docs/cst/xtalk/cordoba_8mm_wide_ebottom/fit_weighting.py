"""30 GHz, electric bottom, six 2 mm eigenmodes: effect of the fit weighting.
The data are four patterns: A CPW, A slot, B' CPW, B' slot (CPW = (E+ - E-)/2, slot = (E+ + E-)/2).
Weightings: (1) as in fit30.py: one weight per line, 1/rms(line); (2) one weight per pattern, 1/rms(pattern);
(3) one common weight (absolute field). Residuals are reported per pattern, relative to that pattern's rms."""
import os, io, contextlib, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(HERE, "fit30_ebottom_2mm.py")).read().split("# free extra wave")[0])
cpw = lambda v: (v[0] - v[1]) / 2; slot = lambda v: (v[0] + v[1]) / 2
def solve(names_e, names_o, mode):
    ce, le = F.basis(names_e); co, lo = F.basis(names_o)
    colsA = [0.5 * c for c in ce] + [0.5 * c for c in co]
    colsB = [0.5 * c for c in ce] + [-0.5 * c for c in co]
    data = {"A CPW": cpw(F.A), "A slot": slot(F.A), "B CPW": cpw(F.Bp), "B slot": slot(F.Bp)}
    cols = {"A CPW": [cpw(c) for c in colsA], "A slot": [slot(c) for c in colsA],
            "B CPW": [cpw(c) for c in colsB], "B slot": [slot(c) for c in colsB]}
    rms = lambda v: np.sqrt(np.mean(np.abs(v) ** 2))
    if mode == "line":
        wA = 1 / np.sqrt(np.mean(np.abs(F.A) ** 2)); wB = 1 / np.sqrt(np.mean(np.abs(F.Bp) ** 2))
        w = {"A CPW": wA, "A slot": wA, "B CPW": wB, "B slot": wB}
    elif mode == "pattern":
        w = {k: 1 / rms(v) for k, v in data.items()}
    else:
        w = {k: 1.0 for k in data}
    M = np.vstack([np.array(cols[k]).T * w[k] for k in data]); d = np.concatenate([data[k] * w[k] for k in data])
    x, *_ = np.linalg.lstsq(M, d, rcond=None)
    out = {k: np.linalg.norm(data[k] - np.array(cols[k]).T @ x) / np.linalg.norm(data[k]) for k in data}
    out["model A slot / A CPW data"] = np.linalg.norm(np.array(cols["A slot"]).T @ x) / np.linalg.norm(data["A CPW"])
    return out
print("data: A slot / A CPW", f"{np.linalg.norm(slot(F.A))/np.linalg.norm(cpw(F.A)):.4f}",
      " B' rms / A rms", f"{np.sqrt(np.mean(np.abs(F.Bp)**2))/np.sqrt(np.mean(np.abs(F.A)**2)):.2e}")
for lab, ne, no in (("CPW + slot pairs", ["e_cpw", "e_slot"], ["o_cpw", "o_slot"]), ("all six", E, O)):
    print(f"\n{lab}:  weighting | A CPW | A slot | B' CPW | B' slot | model A slot / A CPW")
    for mode in ("line", "pattern", "absolute"):
        r = solve(ne, no, mode)
        print(f"   {mode:9s}          | {r['A CPW']:.3f} | {r['A slot']:6.2f} | {r['B CPW']:.3f}  | {r['B slot']:.3f}   | {r['model A slot / A CPW data']:.4f}")

# Is the tension caused by the even-odd splits? Pattern weighting, CPW split and slot split free (grid).
k0 = 2 * np.pi * F.F / F.C0; orig = F.gamma
fe = {F.MODES[k][1]: k for k in F.MODES}
def with_splits(d_cpw, d_slot):
    def g(f_GHz, Q, ng, n_override=None):
        gg, n, a = orig(f_GHz, Q, ng); nm = fe.get(f_GHz, "")
        sh = {"e_cpw": 0.5 * d_cpw, "o_cpw": -0.5 * d_cpw, "e_slot": 0.5 * d_slot, "o_slot": -0.5 * d_slot}.get(nm, 0.0)
        return gg + 1j * k0 * sh, n + sh, a
    return g
ne0 = orig(*F.MODES["e_cpw"][1:])[1] - orig(*F.MODES["o_cpw"][1:])[1]
ns0 = orig(*F.MODES["e_slot"][1:])[1] - orig(*F.MODES["o_slot"][1:])[1]
print(f"\neigen splits: CPW {ne0:.2e}, slot {ns0:.4f}. Pattern weighting, all six, splits changed by (dCPW, dslot):")
best = []
for dc in (-4e-5, -2e-5, 0, 2e-5, 4e-5, 8e-5, 1.2e-4):
    for ds in (-0.008, -0.004, 0, 0.004, 0.008, 0.016):
        F.gamma = with_splits(dc, ds); r = solve(E, O, "pattern"); F.gamma = orig
        best.append((r["A CPW"] + r["B CPW"] + r["B slot"], dc, ds, r))
best.sort(key=lambda t: t[0])
for s, dc, ds, r in best[:5]:
    print(f"   dCPW {dc:+.0e} dslot {ds:+.3f}: A CPW {r['A CPW']:.3f} A slot {r['A slot']:.2f} B' CPW {r['B CPW']:.3f} B' slot {r['B slot']:.3f}")
