#!/usr/bin/env python3
"""
Offline checks of the scripted "TL line" element (no INTERCONNECT needed).

The element's maths lives in lumerical/tl_element_setup.lsf and, line for line,
in mzm_interconnect/scripted_line.py. These checks solve the network the
element will sit in and compare it with the two models already validated
against INTERCONNECT:

  1. straight electrode, element chain vs eo_transfer (the TW block's formula),
     complex, for a matched and a strongly mismatched source/termination,
     and power vs voltage wave convention (outputs differ by sqrt(R0) only)
  2. electrode + bend + electrode, element chain vs the GUI's segmented cascade
  3. the table written for the element reads back to the same numbers
  4. the second modulation output (arm 2, its own n_g) vs the cascade at that n_g
  5. R + L + C source and load, and the far-end voltage, vs closed forms
  6. the TL electrode element (a whole bent electrode in one element), 0-4 bends:
     against the chain of TL line elements and against the GUI's device response

    python tools/validate_tl_line.py [path/to/line.s2p --L-meas 2.5]

With no file it uses the synthetic line in tests/data.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mzm_interconnect import parameters as P                        # noqa: E402
from mzm_interconnect import scripted_line as SL                    # noqa: E402
from mzm_interconnect.extractor import extract_line_fit, line_tables  # noqa: E402
from mzm_interconnect.physics import (bend_line, electrode_layout,  # noqa: E402
                                      eo_transfer, segmented_transfer)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("s2p", nargs="?", default=os.path.join(ROOT, "tests", "data",
                                                            "synth_line_8mm.s2p"))
    ap.add_argument("--L-meas", type=float, default=None,
                    help="measured line length, mm (8 for the synthetic file)")
    a = ap.parse_args(argv)
    L_meas = a.L_meas if a.L_meas is not None else (
        8.0 if a.s2p.endswith("synth_line_8mm.s2p") else 2.5)
    fit = extract_line_fit(a.s2p, L_meas, 50.0, 0.5, "saturating")
    out = tempfile.mkdtemp()
    base = dict(P.defaults(), s2p_path=a.s2p, L_meas_mm=L_meas, f_max_GHz=150.0,
                ic_sample_rate_GHz=640.0)
    tol = 1e-4                  # the LSF's exact dB->Np constant vs physics.py's 1/8.686
    results = []

    def check(name, value, limit, detail):
        ok = value < limit
        results.append(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {value:.2e} (limit {limit:.0e})  {detail}")

    print("1. straight electrode: TL line chain vs eo_transfer (complex)")
    for Zs, Rt in ((50.0, 50.0), (30.0, 80.0)):
        p = P.normalise(dict(base, L_target_mm=10.0, Zs_R=Zs, Rt_R=Rt))
        paths = SL.export_tl_tables(fit, p, out)
        els, _ = SL.device_chain(paths)
        r = SL.chain_response(els, Zs, Rt)
        f = r.f_Hz / 1e9
        m = f > 0
        al, Zc, nm = line_tables(fit, p, f[m])
        H_tw, _ = eo_transfer(f[m], al, nm, Zc, 10e-3, float(p["ng"]), Zs, Rt)
        # eo_transfer carries an overall minus sign; the TL line uses the physical one
        check(f"Zs {Zs:g} / Rt {Rt:g} ohm", float(np.max(np.abs(r.H[m] / -H_tw - 1))), tol,
              f"BW {SL.bw_GHz(f[m], r.H[m]):.3f} vs {SL.bw_GHz(f[m], H_tw):.3f} GHz")
        rp = SL.chain_response(SL.device_chain(paths, waves="power")[0], Zs, Rt)
        check("  power waves / sqrt(R0) = voltage waves",
              float(np.max(np.abs(rp.H / (r.H * np.sqrt(50.0)) - 1))), 1e-9, "")

    print("2. electrode + bend + electrode: TL line chain vs the GUI cascade")
    for Zb, Lb in ((60.0, 0.8), (35.0, 1.6)):
        p = P.normalise(dict(base, n_bends=1, tw_len_1_mm=5, tw_len_2_mm=7,
                             bend_len_mm=Lb, bend_Z_ohm=Zb))
        paths = SL.export_tl_tables(fit, p, out)
        els, opt = SL.device_chain(paths)
        r = SL.chain_response(els, float(p["Zs_R"]), float(p["Rt_R"]), opt_lengths=opt)
        f = r.f_Hz / 1e9
        m = f > 0
        al, Zc, nm = line_tables(fit, p, f[m])
        seg = segmented_transfer(f[m], al, nm, Zc, electrode_layout(p), float(p["ng"]),
                                 float(p["Zs_R"]), float(p["Rt_R"]), **bend_line(p, f[m]))
        check(f"bend {Lb:g} mm at {Zb:g} ohm, 5 + 7 mm",
              float(np.max(np.abs(np.abs(r.H[m]) / np.abs(seg.H) - 1))), tol,
              f"BW {SL.bw_GHz(f[m], r.H[m]):.3f} vs {SL.bw_GHz(f[m], seg.H):.3f} GHz")

    print("3. table round trip")
    f, loss, nm_t, Z = SL.read_tl_table(paths["electrode"])
    al, Zc, nm = line_tables(fit, p, f[1:] / 1e9)
    check("electrode_line.txt vs the fit", float(np.max(np.abs(Z[1:] / Zc - 1))), 1e-9,
          f"{len(f)} rows incl. the DC row, up to {f[-1]/1e9:.0f} GHz")

    print("4. second modulation output (push-pull arm 2, its own n_g)")
    p = P.normalise(dict(base, n_bends=1, tw_len_1_mm=5, tw_len_2_mm=7, bend_len_mm=0.8,
                         bend_Z_ohm=60.0, ng_imbalance=0.02))
    paths = SL.export_tl_tables(fit, p, out)
    els, opt = SL.device_chain(paths, second=True)
    r = SL.chain_response(els, float(p["Zs_R"]), float(p["Rt_R"]), opt_lengths=opt)
    f = r.f_Hz / 1e9
    m = f > 0
    al, Zc, nm = line_tables(fit, p, f[m])
    for arm, H, ngk in ((1, r.H, els[0]["ng"]), (2, r.H2, els[0]["ng2"])):
        seg = segmented_transfer(f[m], al, nm, Zc, electrode_layout(p), ngk,
                                 float(p["Zs_R"]), float(p["Rt_R"]), **bend_line(p, f[m]))
        check(f"arm {arm}, n_g = {ngk:.4f}: chain vs cascade at that n_g",
              float(np.max(np.abs(np.abs(H[m]) / np.abs(seg.H) - 1))), tol,
              f"BW {SL.bw_GHz(f[m], H[m]):.3f} vs {SL.bw_GHz(f[m], seg.H):.3f} GHz")
    p0 = P.normalise(dict(p, ng_imbalance=0.0))
    els0, opt0 = SL.device_chain(SL.export_tl_tables(fit, p0, out), second=True)
    r0 = SL.chain_response(els0, float(p["Zs_R"]), float(p["Rt_R"]), opt_lengths=opt0)
    check("no imbalance: modulation 2 = modulation", float(np.max(np.abs(r0.H2 - r0.H))),
          1e-15, "")

    print("5. source and load with R + L + C, and the far-end voltage")
    from mzm_interconnect.physics import rlc_impedance
    fz = np.linspace(0.0, 300.0, 601)
    for R, Lp, Cf in ((45.0, 80.0, 0.0), (55.0, 120.0, 40.0), (50.0, 0.0, 30.0)):
        zl = SL.rlc_z(fz * 1e9, R, Lp * 1e-12, Cf * 1e-15)
        zp = rlc_impedance(fz, R, Lp, Cf)
        check(f"rlc_z (as the LSF) = physics.rlc_impedance, {R:g} ohm {Lp:g} pH {Cf:g} fF",
              float(np.max(np.abs(zl / zp - 1))), 1e-12, "")
    p = P.normalise(dict(base, L_target_mm=10.0, Zs_R=40.0, Zs_L_pH=60.0, Zs_C_fF=20.0,
                         Rt_R=60.0, Rt_L_pH=90.0, Rt_C_fF=35.0))
    paths = SL.export_tl_tables(fit, p, out)
    els, _ = SL.device_chain(paths)
    Zs_f, Zt_f = SL.device_terminations(paths, els[0]["f_Hz"])
    r = SL.chain_response(els, Zs_f, Zt_f)
    f = r.f_Hz / 1e9
    m = f > 0
    al, Zc, nm = line_tables(fit, p, f[m])
    Zs_p = rlc_impedance(f[m], 40.0, 60.0, 20.0)
    Zt_p = rlc_impedance(f[m], 60.0, 90.0, 35.0)
    H_tw, zin = eo_transfer(f[m], al, nm, Zc, 10e-3, float(p["ng"]), Zs_p, Zt_p)
    check("RLC source and load: chain vs eo_transfer", float(np.max(np.abs(r.H[m] / -H_tw - 1))),
          tol, f"BW {SL.bw_GHz(f[m], r.H[m]):.3f} vs {SL.bw_GHz(f[m], H_tw):.3f} GHz")
    # Far end, closed form: V(0) = E zin / (Zs + zin), V(L) = V(0) / (cosh gL + Zc/Zt sinh gL)
    gL = (al * 100.0 * np.log(10) / 20 + 1j * 2 * np.pi * f[m] * 1e9 * nm / 299792458.0) * 10e-3
    VL = zin / (Zs_p + zin) / (np.cosh(gL) + Zc / Zt_p * np.sinh(gL))
    check("far end of the last element = V across the termination (closed form)",
          float(np.max(np.abs(r.far_end[-1][m] / VL - 1))), tol,
          f"|V(L)/EMF| at 1 GHz {abs(np.interp(1.0, f[m], np.abs(VL))):.4f}")

    print("6. TL electrode element (one element per bent electrode) for 0-4 bends")
    from mzm_interconnect.physics import device_response
    cases = [(0, dict()),
             (1, dict(tw_len_1_mm=7, tw_len_2_mm=7, bend_len_mm=0.8, bend_Z_ohm=60.0)),
             (1, dict(tw_len_1_mm=7, tw_len_2_mm=7, bend_len_mm=0.0, bend_Z_ohm=60.0)),
             (2, dict(tw_len_1_mm=3, tw_len_2_mm=6, tw_len_3_mm=5, bend_len_mm=1.2,
                      bend_opt_len_mm=1.5, bend_Z_ohm=35.0, ng_imbalance=0.02)),
             (3, dict(bend_len_mm=0.6, bend_Z_ohm=80.0, Zs_L_pH=40.0, Rt_C_fF=25.0)),
             (4, dict(tw_len_1_mm=2, tw_len_2_mm=4, tw_len_3_mm=3, tw_len_4_mm=2.5,
                      tw_len_5_mm=2.5, bend_len_mm=1.0, bend_Z_ohm=45.0, ng_imbalance=-0.03))]
    for nb, extra in cases:
        p = P.normalise(dict(base, L_target_mm=14.0, Zs_R=50.0, Rt_R=55.0, n_bends=nb, **extra))
        paths = SL.export_tl_tables(fit, p, out)
        el = SL.tl_electrode_from_paths(paths, second=True)
        els, opt = SL.device_chain(paths, second=True)
        Zs_f, Zt_f = SL.device_terminations(paths, el["f_Hz"])
        r_el = SL.chain_response([el], Zs_f, Zt_f)
        r_ch = SL.chain_response(els, Zs_f, Zt_f, opt_lengths=opt)
        f = el["f_Hz"] / 1e9
        m = (f > 0) & (f <= 150)
        tag = f"{nb} bend(s)" + (", 0 mm bend" if nb and extra.get("bend_len_mm") == 0 else "")
        err = max(float(np.max(np.abs(r_el.H[m] / r_ch.H[m] - 1))),
                  float(np.max(np.abs(r_el.H2[m] / r_ch.H2[m] - 1))),
                  float(np.max(np.abs(r_el.far_end[0][m] / r_ch.far_end[-1][m] - 1))),
                  float(np.max(np.abs(r_el.s11_in[m] - r_ch.s11_in[m]))))
        check(f"{tag}: one element = chain of elements (both arms, far end, S11)", err, 1e-9, "")
        res = device_response(fit, p)
        from mzm_interconnect.physics import arm_models
        a1, a2 = arm_models(p)
        Hd = (a1.g * r_el.H - a2.g * r_el.H2) / (a1.g - a2.g)
        fr = res.f_GHz
        k = (fr >= 0.5) & (fr <= 150.0)
        mag = np.interp(fr[k], f, np.abs(Hd)) / np.abs(res.H[k])
        mag = mag / np.median(mag[fr[k] <= 3.0])
        check(f"{tag}: element vs GUI device response, |H| shape to 150 GHz",
              float(np.max(np.abs(20 * np.log10(mag)))), 2e-3,
              f"(GUI BW {res.bw_GHz:.3f} GHz)")

    print(f"\n{sum(results)}/{len(results)} checks passed.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
