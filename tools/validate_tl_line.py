#!/usr/bin/env python3
"""
Offline checks of the scripted "TL line" element (no INTERCONNECT needed).

The element's maths lives in lumerical/tl_element_setup.lsf and, line for line,
in mzm_interconnect/scripted_line.py. These checks solve the network the
element will sit in and compare it with the two models already validated
against INTERCONNECT:

  1. straight electrode, element chain vs eo_transfer (the TW block's formula),
     complex, for a matched and a strongly mismatched source/termination
  2. electrode + bend + electrode, element chain vs the GUI's segmented cascade
  3. the table written for the element reads back to the same numbers
  4. power vs voltage wave convention: modulation output differs by sqrt(R0) only

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

    print(f"\n{sum(results)}/{len(results)} checks passed.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
