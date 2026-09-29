"""
Step 0 for the scripted "TL line" element: is it the same electrode as the
Ansys Traveling Wave Electrode (TW) block?

For each test case the schematic has three rows, each driven by its own
Network Analyzer (impulse response) and measured on the electrode's
modulation output -- electrical only, no optics, so nothing else can differ:

  REF   ENA -> TW (Ansys, the same loss/z0/nm tables, Zs and Rt inside) -> ENA
  FLAT  ENA -> CNC(Zs|R0) -> TL line -> CNC(R0|Rt)      modulation -> ENA
  CMP   the FLAT row inside a Compound with scattering data analysis on

Cases: the GUI's Zs/Rt, and a deliberately mismatched 30/80 ohm pair so the
reflections at both ends of the line are large.

The report compares every row with the Python model and with each other, in
numbers: overall complex scale (it carries the conventions), max |dB| and max
phase difference after removing it, mean group-delay difference, and both
bandwidths. It also says which phase reference the TW block's output uses
(light leaving or light entering the line), which the documentation does not
state.

Nothing here imports lumapi unless run_step0() is called.
"""

from __future__ import annotations

import os
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


class ScriptedElementUnavailable(RuntimeError):
    """The scripted element could not be created or configured from Python."""


def step0_cases(p: dict) -> list:
    return [dict(name="gui", Zs=float(p["Zs_R"]), Rt=float(p["Rt_R"])),
            dict(name="mismatch", Zs=30.0, Rt=80.0)]


class Step0Builder(InterconnectBuilder):
    """The Step 0 schematic. Reuses the main builder's element helpers."""

    R0 = 50.0

    # ---- elements ------------------------------------------------------
    def _ena(self, name: str, x: int, y: int, p: dict):
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
        self.setp(name, ['remove dc', 'remove DC'], False, required=False)
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

    # ---- schematic -----------------------------------------------------
    def build_step0(self, p: dict, files: dict, tl_table: str, L: float,
                    library_name: Optional[str] = None, compound: bool = True) -> list:
        """Returns [(case, row, ENA name)] for everything that was built."""
        sim = self.sim
        sim.new()
        sim.switchtodesign()
        sim.deleteall()
        self._wiring = []
        self._pos = {}
        sim.set("sample rate", float(p["ic_sample_rate_GHz"]) * 1e9)
        ng = float(p["ng"])
        built = []
        for i, case in enumerate(step0_cases(p)):
            y0 = 420 * i
            pc = dict(p, Zs_R=case["Zs"], Rt_R=case["Rt"], Zs_L_pH=0.0, Zs_C_fF=0.0,
                      Rt_L_pH=0.0, Rt_C_fF=0.0, L_target_mm=L * 1e3)
            tag = f"{i + 1}"

            ena = f"ENA_REF_{tag}"
            self._ena(ena, 0, y0, pc)
            tw = f"TW_REF_{tag}"
            self._add_tw(tw, pc, files, ng, 260, y0, length_m=L)
            self.connect(ena, P_OUT, tw, P_IN)
            self.connect(tw, P_OUT, ena, P_IN1)
            built.append((case["name"], "REF", ena))

            rows = [("FLAT", y0 + 140, False)] + ([("CMP", y0 + 280, True)] if compound else [])
            for row, y, into_compound in rows:
                ena = f"ENA_{row}_{tag}"
                cs, tl, ct = f"CNCS_{row}_{tag}", f"TL_{row}_{tag}", f"CNCT_{row}_{tag}"
                self._ena(ena, 0, y, pc)
                self._cnc(cs, 200, y, case["Zs"], self.R0)
                self.make_tl(tl, 340, y, tl_table, L, ng, library_name=library_name)
                self._cnc(ct, 480, y, self.R0, case["Rt"])
                self.connect(ena, P_OUT, cs, P_CNC1)
                self.connect(cs, P_CNC2, tl, P_TL1)
                self.connect(tl, P_TL2, ct, P_CNC1)
                self.connect(tl, P_TLMOD, ena, P_IN1)
                if into_compound and not self._make_compound(f"LINE_{row}_{tag}", [cs, tl, ct]):
                    self.log(f"  Case {case['name']}: compound row not built; the FLAT row "
                             f"still runs. To add it by hand: select {cs}, {tl}, {ct}, "
                             f"right-click > Create compound, and set 'scattering data "
                             f"analysis' = true on it.")
                    continue
                built.append((case["name"], row, ena))
        return built

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

    # ---- read back -----------------------------------------------------
    def raw_trace(self, element: str):
        """(f_GHz, complex H) from a Network Analyzer; H is real (dB) if the
        analyser only exposes a gain, and then phase checks are skipped."""
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
    """Write electrode_line.txt and return the model responses per case: the
    network INTERCONNECT solves (TL chain) with both phase references."""
    tl = SL.export_tl_tables(fit, dict(p, n_bends=0, L_target_mm=L * 1e3), out_dir)
    el = SL.tl_sparams_from_table(tl["electrode"], L, float(p["ng"]), Step0Builder.R0)
    out = {"table": tl["electrode"], "cases": {}}
    w = 2 * np.pi * el["f_Hz"]
    for case in step0_cases(p):
        r = SL.chain_response([el], case["Zs"], case["Rt"], Step0Builder.R0)
        entry = r.H * np.exp(1j * w * float(p["ng"]) * L / SL.C0)
        out["cases"][case["name"]] = dict(f_GHz=el["f_Hz"] / 1e9, exit=r.H, entry=entry,
                                          Zs=case["Zs"], Rt=case["Rt"])
    return out


def format_report(pred: dict, meas: dict, band) -> str:
    """meas[(case, row)] = (f_GHz, H, is_complex, label)."""
    L = []
    A = L.append
    A("STEP 0 -- scripted TL line element vs Ansys TW block")
    A("scale = INTERCONNECT / model at 0.5-3 GHz (conventions live here); every other "
      "number is after removing it.")
    A(f"band for the comparison: {band[0]:g}-{band[1]:g} GHz")
    A("")
    hdr = (f"{'case':9s} {'what':26s} {'scale':>9s} {'max dB':>8s} {'max deg':>8s} "
           f"{'dGD ps':>8s} {'BW ref':>8s} {'BW test':>8s}")
    for cname, c in pred["cases"].items():
        A(f"== case '{cname}': Zs = {c['Zs']:g} ohm, Rt = {c['Rt']:g} ohm")
        A(hdr)
        rows = [r for (cn, r) in meas if cn == cname]
        for row in rows:
            f, H, cplx, label = meas[(cname, row)]
            cmp = SL.compare_traces(c["f_GHz"], c["exit"], f, H, band)
            ph = f"{cmp['max_deg']:8.3f}" if cplx else "     n/a"
            gd = f"{cmp['mean_gd_ps']:8.3f}" if cplx else "     n/a"
            A(f"{cname:9s} {row + ' vs model':26s} {cmp['scale_abs']:9.4f} {cmp['max_dB']:8.4f} "
              f"{ph} {gd} {cmp['bw_ref_GHz']:8.2f} {cmp['bw_test_GHz']:8.2f}")
            A(f"{'':9s}   scale: {SL.interpret_scale(cmp['scale_abs'])}, phase "
              f"{cmp['scale_deg']:+.1f} deg" + (" (opposite sign: flip the OM coefficient "
                                                "sign when replacing the TW)" if
                                                abs(abs(cmp['scale_deg']) - 180) < 5 else "")
              + f"; dataset '{label}'")
            if row == "REF" and cplx:
                ent = SL.compare_traces(c["f_GHz"], c["entry"], f, H, band)
                which = ("light LEAVING the line (as modelled)" if cmp['max_deg'] <= ent['max_deg']
                         else "light ENTERING the line -- the optical delays of the bend "
                              "build must then use the previous electrode instead")
                A(f"{'':9s}   TW phase reference: max phase error {cmp['max_deg']:.2f} deg "
                  f"(exit) vs {ent['max_deg']:.2f} deg (entry): {which}")
        if ("REF" in rows) and len(rows) > 1:
            fR, HR, cR, _ = meas[(cname, "REF")]
            for row in rows:
                if row == "REF":
                    continue
                f, H, cplx, _ = meas[(cname, row)]
                cmp = SL.compare_traces(fR, HR, f, H, band)
                ok = cplx and cR
                ph = f"{cmp['max_deg']:8.3f}" if ok else "     n/a"
                gd = f"{cmp['mean_gd_ps']:8.3f}" if ok else "     n/a"
                A(f"{cname:9s} {row + ' vs REF (IC only)':26s} {cmp['scale_abs']:9.4f} "
                  f"{cmp['max_dB']:8.4f} {ph} {gd} "
                  f"{cmp['bw_ref_GHz']:8.2f} {cmp['bw_test_GHz']:8.2f}")
        A("")
    A("Pass: FLAT/CMP vs REF within ~0.05 dB and ~1 deg to the top of the band, same "
      "bandwidth to ~0.1 GHz, and a scale that is a known convention factor. The CMP "
      "row is the one to trust for reflections between blocks.")
    return "\n".join(L)


def run_step0(fit, p: dict, out_dir: Optional[str] = None,
              library_name: Optional[str] = None, compound: bool = True,
              log: Optional[Callable[[str], None]] = None, keep_open: bool = False):
    """Export, build, run and compare. Returns (report text, builder); the
    report is also written to step0_report.txt. The builder is closed unless
    *keep_open*, in which case the caller owns the INTERCONNECT session."""
    from .extractor import export_lumerical_tables
    from .physics import device_response
    log = log or print
    p = P.normalise(dict(p, n_bends=0))
    # The impulse-response sweep needs the sample rate well above twice its
    # ceiling, or the top of every trace is a sampling artifact.
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
    log(f"  Tables in {out_dir}: loss/z0/nm.txt for the TW block, electrode_line.txt "
        f"for the TL line (up to {SL.default_table_top_GHz(p):.0f} GHz).")

    b = Step0Builder(str(p["lumapi_path"]), hide=bool(p["ic_hide"]), log=log)
    built = b.build_step0(p, files, pred["table"], L, library_name, compound)
    b.run(os.path.join(out_dir, "TL_step0.icp"))
    meas = {}
    for cname, row, ena in built:
        try:
            meas[(cname, row)] = b.raw_trace(ena)
        except Exception as exc:
            log(f"  {ena}: {exc}")
    band = (1.0, 0.95 * float(p["f_max_GHz"]))
    rep = format_report(pred, meas, band)
    with open(os.path.join(out_dir, "step0_report.txt"), "w") as fh:
        fh.write(rep + "\n")
    import csv
    with open(os.path.join(out_dir, "step0_traces.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["case", "row", "f_GHz", "re", "im"])
        for (cname, row), (f, H, _c, _l) in meas.items():
            for fi, hi in zip(f, H):
                wr.writerow([cname, row, f"{fi:.6f}", f"{hi.real:.9e}", f"{hi.imag:.9e}"])
    log(rep)
    if not keep_open:
        b.close()
        b = None
    return rep, b
