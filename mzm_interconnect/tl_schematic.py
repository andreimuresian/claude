"""
Schematic helpers for the scripted "TL line", "TL source" and "TL load"
elements, shared by the Step 0 ladder (scripted_test.py) and the modulator
build (interconnect.py, electrode model "TL line").

Everything here was established by the Step 0 runs:

  * the elements are created from Python as empty scripted elements, given
    their properties and ports with addproperty/addport, and their setup
    script with setnamed(..., "setup script", <LSF text>);
  * a network of them is solved correctly only inside a Compound with
    'scattering data analysis' on (outside, every filter pass adds its latency
    and the reflections come back late);
  * createcompound keeps a link that enters the selection from outside (the
    drive) but drops links that leave it, so every output is re-made: an
    Output port is added to the Compound, wired at root level to its
    destination, and wired inside the Compound to the relay element of that
    port ('External Port = <name>', pin 'input');
  * the source must be reciprocal, and no output may be left dangling inside
    the Compound.

Nothing here imports lumapi: the methods are mixed into InterconnectBuilder,
which owns the session.
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np

LSF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lumerical")
SETUP_LSF = os.path.join(LSF_DIR, "tl_element_setup.lsf")
LOAD_LSF = os.path.join(LSF_DIR, "termination_setup.lsf")
SOURCE_LSF = os.path.join(LSF_DIR, "source_setup.lsf")
ELECTRODE_LSF = os.path.join(LSF_DIR, "tl_electrode_setup.lsf")

SCRIPTED = ['Scripted Element', 'scripted element', 'Scripted element']


class ScriptedElementUnavailable(RuntimeError):
    """The scripted element could not be created or configured from Python."""


def fwd(path: str) -> str:
    """Forward slashes: Lumerical script reads them on every platform."""
    return path.replace("\\", "/")


def first_line(exc: Exception) -> str:
    s = str(exc).strip()
    return s.splitlines()[0] if s else type(exc).__name__


class TLElementsMixin:
    """Creates the scripted TL elements and Compounds. Needs self.sim,
    self.add, self.setp, self.connect, self.log and self._wiring (all from
    InterconnectBuilder)."""

    R0 = 50.0
    ROOT_SCOPE = "::Root Element"

    # ---- elements ----------------------------------------------------------
    def _new_scripted(self, name: str, x: int, y: int):
        try:
            self.add(SCRIPTED, name, x, y)
        except Exception as exc:
            raise ScriptedElementUnavailable(
                "This INTERCONNECT does not let a script create an empty scripted "
                "element. Create one by hand (right-click > Create scripted "
                "element), run lumerical/create_tl_element.lsf on it, add it to "
                "the Custom library, and give its library name.") from exc

    def _set_setup(self, name: str, path: str):
        with open(path, encoding="utf-8") as fh:
            code = fh.read()
        if not self.setp(name, ['setup script', 'setup', 'script setup'], code,
                         required=False):
            raise ScriptedElementUnavailable(
                f"{name}: the setup script could not be set from Python. Paste "
                f"lumerical/{os.path.basename(path)} into Edit > Scripts > Setup of one "
                f"element, add it to the Custom library, and give its library name.")

    def make_tl(self, name: str, x: int, y: int, table: str, L: float, ng: float,
                modulating: bool = True, far_end: bool = False,
                library_name: Optional[str] = None, fir_taps: int = 1024,
                ng2: Optional[float] = None):
        """
        One TL line element. With *library_name* it is taken from the Custom
        library (create it once with create_tl_element.lsf); otherwise an empty
        scripted element is created and configured here. With *ng2* (electrodes
        only) it also has the "modulation 2" output: the second arm's light,
        at its own group index, on the same line voltage.
        """
        table = fwd(table)
        second = bool(modulating) and ng2 is not None
        ng2v = float(ng2) if ng2 is not None else float(ng)
        if library_name:
            self.add([library_name], name, x, y)
        else:
            self._new_scripted(name, x, y)
            s = self.sim
            s.addproperty(name, "line_length", "TL line", "Number", 0, 1, "FixedUnit", "m", L)
            s.addproperty(name, "ng", "TL line", "Number", 0, 100, "FixedUnit", "-", ng)
            s.addproperty(name, "second_modulation", "TL line", "Logical", 0, 0,
                          "NonQuantity", "", int(second))
            s.addproperty(name, "ng2", "TL line", "Number", 0, 100, "FixedUnit", "-", ng2v)
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
            s.addproperty(name, "phase_convention", "TL line", "ComboChoice", 0, 0,
                          "NonQuantity", "", "physics;engineering")
            s.addport(name, "port 1", "Bidirectional", "Electrical Signal", "Left", 0.5)
            s.addport(name, "port 2", "Bidirectional", "Electrical Signal", "Right", 0.5)
            if modulating:
                s.addport(name, "modulation", "Output", "Electrical Signal", "Top", 0.3)
            if second:
                s.addport(name, "modulation 2", "Output", "Electrical Signal", "Top", 0.7)
            if far_end:
                s.addport(name, "far end", "Output", "Electrical Signal", "Bottom", 0.5)
            self._set_setup(name, SETUP_LSF)
        for prop, val in (("line_length", float(L)), ("ng", float(ng)),
                          ("R0", self.R0), ("table_file", table),
                          ("modulating", int(modulating)), ("far_end_output", int(far_end)),
                          ("wave_convention", "voltage"), ("fir_taps", int(fir_taps)),
                          ("phase_convention", "physics")):
            self.setp(name, [prop], val)
        # A library element made before the second output existed has neither
        # property; it is only an error when the second output is wanted.
        ok = self.setp(name, ["second_modulation"], int(second), required=second)
        ok = self.setp(name, ["ng2"], ng2v, required=second) and ok
        if not ok and modulating:
            self.log(f"  {name}: this library element has no 'second_modulation'/'ng2' "
                     f"properties; make it again with create_tl_element.lsf.")

    def make_tl_electrode(self, name: str, x: int, y: int, table: str, bend_table: str,
                          layout: str, ng: float, ng2: Optional[float] = None,
                          far_end: bool = True, fir_taps: int = 1024):
        """A whole bent electrode as one scripted element (tl_electrode_setup.lsf):
        ports 1 and 2, 'modulation' (arm 1), optionally 'modulation 2' (arm 2,
        *ng2*) and 'far end'. The light's delays between sections are inside
        the modulation outputs, so no Optical Delay is needed."""
        second = ng2 is not None
        self._new_scripted(name, x, y)
        s = self.sim
        cat = "TL electrode"
        for prop, kind, val in (("table_file", "FileOpen", fwd(table)),
                                ("bend_table_file", "FileOpen", fwd(bend_table)),
                                ("layout_file", "FileOpen", fwd(layout))):
            s.addproperty(name, prop, cat, kind, 0, 0, "NonQuantity", "", val)
        s.addproperty(name, "ng", cat, "Number", 0, 100, "FixedUnit", "-", float(ng))
        s.addproperty(name, "second_modulation", cat, "Logical", 0, 0, "NonQuantity", "",
                      int(second))
        s.addproperty(name, "ng2", cat, "Number", 0, 100, "FixedUnit", "-",
                      float(ng2 if second else ng))
        s.addproperty(name, "R0", cat, "Number", 1, 10000, "FixedUnit", "ohm", self.R0)
        s.addproperty(name, "far_end_output", cat, "Logical", 0, 0, "NonQuantity", "",
                      int(far_end))
        s.addproperty(name, "wave_convention", cat, "ComboChoice", 0, 0, "NonQuantity", "",
                      "voltage;power")
        s.addproperty(name, "fir_taps", cat, "Number", 0, 100000, "FixedUnit", "-", int(fir_taps))
        s.addproperty(name, "phase_convention", cat, "ComboChoice", 0, 0, "NonQuantity", "",
                      "physics;engineering")
        s.addport(name, "port 1", "Bidirectional", "Electrical Signal", "Left", 0.5)
        s.addport(name, "port 2", "Bidirectional", "Electrical Signal", "Right", 0.5)
        s.addport(name, "modulation", "Output", "Electrical Signal", "Top", 0.3)
        if second:
            s.addport(name, "modulation 2", "Output", "Electrical Signal", "Top", 0.7)
        if far_end:
            s.addport(name, "far end", "Output", "Electrical Signal", "Bottom", 0.5)
        self._set_setup(name, ELECTRODE_LSF)
        for prop, val in (("table_file", fwd(table)), ("bend_table_file", fwd(bend_table)),
                          ("layout_file", fwd(layout)), ("ng", float(ng)),
                          ("second_modulation", int(second)),
                          ("ng2", float(ng2 if second else ng)), ("R0", self.R0),
                          ("far_end_output", int(far_end)), ("wave_convention", "voltage"),
                          ("fir_taps", int(fir_taps)), ("phase_convention", "physics")):
            self.setp(name, [prop], val)

    def _make_rlc(self, name, x, y, kind, R, L_H, C_F, f_top, n_freq, ports, lsf):
        self._new_scripted(name, x, y)
        s = self.sim
        cat = "TL source" if kind == "source" else "TL load"
        s.addproperty(name, f"{kind}_resistance", cat, "Number", 0, 1e9, "FixedUnit", "ohm", R)
        s.addproperty(name, f"{kind}_inductance", cat, "Number", 0, 1, "FixedUnit", "H", L_H)
        s.addproperty(name, f"{kind}_capacitance", cat, "Number", 0, 1, "FixedUnit", "F", C_F)
        s.addproperty(name, "f_top", cat, "Number", 0, 1e15, "FixedUnit", "Hz", f_top)
        s.addproperty(name, "n_freq", cat, "Number", 2, 1e6, "FixedUnit", "-", n_freq)
        s.addproperty(name, "R0", cat, "Number", 1, 10000, "FixedUnit", "ohm", self.R0)
        for i, side in ports:
            s.addport(name, f"port {i}", "Bidirectional", "Electrical Signal", side, 0.5)
        self._set_setup(name, lsf)
        for prop, val in ((f"{kind}_resistance", float(R)), (f"{kind}_inductance", float(L_H)),
                          (f"{kind}_capacitance", float(C_F)), ("f_top", float(f_top)),
                          ("n_freq", int(n_freq)), ("R0", self.R0)):
            self.setp(name, [prop], val)

    def make_source(self, name: str, x: int, y: int, R: float, L_H: float = 0.0,
                    C_F: float = 0.0, f_top: float = 0.0, n_freq: int = 2):
        """The source impedance (R + jwL) || C as a scripted two-port (port 1
        from the driver, port 2 into the line): launches 2 R0/(Zs + R0) of the
        incoming wave and reflects (Zs - R0)/(Zs + R0) back into the line.
        Reciprocal, so a Compound's solver finds a path from port 1 back to
        itself. With L = C = 0 the entries are constants (the Step 0 element);
        otherwise tables from 0 to *f_top* Hz with *n_freq* points."""
        self._make_rlc(name, x, y, "source", R, L_H, C_F, f_top, n_freq,
                       ((1, "Left"), (2, "Right")), SOURCE_LSF)

    def make_load(self, name: str, x: int, y: int, R: float, L_H: float = 0.0,
                  C_F: float = 0.0, f_top: float = 0.0, n_freq: int = 2):
        """A one-port termination (R + jwL) || C: reflects (Zt - R0)/(Zt + R0)
        and leaves no unconnected port, which a Compound's solver may refuse."""
        self._make_rlc(name, x, y, "load", R, L_H, C_F, f_top, n_freq,
                       ((1, "Left"),), LOAD_LSF)

    # ---- Compound --------------------------------------------------------
    def make_compound(self, name: str, members: list, outputs=()) -> bool:
        """
        Group *members* into a Compound named *name*, give it one Output port
        per entry of *outputs*, and turn its S-parameter solver on.

        *outputs* is a list of (element, element port, Compound port name,
        destination element, destination port candidates). Each Compound port
        is wired to its destination at root level and, inside the Compound, to
        the relay of that port and to no other relay (wiring an output onto the
        drive's relay shorts it onto the drive; the second Step 0 run did
        that). A wire that cannot be drawn is added to self.pending_manual with
        instructions, and nothing is wired to a guess.

        Returns False if the Compound could not be made at all.
        """
        s = self.sim
        if not hasattr(self, "pending_manual"):
            self.pending_manual = []
        try:
            s.select(members[0])
            for m in members[1:]:
                s.shiftselect(m)
            s.createcompound()
        except Exception as exc:
            self.log(f"  createcompound failed: {exc}")
            return False
        for cand in ("COMPOUND_1", "Compound Element", "COMPOUND"):
            try:
                s.setnamed(cand, "name", name)
                break
            except Exception:
                continue

        n = len(outputs)
        for k, (el, port, pname, dest, dest_ports) in enumerate(outputs):
            before = self._elements_inside(name)
            try:
                got = s.addport(name, pname, "Output", "Electrical Signal", "Right",
                                (k + 1) / (n + 1))
                if isinstance(got, str) and got:
                    pname = got
            except Exception as exc:
                self.log(f"  {name}: addport '{pname}' failed: {first_line(exc)}")
                self.pending_manual.append(
                    f"{name}: add an output port '{pname}' and wire {el} '{port}' to it")
                continue
            if dest is not None and \
                    self.connect(name, [pname], dest, dest_ports, required=False) is None:
                self.log(f"  {name}: '{pname}' could not be wired to {dest} {dest_ports}")
            self._wire_relay(name, el, port, pname, before, members, k)

        ok = self.setp(name, ['scattering data analysis'], True, required=False)
        if not ok:
            self.log(f"  {name}: could not switch 'scattering data analysis' on.")
        return ok

    def _wire_relay(self, name, el, port, pname, before, members, k: int = 0) -> bool:
        s = self.sim
        inner, refused, inside, relay = False, [], [], None
        try:
            s.groupscope(f"{self.ROOT_SCOPE}::{name}")
            inside = self._scope_elements()
            relay = self._find_relay(inside, pname, before, members)
            if relay:
                for tport in ("input", "port", pname, "port 1"):
                    try:
                        s.connect(el, port, relay, tport)
                    except Exception as exc:
                        refused.append(f"{relay}:{tport} ({first_line(exc)})")
                        continue
                    self._wiring.append(f"{el}:{port} -> {relay}:{tport}")
                    self.log(f"  {name}: inside, {el}:{port} -> {relay}:{tport}")
                    inner = True
                    break
                # INTERCONNECT drops every new relay at the same spot; spread the
                # output relays so each label can be read (cosmetic only).
                try:
                    y0 = float(s.getnamed(relay, "y position"))
                    s.setnamed(relay, "y position", y0 + 110 * k)
                except Exception:
                    pass
        except Exception as exc:
            refused.append(f"could not enter the Compound's scope ({first_line(exc)})")
        finally:
            try:
                s.groupscope(self.ROOT_SCOPE)
            except Exception:
                pass
        if not inner:
            self.log(f"  {name}: elements inside: {', '.join(inside) or 'could not be listed'}; "
                     f"relay of '{pname}': {relay or 'not identified'}")
            for r in refused:
                self.log(f"  {name}: refused {r}")
            self.pending_manual.append(
                f"{name}: open the saved .icp, double-click {name}, draw the wire from "
                f"{el} '{port}' to the 'input' pin of the relay whose label reads "
                f"'External Port = {pname}' ({relay or 'not identified'}), "
                f"leave every other wire as it is, and save the project")
        return inner

    def _elements_inside(self, name: str) -> list:
        """Names of the elements inside Compound *name* (scope restored)."""
        try:
            self.sim.groupscope(f"{self.ROOT_SCOPE}::{name}")
            return self._scope_elements()
        except Exception:
            return []
        finally:
            try:
                self.sim.groupscope(self.ROOT_SCOPE)
            except Exception:
                pass

    def _find_relay(self, inside: list, pname: str, before: list, members: list):
        """The relay element of the Compound port *pname*, called from inside
        the Compound's scope: the relay whose external port is *pname*, else
        the one element that appeared when the port was added. None if neither
        identifies it; nothing is wired to a guess."""
        for x in inside:
            for prop in ("external port", "External Port", "external_port"):
                try:
                    if str(self.sim.getnamed(x, prop)).strip() == pname:
                        return x
                except Exception:
                    continue
        new = [x for x in inside if x not in before and x not in members]
        return new[0] if len(new) == 1 else None

    def _scope_elements(self) -> list:
        """Names of the elements in the current group scope (empty if the
        script interface does not give them)."""
        code = ('selectall; mzm_n = getnumber; mzm_names = ""; '
                'for (mzm_i = 1:mzm_n) { mzm_names = mzm_names + get("name", mzm_i) + ";"; } '
                'unselectall;')
        try:
            self.sim.eval(code)
            return [x for x in str(self.sim.getv("mzm_names")).split(";") if x.strip()]
        except Exception as exc:
            self.log(f"  could not list the elements in this scope ({first_line(exc)})")
            return []

    # ---- read back -------------------------------------------------------
    def complex_trace(self, element: str, input_port: Optional[int] = None):
        """(f_GHz, complex H, is_complex, dataset label) from a Network
        Analyzer. With *input_port* only that input's results are considered.
        H is a magnitude if the analyser only exposes a gain, and then phase
        checks are skipped."""
        names = []
        try:
            names = [str(n) for n in self.sim.getresultnames(element)]
        except Exception:
            pass
        pref = f"input {input_port or 1}/"
        fallback = [pref + x for x in ('transmission', 'S21', 'gain')]
        cands = names + [x for x in fallback if x not in names]
        if input_port is not None:
            cands = [n for n in cands if n.lower().startswith(pref)]
        best = None
        for n in cands:
            try:
                res = self.sim.getresult(element, n)
            except Exception:
                continue
            for label, f, d in self._collect_datasets(res):
                is_cplx = not np.allclose(np.imag(d), 0.0)
                score = (2 if is_cplx else 0) + (1 if 'trans' in label.lower() else 0)
                if best is None or score > best[0]:
                    best = (score, f"{n}/{label}", f, d, is_cplx)
        if best is None:
            raise RuntimeError(f"No frequency-domain result could be read from {element}"
                               + (f" input {input_port}." if input_port else "."))
        _, label, f, d, is_cplx = best
        if not is_cplx:
            lin = 'gain' not in label.lower() or np.all(d > 0)
            d = (np.abs(d) if lin else 10 ** (np.real(d) / 20)).astype(complex)
        return np.asarray(f, float) / 1e9, np.asarray(d, complex), is_cplx, label
