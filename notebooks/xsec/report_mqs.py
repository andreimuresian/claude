"""Section average with the gold-interior conductor model.  Run: python report_mqs.py

Per section: C, G, C_air from run_rows.json (quasi-static, notebook mesh);
R' and L_int from run_mqs.json (gold interior, finger floating).
    L = 1/(c^2 C_air) + L_int,   R = R'_gold
Old column (IBC) = the same average with the notebook's IBC R' and L_int = R'/w.

Scoring.  The dataset final is COMSOL baseline + multilayer perturbation.  The
2D section C is the 2D code's own baseline.  The two are compared separately:
  table 1  baseline: section C against the COMSOL baseline;
  table 2  perturbation: (average - section C) against (final - baseline),
           as a share of the final value and as the fraction of it reproduced,
           and next to it the error of ignoring the tee (section C alone).
For alpha the reference is the final value with the COMSOL baseline replaced by
the gold-interior section C: alpha_ref = alpha_final - alpha_base + alpha_C,gold.
"""
import json
import os

import numpy as np

import xsec2d as x
from average import combine, load_rows

HERE = os.path.dirname(os.path.abspath(__file__))


def lines_gold(qs, mq, fing):
    return dict(L=1.0 / (x.C0 ** 2 * qs[f"Cair_{fing}"]) + mq["L_int"], C=qs["C"], R=mq["R"], G=qs["G"])


def main():
    qsj = json.load(open(os.path.join(HERE, "run_rows.json")))
    mqj = json.load(open(os.path.join(HERE, "run_mqs.json")))
    D = load_rows()
    rows = sorted({int(k.split("_")[0]) for k in mqj}, key=lambda r: D.nm_final_val[r] / D.nm_baseline_val[r])
    rows = [r for r in rows if all(f"{r}_{s}" in mqj for s in "ABC")]
    res = {}
    for row in rows:
        r = D.loc[row]
        fing = {s: ("float" if s == "B" else "gnd") for s in "ABC"}
        gold = {s: lines_gold(qsj[f"{row}_{s}"]["qs"], mqj[f"{row}_{s}"], fing[s]) for s in "ABC"}
        ibc = {s: x.qs_lines(qsj[f"{row}_{s}"]["qs"], fing[s]) for s in "ABC"}
        res[row] = dict(r=r, g=combine(r, gold), i=combine(r, ibc), gold=gold, ibc=ibc)

    print("1. Baseline: section C of the 2D code vs the COMSOL baseline (dataset)")
    print("   alpha: notebook IBC (notebook mesh) and gold interior;  n, Z0: gold interior")
    print("   last column: 2D share of the IBC loss correction on n, Z0 = sqrt(L_gold / L_IBC) - 1")
    print(" row  MTX  | a_COMSOL  a_IBC   a_gold | gold/COMSOL gold/IBC | n_gold   Z0_gold  | dn,dZ0 from L_int")
    for row in rows:
        r, g, i = res[row]["r"], res[row]["g"], res[row]["i"]
        dL = np.sqrt(res[row]["gold"]["C"]["L"] / res[row]["ibc"]["C"]["L"]) - 1
        print(f" {row:3d} {r.MTX:5.2f} |  {r.alpha_baseline_val:6.3f}  {i['alphaC']:6.3f}  {g['alphaC']:6.3f} |"
              f"   {(g['alphaC'] / r.alpha_baseline_val - 1) * 100:+6.1f}%    {(g['alphaC'] / i['alphaC'] - 1) * 100:+6.1f}% |"
              f" {(g['nC'] / r.nm_baseline_val - 1) * 100:+6.2f}% {(g['Z0C'] / r.z0_baseline_val - 1) * 100:+6.2f}%  |"
              f"  {dL * 100:+5.2f}%")

    print("\n2. Perturbation: 2D (average - section C) vs dataset (final - baseline)")
    print("   err = (d_2D - d_dataset) / final value;  got = d_2D / d_dataset")
    print("                     n                  |           Z0               |              alpha (dB/cm)")
    print(" row  n_fin/n_b | d_data  d_2D  err   got | d_data  d_2D   err   got | d_data  d_2D(gold) d_2D(IBC) err(gold)")
    E = []
    for row in rows:
        r, g, i = res[row]["r"], res[row]["g"], res[row]["i"]
        dn_d, dn_2 = r.nm_final_val - r.nm_baseline_val, g["n"] - g["nC"]
        dz_d, dz_2 = r.z0_final_val - r.z0_baseline_val, g["Z0"] - g["Z0C"]
        da_d, da_2, da_i = r.alpha_final_val - r.alpha_baseline_val, g["alpha"] - g["alphaC"], i["alpha"] - i["alphaC"]
        a_ref = r.alpha_final_val - r.alpha_baseline_val + g["alphaC"]       # COMSOL baseline -> gold baseline
        en, ez, ea = (dn_2 - dn_d) / r.nm_final_val, (dz_2 - dz_d) / r.z0_final_val, (da_2 - da_d) / a_ref
        E.append((en, ez, ea, dn_2 / dn_d, dz_2 / dz_d, da_d,
                  dn_d / r.nm_final_val, dz_d / r.z0_final_val, da_d / a_ref))     # error if the tee is ignored
        print(f" {row:3d}  {r.nm_final_val / r.nm_baseline_val:5.3f}   | {dn_d:+.3f} {dn_2:+.3f} {en * 100:+5.1f}% {dn_2 / dn_d * 100:3.0f}% |"
              f" {dz_d:+6.2f} {dz_2:+6.2f} {ez * 100:+5.1f}% {dz_2 / dz_d * 100:3.0f}% |"
              f" {da_d:+6.2f}  {da_2:+6.2f}     {da_i:+6.2f}    {ea * 100:+6.1f}%")
    E = np.array(E)
    adds = E[:, 5] > 0.5                    # rows where the dataset says the tee adds loss
    print(" |err| median / max:   n {:.1f} / {:.1f} %   Z0 {:.1f} / {:.1f} %   alpha {:.1f} / {:.1f} %".format(
        *(f(np.abs(E[:, k]) * 100) for k in range(3) for f in (np.median, np.max))))
    print(f" fraction of the dataset perturbation reproduced (median, range):"
          f"  n {np.median(E[:, 3]) * 100:.0f}% ({E[:, 3].min() * 100:.0f}-{E[:, 3].max() * 100:.0f}%)"
          f"   Z0 {np.median(E[:, 4]) * 100:.0f}% ({E[:, 4].min() * 100:.0f}-{E[:, 4].max() * 100:.0f}%)")
    print(" ignoring the tee (2D section C alone), |err| median / max:   n {:.1f} / {:.1f} %   Z0 {:.1f} / {:.1f} %"
          "   alpha {:.1f} / {:.1f} %".format(*(f(np.abs(E[:, k]) * 100) for k in (6, 7, 8) for f in (np.median, np.max))))
    for name, sel in ((f"{(~adds).sum()} rows with d_data <= +0.5 dB/cm", ~adds),
                      (f"{adds.sum()} rows with d_data  > +0.5 dB/cm", adds)):
        print(f" alpha, {name}: |err| median / max  2D average {np.median(np.abs(E[sel, 2])) * 100:4.1f} /"
              f" {np.abs(E[sel, 2]).max() * 100:4.1f} %,  ignoring the tee {np.median(np.abs(E[sel, 8])) * 100:4.1f} /"
              f" {np.abs(E[sel, 8]).max() * 100:4.1f} %")


if __name__ == "__main__":
    main()
