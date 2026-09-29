"""
Step 0 for the scripted "TL line" element: is it the same electrode as the
Ansys Traveling Wave Electrode (TW) block?

Step 0 runs as a ladder of small simulations, each in a fresh INTERCONNECT
session and each saved BEFORE it runs, so that a crash names its cause and
leaves a project you can open and run by hand to read INTERCONNECT's own
message in its Output window:

  S1  Ansys TW block alone (baseline; this build is known to run)
  S2  TL line as a plain 2-port: ENA -> CNC(Zs|R0) -> TL -> ENA
      (tests setsparameter on bidirectional electrical ports, reflections)
  S3  TL line with its modulation output, short table (about 50 points)
  S4  TL line with its modulation output, full table, both cases
  S5  S4 inside a Compound with scattering data analysis on

Every row is driven by its own Network Analyzer (impulse response) and
measured electrically -- no optics, so nothing else can differ:

  REF   ENA -> TW (same loss/z0/nm tables, Zs and Rt inside) -> ENA
  FLAT  ENA -> CNC(Zs|R0) -> TL line -> CNC(R0|Rt)      modulation -> ENA
  CMP   the FLAT row inside a Compound

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

LSF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lumerical")
SETUP_LSF = os.path.join(LSF_DIR, "tl_element_setup.lsf")

P_CNC1 = ['port 1']
P_CNC2 = ['port 2']
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
    ("S5", "S4 inside a Compound with scattering data analysis",
     [dict(kind="TL", table="full", cases="all", label="CMP", compound=True)]),
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
    "S5": "the element works on its own but not inside a Compound: the S-parameter "
          "solver of the Compound is the problem",
}


class ScriptedElementUnavailable(RuntimeError):
    """The scripted element could not be created or configured from Python."""


def step0_cases(p: dict) -> list:
    return [dict(name="gui", Zs=float(p["Zs_R"]), Rt=float(p["Rt_R"])),
            dict(name="mismatch", Zs=30.0, Rt=80.0)]


def _fwd(path: str) -> str:
    """Forward slashes: Lumerical script reads them on every platform."""
    return path.replace("\\", "/")


class Step0Builder(InterconnectBuilder):
    """One Step 0 stage. Reuses the main builder's element helpers."""

    R0 = 50.0

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

    def _cnc(self, name: str, x: int, y: int, z1: float, z2: float):
        self.add(['Electrical Connector'], name, x, y)
        self.setp(name, ['impedance 1'], float(z1))
        self.setp(name, ['impedance 2'], float(z2))

    def make_tl(self, name: str, x: int, y: int, table: str, L: float, ng: float,
                modulating: bool = True, far_end: bool = False,
                library_name: Optional[str] = None, fir_taps: int = 1024):
        """
        One TL line element. With *library_name* it is taken from the Custom
        library (create it once with create_tl_element.lsf); otherwise an empty
        scripted element is created and configured here.
        """
        table = _fwd(table)
        if library_name:
            self.add([library_name], name, x, y)
        else:
            try:
                self.add(['Scripted Element', 'scripted element', 'Scripted element'],
                         name, x, y)
            except Exception as exc:
                raise ScriptedElementUnavailable(
                    "This INTERCONNECT does not let a script create an empty scripted "
                    "element. Create one by hand (right-click > Create scripted "
                    "element), run lumerical/create_tl_element.lsf on it, add it to "
                    "the Custom library, and give its library name here.") from exc
            s = self.sim
            s.addproperty(name, "line_length", "TL line", "Number", 0, 1, "FixedUnit", "m", L)
            s.addproperty(name, "ng", "TL line", "Number", 0, 100, "FixedUnit", "-", ng)
            s.addproperty(name, "R0", "TL line", "Number", 1, 10000, "FixedUnit", "ohm", self.R0)
            s.addproperty(name, "table_file", "TL line", "FileOpen", 0, 0, "NonQuantity", "", table)
            s.addproperty(name, "modulating", "TL line", "Logical", 0, 0, "NonQuantity", "",
                          int(modulating))
            s.addproperty(name, "far_end_output", "TL line", "Logical", 0, 0, "NonQuantity", "",
                          int(far_end))
            s.addproperty(name, "wave_convention", "TL line", "ComboChoice", 0, 0,
                          "NonQuantity", "", "voltage;power")
            s.addproperty(name, "fir_taps", "TL line", "Number", 0, 100000, "FixedUnit", "-",
                          int(fir_taps))
            s.addport(name, "port 1", "Bidirectional", "Electrical Signal", "Left", 0.5)
            s.addport(name, "port 2", "Bidirectional", "Electrical Signal", "Right", 0.5)
            if modulating:
                s.addport(name, "modulation", "Output", "Electrical Signal", "Top", 0.5)
            if far_end:
                s.addport(name, "far end", "Output", "Electrical Signal", "Bottom", 0.5)
            with open(SETUP_LSF, encoding="utf-8") as fh:
                code = fh.read()
            if not self.setp(name, ['setup script', 'setup', 'script setup'], code,
                             required=False):
                raise ScriptedElementUnavailable(
                    f"{name}: the setup script could not be set from Python. Paste "
                    f"lumerical/tl_element_setup.lsf into Edit > Scripts > Setup of one "
                    f"element, add it to the Custom library, and give its library name.")
        for prop, val in (("line_length", float(L)), ("ng", float(ng)),
                          ("R0", self.R0), ("table_file", table),
                          ("modulating", int(modulating)), ("far_end_output", int(far_end)),
                          ("wave_convention", "voltage"), ("fir_taps", int(fir_taps))):
            self.setp(name, [prop], val)

    def _make_compound(self, name: str, members: list) -> bool:
        """Group already-wired elements into a Compound and turn its S-parameter
        solver on. The Compound keeps the external connections as its ports."""
        try:
            self.sim.select(members[0])
            for m in members[1:]:
                self.sim.shiftselect(m)
            self.sim.createcompound()
        except Exception as exc:
            self.log(f"  createcompound failed: {exc}")
            return False
        for cand in ("COMPOUND_1", "Compound Element", "COMPOUND"):
            try:
                self.sim.setnamed(cand, "name", name)
                break
            except Exception:
                continue
        ok = self.setp(name, ['scattering data analysis'], True, required=False)
        if not ok:
            self.log(f"  {name}: could not switch 'scattering data analysis' on.")
        return ok

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
                    self.connect(ena, P_OUT, tw, P_IN)
                    self.connect(tw, P_OUT, ena, P_IN1)
                elif kind == "TL2P":
                    cs, tl = f"CNCS_{label}_{i}", f"TL_{label}_{i}"
                    self._cnc(cs, 200, y, case["Zs"], self.R0)
                    self.make_tl(tl, 340, y, tables[spec["table"]], L, ng, modulating=False,
                                 library_name=library_name)
                    self.connect(ena, P_OUT, cs, P_CNC1)
                    self.connect(cs, P_CNC2, tl, P_TL1)
                    self.connect(tl, P_TL2, ena, P_IN1)
                else:
                    cs, tl, ct = f"CNCS_{label}_{i}", f"TL_{label}_{i}", f"CNCT_{label}_{i}"
                    self._cnc(cs, 200, y, case["Zs"], self.R0)
                    self.make_tl(tl, 340, y, tables[spec["table"]], L, ng,
                                 library_name=library_name)
                    self._cnc(ct, 480, y, self.R0, case["Rt"])
                    self.connect(ena, P_OUT, cs, P_CNC1)
                    self.connect(cs, P_CNC2, tl, P_TL1)
                    self.connect(tl, P_TL2, ct, P_CNC1)
                    self.connect(tl, P_TLMOD, ena, P_IN1)
                    if spec.get("compound") and not self._make_compound(
                            f"LINE_{label}_{i}", [cs, tl, ct]):
                        raise RuntimeError(f"the Compound for {tl} could not be made")
                built.append((case["name"], label, ena))
                y += 150
        return built

    # ---- read back -----------------------------------------------------
    def raw_trace(self, element: str):
        """(f_GHz, complex H, is_complex, dataset label) from a Network
        Analyzer. H is a magnitude if the analyser only exposes a gain, and
        then phase checks are skipped."""
        names = []
        try:
            names = [str(n) for n in self.sim.getresultnames(element)]
        except Exception:
            pass
        best = None
        for n in names + [x for x in ('input 1/transmission', 'input 1/S21',
                                      'input 1/gain') if x not in names]:
            try:
                res = self.sim.getresult(element, n)
            except Exception:
                continue
            for label, f, d in self._collect_datasets(res):
                is_cplx = not np.allclose(np.imag(d), 0.0)
                score = (2 if is_cplx else 0) + (1 if 'trans' in label.lower() else 0)
                if best is None or score > best[0]:
                    best = (score, label, f, d, is_cplx)
        if best is None:
            raise RuntimeError(f"No frequency-domain result could be read from {element}.")
        _, label, f, d, is_cplx = best
        if not is_cplx:
            lin = 'gain' not in label.lower() or np.all(d > 0)
            d = (np.abs(d) if lin else 10 ** (np.real(d) / 20)).astype(complex)
        return np.asarray(f, float) / 1e9, np.asarray(d, complex), is_cplx, label


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
            d = dict(f_GHz=el["f_Hz"] / 1e9, exit=r.H, entry=entry, Zs=case["Zs"], Rt=case["Rt"])
            (pred["cases"] if key == "full" else pred["short"])[case["name"]] = d
    el2 = SL.tl_sparams_from_table(tables["short"], L, None, R0, modulating=False)
    case = step0_cases(p)[0]
    r2 = SL.chain_response([el2], case["Zs"], R0, R0)        # ENA input taken as matched
    pred["2port"][case["name"]] = dict(f_GHz=el2["f_Hz"] / 1e9, exit=r2.far_end[0],
                                       Zs=case["Zs"], Rt=R0)
    pred["tables"] = tables
    pred["table_top_GHz"] = top
    return pred


def _row_line(A, cname, what, c_ref, meas_row, band, show_phase_ref=False):
    f, H, cplx, label = meas_row
    cmp = SL.compare_traces(c_ref["f_GHz"], c_ref["exit"], f, H, band)
    ph = f"{cmp['max_deg']:8.3f}" if cplx else "     n/a"
    gd = f"{cmp['mean_gd_ps']:8.3f}" if cplx else "     n/a"
    A(f"{cname:9s} {what:28s} {cmp['scale_abs']:9.4f} {cmp['max_dB']:8.4f} "
      f"{ph} {gd} {cmp['bw_ref_GHz']:8.2f} {cmp['bw_test_GHz']:8.2f}")
    sign = (" (opposite sign: flip the OM coefficient sign when replacing the TW)"
            if abs(abs(cmp['scale_deg']) - 180) < 5 else "")
    A(f"{'':9s}   scale: {SL.interpret_scale(cmp['scale_abs'])}, phase "
      f"{cmp['scale_deg']:+.1f} deg{sign}; dataset '{label}'")
    if show_phase_ref and cplx and "entry" in c_ref:
        ent = SL.compare_traces(c_ref["f_GHz"], c_ref["entry"], f, H, band)
        which = ("light LEAVING the line (as modelled)" if cmp['max_deg'] <= ent['max_deg']
                 else "light ENTERING the line -- the optical delays of the bend build "
                      "must then follow the previous electrode instead")
        A(f"{'':9s}   TW phase reference: max phase error {cmp['max_deg']:.2f} deg (exit) "
          f"vs {ent['max_deg']:.2f} deg (entry): {which}")


def format_report(pred: dict, meas: dict, stages: list, band) -> str:
    """meas[(case, label)] = (f_GHz, H, is_complex, dataset label);
    stages = [(id, title, status, detail)]."""
    L, A = [], None
    A = L.append
    A("STEP 0 -- scripted TL line element vs Ansys TW block")
    A("")
    A("Stages (each in its own INTERCONNECT session, project saved before the run):")
    first_fail = None
    for sid, title, status, detail in stages:
        A(f"  {sid}  {status:7s} {title}" + (f"\n        {detail}" if detail else ""))
        if status != "ran" and first_fail is None and sid != "S1":
            first_fail = sid
    if first_fail:
        A(f"  -> first failing stage {first_fail}: {STAGE_MEANING[first_fail]}.")
        A(f"     Open TL_step0_{first_fail}.icp, press Run, and read the message in "
          f"INTERCONNECT's Output window (the TL line also logs 'TL line ready: ...' "
          f"there when its setup script completes).")
    A("")
    A("scale = INTERCONNECT / model at 0.5-3 GHz (conventions live here); every other "
      "number is after removing it.")
    A(f"band for the comparison: {band[0]:g}-{band[1]:g} GHz; element tables up to "
      f"{pred['table_top_GHz']:.1f} GHz (the Nyquist frequency of this run)")
    A("")
    hdr = (f"{'case':9s} {'what':28s} {'scale':>9s} {'max dB':>8s} {'max deg':>8s} "
           f"{'dGD ps':>8s} {'BW ref':>8s} {'BW test':>8s}")
    for cname, c in pred["cases"].items():
        A(f"== case '{cname}': Zs = {c['Zs']:g} ohm, Rt = {c['Rt']:g} ohm")
        A(hdr)
        if (cname, "REF") in meas:
            _row_line(A, cname, "REF (TW) vs model", c, meas[(cname, "REF")], band, True)
        if (cname, "2PORT") in meas:
            _row_line(A, cname, "2PORT (far end) vs model", pred["2port"][cname],
                      meas[(cname, "2PORT")], band)
        if (cname, "FLAT_SHORT") in meas:
            _row_line(A, cname, "FLAT short table vs model", pred["short"][cname],
                      meas[(cname, "FLAT_SHORT")], band)
        for lab in ("FLAT", "CMP"):
            if (cname, lab) in meas:
                _row_line(A, cname, f"{lab} vs model", c, meas[(cname, lab)], band)
        if (cname, "REF") in meas:
            fR, HR, cR, lR = meas[(cname, "REF")]
            ref = dict(f_GHz=fR, exit=HR)
            for lab in ("FLAT", "CMP"):
                if (cname, lab) in meas:
                    _row_line(A, cname, f"{lab} vs REF (IC only)", ref, meas[(cname, lab)], band)
        A("")
    A("Pass: FLAT/CMP vs REF within ~0.05 dB and ~1 deg to the top of the band, same "
      "bandwidth to ~0.1 GHz, and a scale that is a known convention factor. The CMP "
      "row is the one to trust for reflections between blocks.")
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
    p = P.normalise(dict(p, n_bends=0))
    fs_needed = 2.5 * float(p["f_max_GHz"])
    if float(p["ic_sample_rate_GHz"]) < fs_needed:
        log(f"  Sample rate raised from {float(p['ic_sample_rate_GHz']):.0f} to "
            f"{fs_needed:.0f} GHz for a {float(p['f_max_GHz']):.0f} GHz sweep.")
        p["ic_sample_rate_GHz"] = fs_needed
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
    rep = format_report(pred, meas, status, band)
    with open(os.path.join(out_dir, "step0_report.txt"), "w") as fh:
        fh.write(rep + "\n")
    with open(os.path.join(out_dir, "step0_traces.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["case", "row", "f_GHz", "re", "im"])
        for (cname, row), (f, H, _c, _l) in meas.items():
            for fi, hi in zip(f, H):
                wr.writerow([cname, row, f"{fi:.6f}", f"{hi.real:.9e}", f"{hi.imag:.9e}"])
    log(rep)
    return rep, None
