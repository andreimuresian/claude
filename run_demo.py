#!/usr/bin/env python3
"""End-to-end demo of the pure-Python composite pipeline.

Runs the whole chain for one geometry and prints the composite result:

  1. 2D cross-section  ->  baseline n_m, Z0, alpha    (replaces COMSOL)
  2. 3D unit cell      ->  lumped penalties dL, dC    (replaces CST MoM)
  3. synthesis         ->  3D, tee-perturbed n_m, Z0

No ports, no Touchstone files, no de-embedding, no N+1 minus N.

Usage
-----
    python run_demo.py              # ~3-5 min, coarse 3D mesh
    python run_demo.py --full       # ~10-15 min, finer 3D mesh
    python run_demo.py --2d-only    # seconds, skips the 3D cell
"""

import argparse
import sys
import time

sys.path.insert(0, ".")

from tfln2d import CrossSection, extract
from tfln2d.synthesis import synthesize

# One geometry, expressed once and shared by both solvers.
GEOMETRY = dict(ws=35.0, gap=6.0, t_au=1.0)
STUB = dict(L1=20.0, L2=60.0, W1=15.0, W2=25.0)
PITCH = 200.0

PRESETS = {
    "quick": dict(res_2d=0.5, lc_gap=3.0, air_h=40.0, si_h=60.0,
                  n_air=4, n_si=4),
    "full": dict(res_2d=0.25, lc_gap=1.5, air_h=60.0, si_h=100.0,
                 n_air=6, n_si=5),
}


def banner(text):
    print(f"\n{'=' * 66}\n{text}\n{'=' * 66}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="finer meshes, slower")
    ap.add_argument("--2d-only", dest="two_d", action="store_true",
                    help="skip the 3D unit cell")
    args = ap.parse_args()
    cfg = PRESETS["full" if args.full else "quick"]

    t_start = time.time()

    banner("1. 2D cross-section  (replaces the COMSOL emw baseline)")
    cs = CrossSection(**GEOMETRY)
    t0 = time.time()
    qs = extract(cs, resolution=cfg["res_2d"])
    print(f"  n_m    = {qs.n_m:10.4f}")
    print(f"  Z0     = {qs.Z0:10.3f} ohm")
    print(f"  C      = {qs.C * 1e12:10.3f} pF/m")
    print(f"  L      = {qs.L * 1e9:10.3f} nH/m")
    print(f"  alpha  = {qs.alpha_c:10.3f} dB/cm   (conductor, perturbative)")
    print(f"  [{time.time() - t0:.1f} s]")

    if args.two_d:
        print(f"\nTotal {time.time() - t_start:.1f} s")
        return

    banner("2. 3D unit cell  (replaces the four CST Multilayer runs)")
    from tfln3d import build, penalties

    cell = dict(pitch=PITCH, **GEOMETRY, **STUB,
                lc_gap=cfg["lc_gap"], air_h=cfg["air_h"], si_h=cfg["si_h"],
                n_air=cfg["n_air"], n_si=cfg["n_si"])

    t0 = time.time()
    f_u, n_u, _ = build(etched=False, out="cell_unetched.msh", **cell)
    f_e, n_e, _ = build(etched=True, out="cell_etched.msh", **cell)
    print(f"  meshed: unetched {n_u} nodes, etched {n_e} nodes "
          f"[{time.time() - t0:.1f} s]")

    p = penalties(f_e, f_u, pitch=PITCH)
    print(f"  C_unetched = {p.C_unetched * 1e12:10.3f} pF/m")
    print("     (not expected to equal the 2D value above: the cell uses a")
    print("      uniform LN slab, no ribs/caps and a smaller box.  All of")
    print("      that is common to both cells and cancels in dL and dC.)")
    print(f"  dC         = {p.dC * 1e15:+10.4f} fF per {PITCH:.0f} um cell")
    print(f"  dL         = {p.dL * 1e12:+10.4f} pH per {PITCH:.0f} um cell")
    print(f"  [{p.seconds:.1f} s for four solves]")

    banner("3. Composite synthesis  ->  3D, tee-perturbed kinematics")
    comp = synthesize(qs.n_m, qs.Z0, p.dL, p.dC, pitch_um=PITCH,
                      alpha_2D=qs.alpha_c)
    print(f"  {'':10s} {'2D baseline':>14s} {'3D composite':>14s} {'shift':>10s}")
    print(f"  {'n_m':10s} {comp.n_m_2D:14.4f} {comp.n_m_3D:14.4f} "
          f"{comp.n_m_3D - comp.n_m_2D:+10.4f}")
    print(f"  {'Z0 (ohm)':10s} {comp.Z0_2D:14.3f} {comp.Z0_3D:14.3f} "
          f"{comp.Z0_3D - comp.Z0_2D:+10.3f}")
    print(f"  {'L (nH/m)':10s} {comp.L_2D * 1e9:14.3f} {comp.L_3D * 1e9:14.3f} "
          f"{(comp.L_3D - comp.L_2D) * 1e9:+10.3f}")
    print(f"  {'C (pF/m)':10s} {comp.C_2D * 1e12:14.3f} "
          f"{comp.C_3D * 1e12:14.3f} {(comp.C_3D - comp.C_2D) * 1e12:+10.3f}")
    print("\n  alpha: d_alpha is not implemented yet, so alpha_3D is still")
    print("         the 2D baseline.  See tfln2d/README.md.")

    print(f"\nTotal {time.time() - t_start:.1f} s")


if __name__ == "__main__":
    main()
