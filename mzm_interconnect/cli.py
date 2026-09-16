"""
Headless entry point -- same engine as the GUI, for batch runs and servers.

    python -m mzm_interconnect.cli analyse line.s2p --L_target_mm 8 --Rt_R 40
    python -m mzm_interconnect.cli sweep   line.s2p --param Rt_R --from 10 --to 100 --n 91
    python -m mzm_interconnect.cli sweep   line.s2p --param Rt_R --from 10 --to 100 \
                                           --series L_target_mm --series-from 4 --series-to 12 --series-n 5
    python -m mzm_interconnect.cli export  line.s2p --out_dir ./tables
    python -m mzm_interconnect.cli build   line.s2p --lumapi_path "C:\\Program Files\\..."

Every registry parameter is available as ``--<key> <value>``.
"""

from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import numpy as np

from . import parameters as P
from . import sweep as SW
from .extractor import (DARK, LIGHT, bandwidth_spread, diagnostic_figure, eo_figure,
                        export_lumerical_tables, export_touchstone,
                        extraction_warnings)
from .physics import eo_response, link_metrics


def _add_param_args(ap):
    for spec in P.PARAMS:
        if spec.key == "s2p_path":
            continue
        ap.add_argument(f"--{spec.key}", default=None, help=f"{spec.display} "
                                                            f"(default {spec.default})")


def _params_from_args(args, s2p) -> dict:
    p = P.defaults()
    p["s2p_path"] = s2p
    for spec in P.PARAMS:
        v = getattr(args, spec.key, None)
        if v is not None:
            p[spec.key] = v
    if not str(p["out_dir"]).strip():
        p["out_dir"] = os.path.dirname(os.path.abspath(s2p))
    return P.normalise(p)


def cmd_analyse(args):
    p = _params_from_args(args, args.s2p)
    fit = SW.get_fit(p)
    res = eo_response(fit, p)
    lm = link_metrics(p)
    theme = DARK if args.theme == "dark" else LIGHT

    print(f"file                {fit.source_file}")
    print(f"S-parameter range   {fit.f_min_sim_GHz:.2f} - {fit.f_max_sim_GHz:.2f} GHz")
    print(f"length              {float(p['L_target_mm']):.2f} mm "
          f"(measured {fit.L_meas_m*1e3:.2f} mm)")
    print(f"termination         {float(p['Rt_R']):.1f} ohm, source {float(p['Zs_R']):.1f} ohm")
    print(f"n_g                 {float(p['ng']):.4f}")
    print(f"n_m @ 60 GHz        {float(fit.nm(np.array([60.0]), offset=float(p['nm_offset']))[0]):.4f}")
    a60 = fit.alpha_dB_cm(np.array([60.0]), scale=float(p["alpha_scale"]),
                          skin_scale=float(p["alpha_skin_scale"]),
                          diel_scale=float(p["alpha_diel_scale"]),
                          offset=float(p["alpha_offset_dB_cm"]))[0]
    z60 = complex(fit.Zc(np.array([60.0]), offset=float(p["zc_offset_ohm"]))[0])
    print(f"alpha @ 60 GHz      {float(a60):.3f} dB/cm")
    print(f"Zc @ 60 GHz         {z60.real:.2f}{z60.imag:+.2f}j ohm")
    print("-" * 56)
    if res.norm_window_GHz[1] > res.norm_window_GHz[0]:
        print(f"0 dB reference      mean over {res.norm_window_GHz[0]:.2f}-"
              f"{res.norm_window_GHz[1]:.2f} GHz  (ripple {res.ripple_pp_dB:.2f} dB p-p, "
              f"period {res.ripple_period_GHz:.2f} GHz)")
    else:
        print(f"0 dB reference      single point at {res.norm_window_GHz[0]:.2f} GHz")
    print(f"EO bandwidth        {res.bw_GHz:.2f} GHz"
          + ("  (lower bound: never crossed the criterion)" if res.bw_clipped else ""))
    print(f"EO S21 @ {float(p['f_probe_GHz']):.0f} GHz    {res.s21_at_probe_dB:+.2f} dB")
    print(f"worst S11           {res.s11_worst_dB:.1f} dB")
    print(f"drive configuration {p['drive_config']}")
    print(f"V_pi (device)       {lm.vpi_eff_V:.3f} V   (V_pi.L = {lm.vpi_L_Vcm:.3f} V.cm)")
    print(f"extinction ratio    {lm.er_dB:.1f} dB")
    print(f"chirp parameter     {lm.chirp_alpha:.4f}")

    spread = bandwidth_spread(fit, p)
    if spread:
        print("-" * 56)
        print("Bandwidth across every defensible fit of the same data:")
        for lbl, v in spread["rows"]:
            print(f"  {lbl:46s} {v:7.2f} GHz")
        print(f"  --> {spread['min']:.0f} - {spread['max']:.0f} GHz "
              f"(median {spread['median']:.0f})")
    warns = extraction_warnings(fit, res)
    if warns:
        print("-" * 56)
        for w in warns:
            print(f"  ! {w}")

    if getattr(args, "touchstone", False):
        out = str(p["out_dir"])
        os.makedirs(out, exist_ok=True)
        stem = os.path.splitext(os.path.basename(str(p["s2p_path"])))[0]
        ts = os.path.join(out, f"{stem}_L{float(p['L_target_mm']):g}mm_"
                               f"Rt{float(p['Rt_R']):g}.s2p")
        info = export_touchstone(fit, res, p, ts)
        print(f"\ntouchstone  {ts}  ({info['points']} points, {info['format']}, "
              f"{info['ports']})")

    if args.plot:
        out = str(p["out_dir"])
        os.makedirs(out, exist_ok=True)
        f1 = eo_figure(fit, res, p, theme)
        f1.savefig(os.path.join(out, "eo_response.png"), dpi=180,
                   facecolor=f1.get_facecolor())
        f2 = diagnostic_figure(fit, p, theme)
        f2.savefig(os.path.join(out, "line_diagnostics.png"), dpi=180,
                   facecolor=f2.get_facecolor())
        print(f"\nfigures written to {out}")
    return 0


def cmd_sweep(args):
    p = _params_from_args(args, args.s2p)
    theme = DARK if args.theme == "dark" else LIGHT
    values = SW.make_values(args.start, args.stop, args.n, args.log)

    series_key = series_values = None
    if args.series:
        series_key = args.series
        series_values = SW.make_values(args.series_start, args.series_stop, args.series_n)

    def prog(done, total, msg):
        if done == total or done % max(1, total // 20) == 0:
            pct = 100.0 * done / max(total, 1)
            sys.stderr.write(f"\r  {pct:5.1f}%  {msg}   ")
            sys.stderr.flush()

    r = SW.run_sweep(p, args.param, values, series_key, series_values, progress=prog)
    sys.stderr.write("\n")

    spec = SW.METRIC_BY_KEY[args.metric]
    y = r.metrics[args.metric]
    if series_key is None:
        print(f"{P.BY_KEY[args.param].display:>28} | {spec.display}")
        for xv, yv, cl in zip(r.x_values, y[0], r.clipped[0]):
            print(f"{float(xv):28.4g} | {yv:10.3f}" + ("   (lower bound)" if cl else ""))
    else:
        print(f"{spec.display}: rows = {P.BY_KEY[series_key].label}, "
              f"cols = {P.BY_KEY[args.param].label}")
        head = " " * 12 + "".join(f"{float(v):10.3g}" for v in r.x_values)
        print(head)
        for si, sv in enumerate(series_values):
            print(f"{float(sv):10.3g}  " + "".join(f"{v:10.3f}" for v in y[si]))

    out = str(p["out_dir"])
    os.makedirs(out, exist_ok=True)
    csv_path = os.path.join(out, f"sweep_{args.param}_{args.metric}.csv")
    r.to_csv(csv_path)
    fig = SW.sweep_figure(r, args.metric, theme)
    png_path = os.path.join(out, f"sweep_{args.param}_{args.metric}.png")
    fig.savefig(png_path, dpi=180, facecolor=fig.get_facecolor())
    print(f"\nCSV  {csv_path}\nPNG  {png_path}")
    return 0


def cmd_export(args):
    p = _params_from_args(args, args.s2p)
    fit = SW.get_fit(p)
    res = eo_response(fit, p)
    paths = export_lumerical_tables(fit, p, res, str(p["out_dir"]))
    for k in ("loss", "z0", "nm", "json"):
        print(f"  {paths[k]}")
    print(f"\ntables span 1.0 - {paths['table_f_max_GHz']:.1f} GHz "
          f"({paths['n_points']} points)"
          + ("; extrapolated past the measured range" if paths["extrapolated"] else ""))
    return 0


def cmd_build(args):
    from .interconnect import InterconnectBuilder
    p = _params_from_args(args, args.s2p)
    fit = SW.get_fit(p)
    res = eo_response(fit, p)
    out = str(p["out_dir"])
    files = export_lumerical_tables(fit, p, res, out)
    b = InterconnectBuilder(str(p["lumapi_path"]), hide=bool(p["ic_hide"]))
    topo = b.build(p, files)
    print(f"topology: {topo}")
    b.run(os.path.join(out, "TWMZM_EO_response.icp"))
    f_GHz, s_dB, bw = b.ena_trace(p)
    print(f"Python {res.bw_GHz:.2f} GHz | INTERCONNECT {bw:.2f} GHz | "
          f"difference {abs(res.bw_GHz-bw):.2f} GHz")
    fig = eo_figure(fit, res, p, DARK if args.theme == "dark" else LIGHT,
                    lumerical=(f_GHz, s_dB, bw))
    png = os.path.join(out, "EO_crosscheck.png")
    fig.savefig(png, dpi=180, facecolor=fig.get_facecolor())
    print(f"overlay written to {png}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mzm_interconnect",
                                description="Traveling-wave MZM modelling toolkit")
    ap.add_argument("--theme", choices=("dark", "light"), default="light")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyse", help="fit one .s2p and report the EO figures")
    a.add_argument("s2p")
    a.add_argument("--plot", action="store_true")
    a.add_argument("--touchstone", action="store_true",
                   help="also write the S11 and EO S21 traces as a Touchstone file")
    _add_param_args(a)
    a.set_defaults(func=cmd_analyse)

    s = sub.add_parser("sweep", help="sweep one parameter and plot a metric")
    s.add_argument("s2p")
    s.add_argument("--param", required=True,
                   choices=[p.key for p in P.SWEEPABLE])
    s.add_argument("--from", dest="start", type=float, required=True)
    s.add_argument("--to", dest="stop", type=float, required=True)
    s.add_argument("--n", type=int, default=41)
    s.add_argument("--log", action="store_true")
    s.add_argument("--metric", default="bw_GHz", choices=[m.key for m in SW.METRICS])
    s.add_argument("--series", default=None, choices=[p.key for p in P.SWEEPABLE])
    s.add_argument("--series-from", dest="series_start", type=float, default=0.0)
    s.add_argument("--series-to", dest="series_stop", type=float, default=1.0)
    s.add_argument("--series-n", dest="series_n", type=int, default=5)
    _add_param_args(s)
    s.set_defaults(func=cmd_sweep)

    e = sub.add_parser("export", help="write loss/z0/nm tables + sim_params.json")
    e.add_argument("s2p")
    _add_param_args(e)
    e.set_defaults(func=cmd_export)

    b = sub.add_parser("build", help="export, build and run the INTERCONNECT schematic")
    b.add_argument("s2p")
    _add_param_args(b)
    b.set_defaults(func=cmd_build)

    g = sub.add_parser("gui", help="launch the graphical interface")
    g.add_argument("s2p", nargs="?", default="")
    _add_param_args(g)
    g.set_defaults(func=lambda args: (__import__("mzm_interconnect.gui", fromlist=["launch"])
                                      .launch(_params_from_args(args, args.s2p) if args.s2p
                                              else None, theme="dark"), 0)[1])

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
