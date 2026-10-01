"""
Step 0 for the scripted "TL line" element: is it the same electrode as the
Ansys Traveling Wave Electrode (TW) block?

Step 0 runs as a ladder of small simulations, each in a fresh INTERCONNECT
session and each saved BEFORE it runs, so that a crash names its cause and
leaves a project you can open and run by hand to read INTERCONNECT's own
message in its Output window:

  S1  Ansys TW block alone (baseline; this build is known to run)
  S2  TL line as a plain 2-port: ENA -> SRC(Zs) -> TL -> ENA
      (tests setsparameter on bidirectional electrical ports, reflections)
  S3  TL line with its modulation output, short table (about 50 points)
  S4  TL line with its modulation output, full table, both cases
  S5  S4 inside a Compound with scattering data analysis on; a second
      Compound reads the element's far-end output instead (CMP_FE)

Source and termination are scripted elements (source_setup.lsf,
termination_setup.lsf) on the lines' reference R0. The Electrical Connector is
not used: the third Step 0 run showed that a (Zs | R0) connector reflects with
the opposite sign, i.e. behaves as a source of R0^2/Zs (and a (R0 | Rt)
connector with a free port as a load of R0^2/Rt).

Only the Compound row can pass on a mismatched line: outside a Compound every
pass through an element's filter adds its latency, so reflections come back
late. If the script cannot draw the wire inside the Compound, S5 is saved but
not run; draw that wire by hand, save the project, and run_saved_stages() runs
it and adds its rows to the same report.

Every row is driven by its own Network Analyzer (impulse response) and
measured electrically -- no optics, so nothing else can differ:

  REF   ENA -> TW (same loss/z0/nm tables, Zs and Rt inside) -> ENA
  FLAT  ENA -> SRC(Zs) -> TL line -> LOAD(Rt)      modulation -> ENA
  CMP   the FLAT row inside a Compound
  CMP_FE  the same Compound, analyser on the TL line's 'far end' output
          (the voltage across the termination), compared with the model's V(L)

Cases: the GUI's Zs/Rt, and a deliberately mismatched 30/80 ohm pair.

The report says which stages ran, then compares every measured row with the
Python model and with the TW block, in numbers: overall complex scale (it
carries the conventions), max |dB| and max phase difference after removing
it, mean group-delay difference, and both bandwidths. It also says which phase
reference the TW block's output uses.

Nothing here imports lumapi unless run_step0() is called.
"""

from __future__ import annotations

import csv
import os
import traceback
from typing import Callable, Optional

import numpy as np

from . import parameters as P
from . import scripted_line as SL
from .interconnect import InterconnectBuilder, P_IN, P_IN1, P_OUT
from .tl_schematic import (LOAD_LSF, SETUP_LSF, SOURCE_LSF,  # noqa: F401
                           ScriptedElementUnavailable, first_line, fwd)

FIR_TAPS = 1024        # the same for the TW block and the TL line, so neither is favoured

P_PORT1 = ['port 1']
P_PORT2 = ['port 2']
P_TL1 = ['port 1']
P_TL2 = ['port 2']
P_TLMOD = ['modulation']

# Table densities: the full table resolves the phase of a 20 mm line to well
# under a radian per point; the short one only has to be a valid table.
FULL_POINTS_PER_GHZ = 4.0
SHORT_POINTS_PER_GHZ = 0.25

STAGES = [
    ("S1", "Ansys TW block alone (baseline)",
     [dict(kind="REF", cases="all")]),
    ("S2", "TL line as a plain 2-port, short table",
     [dict(kind="TL2P", table="short", cases="gui")]),
    ("S3", "TL line with modulation output, short table",
     [dict(kind="TL", table="short", cases="gui", label="FLAT_SHORT")]),
    ("S4", "TL line with modulation output, full table",
     [dict(kind="TL", table="full", cases="all", label="FLAT")]),
    ("S5", "S4 inside a Compound (modulation and far-end outputs)",
     [dict(kind="TL", table="full", cases="all", label="CMP", compound=True),
      dict(kind="TL", table="full", cases="all", label="CMP_FE", compound=True,
           output="far end")]),
]

STAGE_MEANING = {
    "S1": "the baseline itself failed: the problem is in the session or the "
          "Network Analyzer setup, not in the TL line",
    "S2": "the scripted element's S-matrix on bidirectional electrical ports is "
          "the problem (setsparameter on electrical ports, or its reflection entries)",
    "S3": "the 2-port works but the modulation output does not: an Output port "
          "driven from bidirectional ports is the problem",
    "S4": "the element works with a short table but not the full one: table size "
          "or FIR design",
    "S5": "the element works on its own but not inside a Compound: either a wire "
          "inside the Compound is wrong (check that the TL line's modulation output "
          "goes only to the relay 'External Port = modulation') or the Compound's "
          "S-parameter solver refuses the scripted element",
}


def step0_cases(p: dict) -> list:
    return [dict(name="gui", Zs=float(p["Zs_R"]), Rt=float(p["Rt_R"])),
            dict(name="mismatch", Zs=30.0, Rt=80.0)]


_fwd, _first_line = fwd, first_line


class Step0Builder(InterconnectBuilder):
    """One Step 0 stage. Reuses the main builder's element helpers (the TL
    elements and Compounds come from tl_schematic.TLElementsMixin)."""

    # ---- elements ------------------------------------------------------
    def _ena(self, name: str, x: int, y: int, p: dict):
        # Same settings as the validated main build.
        self.add(['Network Analyzer'], name, x, y)
        self.setp(name, ['analysis type'], 'impulse response')
        self.setp(name, ['signal source', 'source'], 'internal', required=False)
        self.setp(name, ['source kind', 'kind'], 'power', required=False)
        self.setp(name, ['power', 'source power'], 0.001, required=False)
        self.setp(name, ['input parameter'], 'start and stop', required=False)
        self.setp(name, ['start frequency'], 0, required=False)
        self.setp(name, ['stop frequency'], float(p["f_max_GHz"]) * 1e9, required=False)
        self.setp(name, ['number of points', 'number of frequency points'],
                  int(p["ic_ena_points"]), required=False)
        self.setp(name, ['remove dc', 'remove DC'], True, required=False)
        self.setp(name, ['peak analysis', 'peak_analysis'], 'disable', required=False)

    def _fix_tw_filter(self, el):
        """Give the TW block the same FIR length as the TL line. Its default
        filter can be shorter than one round trip of the line (2 n L / c), and
        then it cannot reproduce the reflections at all."""
        self.setp(el, ['digital filter type'], 'FIR', required=False)
        self.setp(el, ['number of taps estimation'], 'disabled', required=False)
        self.setp(el, ['number of fir taps'], FIR_TAPS, required=False)
        self.setp(el, ['maximum number of fir taps'], max(4096, FIR_TAPS), required=False)

    def _make_compound(self, name: str, members: list, out_from=None, out_to=None,
                       pname: str = "modulation") -> bool:
        """One Compound with one output, wired to an analyser's 'input 1'
        (see TLElementsMixin.make_compound)."""
        outs = [(out_from[0], out_from[1], pname, out_to, P_IN1)] if out_from else []
        return self.make_compound(name, members, outs)

    # ---- one stage -------------------------------------------------------
    def build_stage(self, p: dict, files: dict, tables: dict, L: float, rows: list,
                    library_name: Optional[str] = None) -> list:
        """Returns [(case, label, ENA name)] for every row that was built."""
        sim = self.sim
        sim.new()
        sim.switchtodesign()
        sim.deleteall()
        self._wiring = []
        self._pos = {}
        self.pending_manual = []
        sim.set("sample rate", float(p["ic_sample_rate_GHz"]) * 1e9)
        ng = float(p["ng"])
        built, y = [], 0
        for spec in rows:
            cases = step0_cases(p) if spec["cases"] == "all" else step0_cases(p)[:1]
            for i, case in enumerate(cases, start=1):
                pc = dict(p, Zs_R=case["Zs"], Rt_R=case["Rt"], Zs_L_pH=0.0, Zs_C_fF=0.0,
                          Rt_L_pH=0.0, Rt_C_fF=0.0, L_target_mm=L * 1e3)
                kind = spec["kind"]
                label = spec.get("label", "REF" if kind == "REF" else "2PORT")
                ena = f"ENA_{label}_{i}"
                self._ena(ena, 0, y, pc)
                if kind == "REF":
                    tw = f"TW_REF_{i}"
                    self._add_tw(tw, pc, files, ng, 260, y, length_m=L)
                    self._fix_tw_filter(tw)
                    self.connect(ena, P_OUT, tw, P_IN)
                    self.connect(tw, P_OUT, ena, P_IN1)
                elif kind == "TL2P":
                    cs, tl = f"SRC_{label}_{i}", f"TL_{label}_{i}"
                    self.make_source(cs, 200, y, case["Zs"])
                    self.make_tl(tl, 340, y, tables[spec["table"]], L, ng, modulating=False,
                                 library_name=library_name, fir_taps=FIR_TAPS)
                    self.connect(ena, P_OUT, cs, P_PORT1)
                    self.connect(cs, P_PORT2, tl, P_TL1)
                    self.connect(tl, P_TL2, ena, P_IN1)
                else:
                    cs, tl, ct = f"SRC_{label}_{i}", f"TL_{label}_{i}", f"LOAD_{label}_{i}"
                    out = spec.get("output", "modulation")
                    self.make_source(cs, 200, y, case["Zs"])
                    # one output per row, so no output is left dangling in a Compound
                    self.make_tl(tl, 340, y, tables[spec["table"]], L, ng,
                                 modulating=(out == "modulation"),
                                 far_end=(out == "far end"), library_name=library_name)
                    self.make_load(ct, 480, y, case["Rt"])
                    self.connect(ena, P_OUT, cs, P_PORT1)
                    self.connect(cs, P_PORT2, tl, P_TL1)
                    self.connect(tl, P_TL2, ct, P_PORT1)
                    if not spec.get("compound"):
                        self.connect(tl, P_TLMOD if out == "modulation" else [out], ena, P_IN1)
                    elif not self._make_compound(f"LINE_{label}_{i}", [cs, tl, ct],
                                                 out_from=(tl, out), out_to=ena, pname=out):
                        raise RuntimeError(f"the Compound for {tl} could not be made")
                built.append((case["name"], label, ena))
                y += 150
        return built

    # ---- read back -----------------------------------------------------
    def raw_trace(self, element: str):
        return self.complex_trace(element)


# ---------------------------------------------------------------------------
def python_predictions(fit, p: dict, out_dir: str, L: float) -> dict:
    """
    Write the element tables (full and short, up to the simulation's Nyquist
    frequency) and return the model responses per case, as INTERCONNECT should
    see them: modulation output with both phase references, and the 2-port's
    transmitted voltage into a matched receiver.
    """
    top = 0.5 * float(p["ic_sample_rate_GHz"])
    pp = dict(p, n_bends=0, L_target_mm=L * 1e3)
    tables, pred = {}, {"cases": {}, "short": {}, "2port": {}}
    for key, dens in (("full", FULL_POINTS_PER_GHZ), ("short", SHORT_POINTS_PER_GHZ)):
        d = out_dir if key == "full" else os.path.join(out_dir, "short_table")
        tables[key] = SL.export_tl_tables(fit, pp, d, f_top_GHz=top,
                                          points_per_GHz=dens)["electrode"]
    ng = float(p["ng"])
    R0 = Step0Builder.R0
    for key in ("full", "short"):
        el = SL.tl_sparams_from_table(tables[key], L, ng, R0)
        w = 2 * np.pi * el["f_Hz"]
        for case in step0_cases(p):
            r = SL.chain_response([el], case["Zs"], case["Rt"], R0)
            entry = r.H * np.exp(1j * w * ng * L / SL.C0)
            d = dict(f_GHz=el["f_Hz"] / 1e9, exit=r.H, entry=entry, far=r.far_end[0],
                     Zs=case["Zs"], Rt=case["Rt"])
            (pred["cases"] if key == "full" else pred["short"])[case["name"]] = d
    el2 = SL.tl_sparams_from_table(tables["short"], L, None, R0, modulating=False)
    case = step0_cases(p)[0]
    r2 = SL.chain_response([el2], case["Zs"], R0, R0)        # ENA input taken as matched
    pred["2port"][case["name"]] = dict(f_GHz=el2["f_Hz"] / 1e9, exit=r2.far_end[0],
                                       Zs=case["Zs"], Rt=R0)
    pred["tables"] = tables
    pred["table_top_GHz"] = top
    return pred


def _row_line(A, cname, what, c_ref, meas_row, band, convention=None):
    f, H, cplx, label = meas_row
    cmp = SL.compare_traces(c_ref["f_GHz"], c_ref["exit"], f, H, band, convention=convention)
    ph = f"{cmp['max_deg']:8.3f}" if cplx else "     n/a"
    lat = f"{cmp['latency_ps']:9.2f}" if cplx else "      n/a"
    conv = cmp["convention"][:4] if cplx else "n/a"
    A(f"{cname:9s} {what:30s} {cmp['scale_abs']:8.4f} {conv:>5s} {lat} {cmp['max_dB']:8.4f} "
      f"{ph} {cmp['bw_ref_GHz']:8.2f} {cmp['bw_test_GHz']:8.2f}")
    return cmp


def format_report(pred: dict, meas: dict, stages: list, band, fs_GHz: float) -> str:
    """meas[(case, label)] = (f_GHz, H, is_complex, dataset label);
    stages = [(id, title, status, detail)]."""
    L = []
    A = L.append
    A("STEP 0 -- scripted TL line element vs Ansys TW block")
    A("")
    A("Stages (each in its own INTERCONNECT session, project saved before the run):")
    first_fail = None
    for sid, title, status, detail in stages:
        A(f"  {sid}  {status:7s} {title}" + (f"\n        {detail}" if detail else ""))
        if status == "FAILED" and first_fail is None and sid != "S1":
            first_fail = sid
    for sid, _t, status, _d in stages:
        if status == "SAVED":
            A(f"  -> {sid} was saved but not run: draw the wire named above, save the project, "
              f"then press 'Step 0: run wired S5' (CLI: tl-step0-saved).")
    if not any(lb in ("CMP", "CMP_CNC") for (_c, lb) in meas):
        A("  -> No Compound row (CMP) yet. It is the row that decides Step 0; "
          "the FLAT rows cannot pass on a mismatched line.")
    if first_fail:
        A(f"  -> first failing stage {first_fail}: {STAGE_MEANING[first_fail]}.")
        A(f"     Open TL_step0_{first_fail}.icp, press Run, and copy the message in "
          f"INTERCONNECT's Output window.")
    A("")
    A("How to read the table")
    A("  scale    |INTERCONNECT / reference| at 0.5-3 GHz. Against the model it includes the")
    A("           Network Analyzer's own factor (the same for every row); the number that")
    A("           says something about the element is the TL / TW ratio ('vs REF' rows): 1.")
    A("  conv     phase convention of the INTERCONNECT data: 'phys' = exp(-i w t), so the")
    A("           data were conjugated before comparing.")
    A("  latency  pure delay added by INTERCONNECT's digital filters, fitted and removed.")
    A(f"           One sample is {1e3 / fs_GHz:.3f} ps; half a {FIR_TAPS}-tap filter is "
      f"{FIR_TAPS / 2 * 1e3 / fs_GHz:.1f} ps.")
    A("  max dB, max deg   what is left after removing scale and latency")
    A(f"band {band[0]:g}-{band[1]:g} GHz; element tables up to {pred['table_top_GHz']:.1f} GHz "
      f"(the Nyquist frequency of this run)")
    A("")
    # The phase convention is a property of INTERCONNECT, not of a row: take it
    # from the cleanest comparison (the plain 2-port, then the short-table row)
    # and impose it on every model comparison.
    conv = None
    for key, pr in (("2PORT", "2port"), ("FLAT_SHORT", "short")):
        k = next(((cn, lb) for (cn, lb) in meas if lb == key), None)
        if k and meas[k][2]:
            conv = SL.compare_traces(pred[pr][k[0]]["f_GHz"], pred[pr][k[0]]["exit"],
                                     meas[k][0], meas[k][1], band)["convention"]
            A(f"INTERCONNECT phase convention, from the {key} row: {conv} "
              f"(applied to every row below)")
            A("")
            break
    hdr = (f"{'case':9s} {'what':30s} {'scale':>8s} {'conv':>5s} {'latency ps':>9s} "
           f"{'max dB':>8s} {'max deg':>8s} {'BW ref':>8s} {'BW test':>8s}")
    tl_rows = ("FLAT", "CMP", "CMP_CNC")
    for cname, c in pred["cases"].items():
        A(f"== case '{cname}': Zs = {c['Zs']:g} ohm, Rt = {c['Rt']:g} ohm")
        A(hdr)
        if (cname, "REF") in meas:
            _row_line(A, cname, "REF (Ansys TW) vs model", c, meas[(cname, "REF")], band, conv)
        if (cname, "2PORT") in meas:
            _row_line(A, cname, "2PORT far end vs model", pred["2port"][cname],
                      meas[(cname, "2PORT")], band, conv)
        if (cname, "FLAT_SHORT") in meas:
            _row_line(A, cname, "FLAT short table vs model", pred["short"][cname],
                      meas[(cname, "FLAT_SHORT")], band, conv)
        for lab in tl_rows:
            if (cname, lab) in meas:
                _row_line(A, cname, f"{lab} vs model", c, meas[(cname, lab)], band, conv)
        if (cname, "CMP_FE") in meas:
            _row_line(A, cname, "CMP_FE far end vs model V(L)",
                      dict(f_GHz=c["f_GHz"], exit=c["far"]), meas[(cname, "CMP_FE")], band, conv)
        if (cname, "REF") in meas:
            fR, HR, cR, lR = meas[(cname, "REF")]
            ref = dict(f_GHz=fR, exit=HR)
            for lab in tl_rows:
                if (cname, lab) in meas:
                    _row_line(A, cname, f"{lab} vs REF (IC only)", ref,
                              meas[(cname, lab)], band, "engineering" if conv else None)
        A("")
    A("Pass: the CMP row within ~0.05 dB and ~1 deg of REF and of the model up to the top "
      "of the band, the same bandwidth to ~0.1 GHz, and a TL / TW scale of 1.")
    A("A FLAT row (outside a Compound) with a large latency cannot be right when the line "
      "is mismatched: the latency is added on every round trip of the reflections.")
    return "\n".join(L)


def run_step0(fit, p: dict, out_dir: Optional[str] = None,
              library_name: Optional[str] = None, compound: bool = True,
              log: Optional[Callable[[str], None]] = None, keep_open: bool = False,
              stages: Optional[list] = None):
    """
    Export, then run the stages one by one, each in a fresh INTERCONNECT
    session saved before it runs. A failing stage is recorded and the next one
    still runs (a Compound can work where the flat row does not). Returns
    (report text, None); the report is also written to step0_report.txt.
    """
    from .extractor import export_lumerical_tables
    from .physics import device_response
    log = log or print
    p = _step0_params(p, log)
    out_dir = out_dir or os.path.join(str(p["out_dir"]) or ".", "tl_step0")
    os.makedirs(out_dir, exist_ok=True)
    L = float(p["L_target_mm"]) * 1e-3
    library_name = library_name if library_name is not None else (
        str(p.get("tl_library_name", "")).strip() or None)
    res = device_response(fit, p)
    files = export_lumerical_tables(fit, p, res, out_dir)
    pred = python_predictions(fit, p, out_dir, L)
    log(f"  Tables in {out_dir}: loss/z0/nm.txt for the TW block; electrode_line.txt "
        f"({FULL_POINTS_PER_GHZ:g}/GHz) and short_table/electrode_line.txt for the TL "
        f"line, up to {pred['table_top_GHz']:.1f} GHz.")

    todo = [s for s in STAGES if (stages is None or s[0] in stages)
            and (compound or s[0] != "S5")]
    meas, status = {}, []
    for sid, title, rows in todo:
        log(f"  --- {sid}: {title}")
        b = None
        try:
            b = Step0Builder(str(p["lumapi_path"]), hide=bool(p["ic_hide"]), log=log)
            built = b.build_stage(p, files, pred["tables"], L, rows, library_name)
            icp = os.path.join(out_dir, f"TL_step0_{sid}.icp")
            b.sim.save(icp)
            if b.pending_manual:
                msg = "; ".join(b.pending_manual)
                status.append((sid, title, "SAVED", "not run -- one wire must be drawn by "
                                                    "hand: " + msg))
                log(f"  {sid}: saved {icp}, not run: {msg}")
                continue
            log(f"  {sid}: saved {icp}; running...")
            b.sim.run()
            got = 0
            for cname, label, ena in built:
                try:
                    meas[(cname, label)] = b.raw_trace(ena)
                    got += 1
                except Exception as exc:
                    log(f"  {ena}: {exc}")
            status.append((sid, title, "ran", f"{got}/{len(built)} analysers read"))
            log(f"  {sid}: ran.")
        except ScriptedElementUnavailable:
            raise
        except Exception as exc:
            msg = f"{type(exc).__name__}: {str(exc).strip()}"
            status.append((sid, title, "FAILED", msg))
            log(f"  {sid}: FAILED -- {msg}")
            log("  " + traceback.format_exc().strip().splitlines()[-1])
        finally:
            if b is not None:
                try:
                    b.close()
                except Exception:
                    pass

    band = (1.0, 0.95 * float(p["f_max_GHz"]))
    rep = format_report(pred, meas, status, band, float(p["ic_sample_rate_GHz"]))
    with open(os.path.join(out_dir, "step0_report.txt"), "w") as fh:
        fh.write(rep + "\n")
    _write_traces(out_dir, meas)
    log(rep)
    return rep, None


def report_from_csv(fit, p: dict, out_dir: str, stages: Optional[list] = None) -> str:
    """Rebuild the Step 0 report from a saved step0_traces.csv, with the current
    comparison rules, without running INTERCONNECT. *p* must hold the same
    parameters as the run (sim_params.json in the same folder has them)."""
    p = _step0_params(p)
    L = float(p["L_target_mm"]) * 1e-3
    pred = python_predictions(fit, p, os.path.join(out_dir, "reanalysis"), L)
    meas = _read_traces(out_dir)
    band = (1.0, 0.95 * float(p["f_max_GHz"]))
    stages = stages or [("csv", "re-read from step0_traces.csv", "ran", f"{len(meas)} traces")]
    return format_report(pred, meas, stages, band, float(p["ic_sample_rate_GHz"]))


def _step0_params(p: dict, log: Optional[Callable[[str], None]] = None) -> dict:
    """The parameters every Step 0 stage uses: no bends, and a sample rate of at
    least 2.5x the sweep ceiling."""
    p = P.normalise(dict(p, n_bends=0))
    fs_needed = 2.5 * float(p["f_max_GHz"])
    if float(p["ic_sample_rate_GHz"]) < fs_needed:
        if log:
            log(f"  Sample rate raised from {float(p['ic_sample_rate_GHz']):.0f} to "
                f"{fs_needed:.0f} GHz for a {float(p['f_max_GHz']):.0f} GHz sweep.")
        p["ic_sample_rate_GHz"] = fs_needed
    return p


def _read_traces(out_dir: str) -> dict:
    path = os.path.join(out_dir, "step0_traces.csv")
    rows = {}
    if os.path.exists(path):
        with open(path, newline="") as fh:
            for r in csv.DictReader(fh):
                rows.setdefault((r["case"], r["row"]), []).append(
                    (float(r["f_GHz"]), complex(float(r["re"]), float(r["im"]))))
    return {k: (np.array([a for a, _ in v]), np.array([b for _, b in v]),
                bool(np.any(np.imag([b for _, b in v]))), "from csv")
            for k, v in rows.items()}


def _write_traces(out_dir: str, meas: dict) -> None:
    with open(os.path.join(out_dir, "step0_traces.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["case", "row", "f_GHz", "re", "im"])
        for (cname, row), (f, H, _c, _l) in meas.items():
            for fi, hi in zip(f, H):
                wr.writerow([cname, row, f"{fi:.6f}", f"{hi.real:.9e}", f"{hi.imag:.9e}"])


# Stages that may need a wire drawn by hand, and the row label of their analysers.
SAVED_STAGE_ROWS = {"S5": ("CMP", "CMP_FE")}


def run_saved_stages(fit, p: dict, out_dir: str, stages=("S5",),
                     log: Optional[Callable[[str], None]] = None) -> str:
    """
    Run the Compound stages from their saved projects, after the missing wire
    has been drawn by hand and the project saved (TL_step0_S5.icp).

    Each project is opened in a fresh INTERCONNECT session and run; its
    analysers are read, added to step0_traces.csv next to the earlier rows, and
    step0_report.txt is rewritten with every row. *p* must be the parameters of
    the Step 0 run that saved the projects (sim_params.json has them): the model
    rows are recomputed from it.
    """
    log = log or print
    p = _step0_params(p)
    meas = _read_traces(out_dir)
    n_old = len(meas)
    titles = {sid: title for sid, title, _r in STAGES}
    status = [("S1-S4", "earlier run, re-read from step0_traces.csv", "ran",
               f"{n_old} traces")]
    for sid in stages:
        icp = os.path.join(out_dir, f"TL_step0_{sid}.icp")
        labels = SAVED_STAGE_ROWS[sid]
        if not os.path.exists(icp):
            status.append((sid, titles[sid], "MISSING", f"{icp} not found"))
            continue
        log(f"  --- {sid}: running {icp}")
        b = None
        try:
            b = Step0Builder(str(p["lumapi_path"]), hide=bool(p["ic_hide"]), log=log)
            b.sim.load(_fwd(icp))
            b.sim.run()
            got, empty = 0, []
            for (i, case), label in ((ic, lb) for lb in labels
                                     for ic in enumerate(step0_cases(p), start=1)):
                ena = f"ENA_{label}_{i}"
                try:
                    tr = b.raw_trace(ena)
                except Exception as exc:
                    log(f"  {ena}: {_first_line(exc)}")
                    empty.append(ena)
                    continue
                f, H = tr[0], tr[1]
                if not np.any(np.abs(H[f > 0.5]) > 1e-9):
                    log(f"  {ena}: no signal -- the wire inside LINE_{label}_{i} is not drawn")
                    empty.append(ena)
                    continue
                meas[(case["name"], label)] = tr
                got += 1
            detail = (f"{got}/{len(labels) * len(step0_cases(p))} analysers read "
                      f"(project wired by hand)")
            if empty:
                detail += f"; no data from {', '.join(empty)}"
            status.append((sid, titles[sid], "ran" if got else "FAILED", detail))
        except Exception as exc:
            status.append((sid, titles[sid], "FAILED", f"{type(exc).__name__}: {_first_line(exc)}"))
            log(f"  {sid}: FAILED -- {_first_line(exc)}")
        finally:
            if b is not None:
                b.close()
    _write_traces(out_dir, meas)
    rep = report_from_csv(fit, p, out_dir, stages=status)
    with open(os.path.join(out_dir, "step0_report.txt"), "w") as fh:
        fh.write(rep + "\n")
    log(rep)
    return rep
