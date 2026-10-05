"""Tables from run_rows.json.  Run: python report.py

Headline numbers use the quasi-static + IBC section solves: there the finger can
be tied to ground (slides) or carry no net current (floating).  The full-wave
eigen solve cannot do either: a 2D eigenmode leaves the finger an isolated
conductor whose potential the mode decides.  Full-wave is kept as the check of
section C against the dataset baseline, and as a diagnostic table per section.
"""
import json
import os

import numpy as np

import xsec2d as x
from average import average, load_rows

HERE = os.path.dirname(os.path.abspath(__file__))
# ../qs3d/README.md: 3D quasi-static unit cell (cascade), errors vs the same final values
QS3D = {118: (-0.13, -2.16), 416: (0.09, -0.58), 121: (-0.20, -3.18), 38: (-0.60, -4.58), 49: (-0.91, -6.08)}


def e(v, ref):
    return (v / ref - 1) * 100


def main():
    out = json.load(open(os.path.join(HERE, "run_rows.json")))
    D = load_rows()
    rows = sorted({int(k.split("_")[0]) for k in out}, key=lambda r: D.nm_final_val[r] / D.nm_baseline_val[r])
    rows = [r for r in rows if all(f"{r}_{s}" in out for s in "ABC")]

    print("1. Section C (no slot) vs the dataset baseline (COMSOL)")
    print(" row | QS+IBC  n      Z0     alpha | full-wave  n      Z0     alpha  (div, score)")
    for row in rows:
        r, res = D.loc[row], out[f"{row}_C"]
        n, Z, a = x.line_fom(**x.qs_lines(res["qs"]))
        fw = res["fw"]
        s = (f" {row:3d} |        {e(n, r.nm_baseline_val):+6.2f}% {e(Z, r.z0_baseline_val):+6.2f}% "
             f"{e(a, r.alpha_baseline_val):+6.2f}% |")
        if "error" in fw:
            s += "  " + fw["error"]
        else:
            s += (f"           {e(fw['n'], r.nm_baseline_val):+6.2f}% {e(fw['Z0'], r.z0_baseline_val):+6.2f}% "
                  f"{e(fw['alpha_dB_cm'], r.alpha_baseline_val):+6.2f}%  ({fw['div']*100:.1f}%, {fw['score']:.3f})")
        print(s)

    print("\n2. Full-wave vs quasi-static per section (diagnostic): Z0_fw / Z0_qs - 1, mode score")
    for row in rows:
        s = f" {row:3d}"
        for sec in "CAB":
            res = out[f"{row}_{sec}"]
            Zq = x.line_fom(**x.qs_lines(res["qs"]))[1]
            fw = res["fw"]
            s += f" | {sec} " + ("filter failed      " if "error" in fw else
                                  f"{e(fw['Z0'], Zq):+6.1f}%  {fw['score']:.3f}")
        print(s)

    summary = {}
    for name, fing in (("slides (finger carries current)", "gnd"), ("floating finger (finger carries no net current)", "float")):
        print(f"\n3. {name}: errors vs the dataset final values")
        print("    absolute = 2D code only;  additive = dataset baseline + 2D perturbation")
        print(" row   wA   wB   wC  | n_ref  Z0_ref a_ref | absolute n   Z0     a    | additive n   Z0     a     (a pred) | qs3d n  Z0")
        errs = []
        for row in rows:
            r = D.loc[row]
            d = average(r, {s: out[f"{row}_{s}"]["qs"] for s in "ABC"}, fing)
            ee = [e(d["n"], r.nm_final_val), e(d["Z0"], r.z0_final_val), e(d["alpha"], r.alpha_final_val),
                  e(d["n_add"], r.nm_final_val), e(d["Z0_add"], r.z0_final_val), e(d["alpha_add"], r.alpha_final_val)]
            errs.append(ee)
            q3 = QS3D.get(row)
            print(f" {row:3d} {d['wA']:.2f} {d['wB']:.2f} {d['wC']:.2f} | {r.nm_final_val:.3f} {r.z0_final_val:6.2f} "
                  f"{r.alpha_final_val:5.2f} |  {ee[0]:+6.2f} {ee[1]:+6.2f} {ee[2]:+6.1f}  |  {ee[3]:+6.2f} {ee[4]:+6.2f} "
                  f"{ee[5]:+6.1f} ({d['alpha_add']:5.2f})  |" + (f" {q3[0]:+5.2f} {q3[1]:+5.2f}" if q3 else ""))
        E = np.abs(np.array(errs))
        summary[fing] = E
        print(" median |err|              " + "  ".join(f"{v:6.2f}" for v in np.median(E, 0)))
        print(" max    |err|              " + "  ".join(f"{v:6.2f}" for v in E.max(0)))

    print("\n4. Delta alpha (dB/cm): dataset alpha_delta vs the floating-finger section average")
    print(" row  dataset   2D    | alpha_base  ")
    for row in rows:
        r = D.loc[row]
        d = average(r, {s: out[f"{row}_{s}"]["qs"] for s in "ABC"}, "float")
        print(f" {row:3d}  {r.alpha_delta_val:+6.2f}  {d['alpha'] - d['alphaC']:+6.2f}  |  {r.alpha_baseline_val:5.2f}")


if __name__ == "__main__":
    main()
