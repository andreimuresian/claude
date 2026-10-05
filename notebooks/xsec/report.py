"""Tables from run_rows.json.  Run: python report.py"""
import json
import os

import numpy as np

import xsec2d as x
from average import average, combine, load_rows

HERE = os.path.dirname(os.path.abspath(__file__))


def fw_lines(res):
    fw, qs = res["fw"], res["qs"]
    return dict(L=fw["Z0"] * fw["n"] / x.C0, C=fw["n"] / (fw["Z0"] * x.C0), R=fw["R"], G=qs["G"])


def main():
    out = json.load(open(os.path.join(HERE, "run_rows.json")))
    D = load_rows()
    rows = sorted({int(k.split("_")[0]) for k in out}, key=lambda r: D.nm_final_val[r] / D.nm_baseline_val[r])
    rows = [r for r in rows if all(f"{r}_{s}" in out for s in "ABC")]

    print("Section C (no slot) vs the dataset baseline (COMSOL)")
    print(" row | FW n err  Z0 err  a err | QS n err  Z0 err  a err")
    for row in rows:
        r, res = D.loc[row], out[f"{row}_C"]
        n, Z, a = x.line_fom(**x.qs_lines(res["qs"]))
        fw = res["fw"]
        e = lambda v, ref: (v / ref - 1) * 100
        print(f" {row:3d} | {e(fw['n'], r.nm_baseline_val):+6.2f}% {e(fw['Z0'], r.z0_baseline_val):+6.2f}% "
              f"{e(fw['alpha_dB_cm'], r.alpha_baseline_val):+6.2f}% | {e(n, r.nm_baseline_val):+6.2f}% "
              f"{e(Z, r.z0_baseline_val):+6.2f}% {e(a, r.alpha_baseline_val):+6.2f}%")

    variants = {
        "slides, full-wave": lambda r, q: combine(r, {s: fw_lines(q[s]) for s in "ABC"}),
        "slides, quasi-static": lambda r, q: average(r, {s: q[s]["qs"] for s in "ABC"}, "gnd"),
        "floating finger, quasi-static": lambda r, q: average(r, {s: q[s]["qs"] for s in "ABC"}, "float"),
    }
    summary = {}
    for name, f in variants.items():
        print(f"\n=== {name} ===   errors vs dataset final values (absolute | additive on the dataset baseline)")
        print(" row  wA   wB   wC  | n_ref  Z_ref  a_ref  | n err  Z0 err  a err  | n err  Z0 err  a err (a pred)")
        errs = []
        for row in rows:
            r = D.loc[row]
            q = {s: out[f"{row}_{s}"] for s in "ABC"}
            if any("error" in q[s]["fw"] for s in "ABC") and "full-wave" in name:
                print(f" {row:3d}  full-wave filter failed"); continue
            d = f(r, q)
            e = [(d[k] / ref - 1) * 100 for k, ref in (("n", r.nm_final_val), ("Z0", r.z0_final_val),
                                                       ("alpha", r.alpha_final_val), ("n_add", r.nm_final_val),
                                                       ("Z0_add", r.z0_final_val), ("alpha_add", r.alpha_final_val))]
            errs.append(e)
            print(f" {row:3d} {d['wA']:.2f} {d['wB']:.2f} {d['wC']:.2f} | {r.nm_final_val:.3f} {r.z0_final_val:6.2f} "
                  f"{r.alpha_final_val:5.2f} | {e[0]:+6.2f} {e[1]:+6.2f} {e[2]:+6.1f} | {e[3]:+6.2f} {e[4]:+6.2f} "
                  f"{e[5]:+6.1f} ({d['alpha_add']:.2f})")
        E = np.abs(np.array(errs))
        summary[name] = E
        print("  median |err|  " + "  ".join(f"{v:5.2f}" for v in np.median(E, 0)))
        print("  max    |err|  " + "  ".join(f"{v:5.2f}" for v in E.max(0)))


if __name__ == "__main__":
    main()
