#!/usr/bin/env python3
"""
Self-check the eye model against limits where the answer is known in advance.

You do not need measured eyes to know whether an eye model is behaving. There
are several regimes where the correct answer follows from a closed form or from
a monotonicity argument, and a model that gets those right is doing arithmetic
you can trust for the cases in between.

Each check below prints what was expected, where the expectation comes from,
and what the model actually produced. Run it against your own .s2p:

    python tools/validate_eye.py path/to/line.s2p --L-meas 2.5 --L 16.5 --Rt 53

With no file it uses a synthetic line, so it also works as a regression test.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mzm_interconnect import parameters as P                       # noqa: E402
from mzm_interconnect.extractor import extract_line_fit            # noqa: E402
from mzm_interconnect.eye import simulate_eye                      # noqa: E402
from mzm_interconnect.physics import (eo_response, link_metrics,   # noqa: E402
                                      link_response)

RESULTS = []


def check(name, why, expected, got, tol=None, rel=None, passed=None):
    if passed is None:
        if rel is not None:
            passed = abs(got - expected) <= rel * abs(expected)
        else:
            passed = abs(got - expected) <= tol
    RESULTS.append(passed)
    mark = "PASS" if passed else "FAIL"
    exp = f"{expected:.4g}" if isinstance(expected, float) else str(expected)
    gt = f"{got:.4g}" if isinstance(got, float) else str(got)
    print(f"  [{mark}] {name}")
    print(f"         expected {exp}   got {gt}")
    print(f"         {why}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("s2p", nargs="?", default=None)
    ap.add_argument("--L-meas", type=float, default=8.0)
    ap.add_argument("--L", type=float, default=8.0)
    ap.add_argument("--Rt", type=float, default=40.0)
    ap.add_argument("--vpi", type=float, default=4.0)
    a = ap.parse_args()

    s2p = a.s2p
    if s2p is None:
        here = os.path.dirname(os.path.abspath(__file__))
        s2p = os.path.join(here, "..", "tests", "data", "synth_line_8mm.s2p")
        if not os.path.isfile(s2p):
            print("No .s2p given and no bundled synthetic line found.\n"
                  "Pass a Touchstone file as the first argument.")
            return 2

    fit = extract_line_fit(s2p, a.L_meas, 50.0, 0.5, "saturating")
    base = dict(P.defaults(), s2p_path=s2p, L_meas_mm=a.L_meas, L_target_mm=a.L,
                Rt_R=a.Rt, Vpi_V=a.vpi, f_max_GHz=300.0, n_points=3000,
                prbs_order=9, samples_per_symbol=32, eye_noise=False)
    bw = eo_response(fit, P.normalise(base)).bw_GHz
    base["drive_Vpp_V"] = link_metrics(P.normalise(base)).vpi_eff_V
    print(f"\nLine: {os.path.basename(s2p)}   L = {a.L} mm, Rt = {a.Rt} ohm")
    print(f"EO bandwidth {bw:.2f} GHz, V_pi,eff {base['drive_Vpp_V']:.3f} V, "
          f"drive set to V_pi,eff\n")

    # ---- 1. static extinction ratio is a closed form -------------------
    print("1. Static ER against its closed form")
    for d_loss in (0.5, 1.0, 3.0):
        p = P.normalise({**base, "arm_loss_imbalance_dB": d_loss})
        rho = 10 ** (-d_loss / 20.0)
        want = 20 * np.log10((1 + rho) / (1 - rho))
        check(f"arm loss {d_loss} dB", "ER = 20.log10((1+rho)/(1-rho)), "
              "rho = the field ratio of the two arms",
              float(want), float(link_metrics(p).er_dB), tol=1e-6)

    # ---- 2. chirp is a closed form ------------------------------------
    print("\n2. Chirp against its closed form")
    for d in (0.1, 0.3):
        p = P.normalise({**base, "vpi_imbalance_frac": d})
        check(f"V_pi imbalance {d*100:.0f} %",
              "alpha = (g1+g2)/(g1-g2) = d/(2+d) for push-pull",
              float(d / (2 + d)), float(link_metrics(p).chirp_alpha), tol=1e-9)

    # ---- 3. bandwidth is blind to the flat imbalances ------------------
    print("\n3. The four frequency-flat imbalances cannot move the -3 dB point")
    bw0 = link_response(fit, P.normalise(base)).bw_GHz
    for label, over in (("2 dB arm loss", {"arm_loss_imbalance_dB": 2.0}),
                        ("splitter 55:45", {"split_err": 0.05}),
                        ("30 % V_pi mismatch", {"vpi_imbalance_frac": 0.3}),
                        ("30 deg bias error", {"arm_phase_imbalance_deg": 30.0})):
        got = link_response(fit, P.normalise({**base, **over})).bw_GHz
        check(label, "each enters dP only through a frequency-flat factor, "
              "which cancels when the response is normalised",
              float(bw0), float(got), tol=1e-6)

    # ---- 4. group-index imbalance DOES move it ------------------------
    print("\n4. ...but a group-index mismatch does")
    got = link_response(fit, P.normalise({**base, "ng_imbalance": 0.05})).bw_GHz
    check("5 % n_g mismatch", "the two arms then have different walk-off, so "
          "H1 and H2 are different functions of frequency",
          True, bool(got < bw0 - 0.5), passed=bool(got < bw0 - 0.5))
    print(f"         (balanced {bw0:.2f} GHz -> mismatched {got:.2f} GHz)")

    # ---- 5. the ISI-free limit recovers the static ER ------------------
    print("\n5. At a low enough bit rate the eye ER must reach the static ceiling")
    # The driver and receiver bandwidths track the symbol rate by default -- a
    # real driver is specified as a fraction of the rate it has to serve -- so
    # simply slowing the data down does NOT remove intersymbol interference.
    # They have to be opened up as well, and then the only thing left to limit
    # the eye is the arm imbalance.
    rate = max(1.0, bw / 20.0)
    p_slow = P.normalise({**base, "arm_loss_imbalance_dB": 2.0,
                          "bitrate_Gbps": rate,
                          "drive_bw_GHz": 8.0 * rate,
                          "rx_bw_GHz": 8.0 * rate})
    want = link_metrics(p_slow).er_dB
    got = simulate_eye(fit, p_slow).er_dB
    check(f"bit rate = BW/20 = {rate:.1f} Gb/s, driver and receiver opened to "
          f"{8*rate:.0f} GHz",
          "with 8x the bandwidth it needs anywhere in the chain there is no "
          "intersymbol interference left, so the eye can only be limited by "
          "the arm imbalance -- the static ceiling",
          float(want), float(got), tol=0.5)

    # ---- 6. crossing sits at 50 % for a symmetric NRZ eye -------------
    print("\n6. A balanced, quadrature-biased NRZ eye crosses at 50 %")
    got = simulate_eye(fit, P.normalise({**base,
                                         "bitrate_Gbps": bw})).crossing_pct
    check("crossing point", "symmetric rise and fall about quadrature put the "
          "crossing halfway between the rails; an asymmetry here means the "
          "bias or the drive is not centred",
          50.0, float(got), tol=3.0)

    # ---- 7. the eye must close as the bit rate crosses the bandwidth --
    print("\n7. Eye height falls monotonically as the bit rate passes the bandwidth")
    rates = [0.25, 0.5, 1.0, 1.5, 2.0]
    hs = [simulate_eye(fit, P.normalise({**base, "bitrate_Gbps": r * bw})
                       ).eye_height_A for r in rates]
    mono = all(hs[i] >= hs[i + 1] - 1e-12 for i in range(len(hs) - 1))
    check("monotonic closure", "more bandwidth is never worse; a model that "
          "re-opens the eye above its own bandwidth is wrong",
          True, mono, passed=mono)
    for r, h in zip(rates, hs):
        print(f"         {r:.2f} x BW = {r*bw:6.1f} Gb/s -> eye height "
              f"{h*1e3:8.4f} mA")

    # ---- 8. noise-limited Q scales with received power ----------------
    print("\n8. Q scales with received power the way the noise says it should")
    p_noise = {**base, "bitrate_Gbps": bw, "eye_noise": True}
    pows = np.array([-20.0, -17.0, -14.0])
    qs = np.array([simulate_eye(fit, P.normalise({**p_noise, "P_laser_dBm": d})
                                ).q_factor for d in pows])
    # Q ~ P^n: thermal-limited gives n = 1, shot-limited n = 0.5.
    n = float(np.polyfit(pows / 10.0 * np.log(10), np.log(qs), 1)[0])
    check("power exponent", "Q ~ P^1 when a constant thermal term dominates, "
          "Q ~ P^0.5 when shot noise does; anything outside that band means "
          "the noise is not being added as a power spectral density",
          True, 0.45 <= n <= 1.15, passed=bool(0.45 <= n <= 1.15))
    print(f"         fitted exponent n = {n:.3f}   "
          f"(Q = {qs[0]:.2f}, {qs[1]:.2f}, {qs[2]:.2f} at "
          f"{pows[0]:.0f}/{pows[1]:.0f}/{pows[2]:.0f} dBm)")

    n_pass = sum(RESULTS)
    print(f"\n{n_pass}/{len(RESULTS)} checks passed.")
    return 0 if n_pass == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
