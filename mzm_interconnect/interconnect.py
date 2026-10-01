"""
Lumerical INTERCONNECT schematic builder and runner.

This is the former MZM_API_launcher, turned into something the GUI can call:
it takes the same normalised parameter dictionary the Python model uses, plus
the exported table files, and builds the schematic. Nothing here is imported
unless the user actually asks for INTERCONNECT, so the rest of the toolkit
runs fine on a machine with no Lumerical installation.

Two topologies are available:

  "single-arm"  one driven arm + a static phase shifter in the other.
                This is the historically validated build.

  "push-pull"   both arms modulated with opposite-sign phase coefficients,
                which is what an X-cut LN G-S-G device physically does. Each
                arm has its own traveling-wave electrode element (same
                microwave tables, same drive) so each can carry its own
                optical group index; with no n_g imbalance the two are
                identical. V_pi halves and the chirp goes to zero.

Two electrode models are available (parameter ic_electrode_model):

  "TL line"     the scripted TL line element (lumerical/tl_element_setup.lsf),
                validated against the exact line model by the Step 0 ladder.
                The whole electrical network -- source (R+L+C), electrode
                sections, bends, termination (R+L+C) -- is one Compound with
                scattering data analysis on, so INTERCONNECT solves every
                reflection itself. Each electrode section has one modulation
                output per arm ("modulation" at arm 1's n_g, "modulation 2" at
                arm 2's), feeding that arm's Optical Modulator Measured; the
                last section also outputs the voltage across the termination
                ("far end"), read by ENA_1 input 2 or by the electrical eye
                EYE_2. No drive fan-out, no per-section drive files.

  "TW block"    the Ansys Traveling Wave Electrode, as below.

With the TW block and electrode bends (n_bends > 0) each arm is a chain of TW + OM sections.
A TW element is one uniform line between a source and a load, so each section
gets the exact Thevenin source and load of its position as impedance TABLES,
and sections after the first are driven through an Electrical Delay and an
Electrical N Port S-Parameter holding V_th/V_s. Optical Delays between the
OMs carry the light's transit through the bends and sections. The bends are
not elements: their impedance, loss and delay live in those tables, which is
what keeps every section on the fitted line tables and the result identical
to the Python cascade (checked to 1e-14 with the closed-form TW model).

If the INTERCONNECT build in use will not fan one electrical output out to two
electrodes, the builder falls back to a single modulator carrying the summed
efficiency. That reproduces the same |S21| and the same effective V_pi -- the
chirp and any n_g imbalance are lost -- and it says so loudly in the log
rather than silently building something different.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Callable, Optional, Sequence

import numpy as np

from . import parameters as P
from .physics import C0, electrode_layout, normalise_and_measure, rlc_impedance
from .tl_schematic import TLElementsMixin


class LumericalUnavailable(RuntimeError):
    pass


class BendsNotSupported(RuntimeError):
    """The schematic cannot yet represent a segmented electrode."""


class _FanOutUnsupported(RuntimeError):
    """This INTERCONNECT build will not drive two electrodes from one
    electrical output, so push-pull has to fall back to the lumped equivalent."""


class PortNameError(RuntimeError):
    """No spelling of a port name was accepted for a connection.

    Port names are not stable across INTERCONNECT versions and element
    libraries -- the same physical pin is 'input', 'in', 'in1' or 'port 1'
    depending on the build -- so every connection is tried against a list of
    spellings. This is raised only when every one of them was refused, and it
    carries INTERCONNECT's own message, which usually names the ports that do
    exist.
    """


# Port-name spellings to try, most likely first. Indexed ports keep their
# index across spellings so a two-output splitter cannot get crossed over.
def _pin(*names):
    return list(names)


P_IN = _pin('input', 'in', 'port 1', 'in1', 'input 1', 'port1')
P_OUT = _pin('output', 'out', 'port 2', 'out1', 'output 1', 'port2')
P_BI1 = _pin('port 1', 'input', 'in', 'in1', 'port1')
P_BI2 = _pin('port 2', 'output', 'out', 'out1', 'port2')
P_OUT1 = _pin('output 1', 'out1', 'output1', 'port 2', 'port2')
P_OUT2 = _pin('output 2', 'out2', 'output2', 'port 3', 'port3')
P_IN1 = _pin('input 1', 'in1', 'input1', 'port 1', 'port1')
P_IN2 = _pin('input 2', 'in2', 'input2', 'port 2', 'port2')
P_MOD = _pin('modulation', 'modulation 1', 'mod', 'electrical', 'input 2', 'in2')
# The NRZ generator's digital input is called 'modulation', not 'input' -- it is
# the one port in this schematic whose name gives no hint of its direction.
P_DIGI_IN = _pin('modulation', 'input', 'in', 'port 1', 'in1')
# A combiner's single port is its OUTPUT, so when this build names its splitter
# ports positionally the combiner's output is 'port 1' -- not 'port 2', which
# would silently wire the detector to one of the inputs.
P_COMB_OUT = _pin('output', 'out', 'port 1', 'output 1', 'out1')
# The Y branch names its ports unambiguously: 'port 1' is the single side,
# 'port 2' and 'port 3' are the pair. No guessing which output is which.
P_Y1, P_Y2, P_Y3 = _pin('port 1'), _pin('port 2'), _pin('port 3')
# The eye analyser's reference input. Its documented job is "automatic delay
# compensation of the input signal": it is the timing reference the element
# folds the received waveform against, so without it there is no eye at all --
# not merely a missing BER. It is enabled by default, which is why it shows up
# in the schematic as an unconnected pin waiting for something.
P_SPAR1 = _pin('port 1', 'port1', 'input', 'in', 'input 1')
P_SPAR2 = _pin('port 2', 'port2', 'output', 'out', 'output 1')
P_EYE_REF = _pin('reference', 'reference input', 'signal reference', 'input 2')
# Everything worth probing when a name is refused.
P_ALL = _pin('input', 'output', 'in', 'out', 'modulation', 'reference',
             'port 1', 'port 2', 'port 3', 'port 4',
             'input 1', 'input 2', 'output 1', 'output 2',
             'in1', 'in2', 'out1', 'out2', 'electrical', 'optical')


def load_lumapi(lumapi_path: str):
    """Import lumapi from an explicit install directory."""
    if lumapi_path and os.path.isdir(lumapi_path) and lumapi_path not in sys.path:
        sys.path.insert(0, lumapi_path)
    try:
        import lumapi                                   # noqa: F401
        return lumapi
    except Exception as exc:                            # pragma: no cover
        raise LumericalUnavailable(
            f"Could not import lumapi from '{lumapi_path}'. Point the "
            f"'lumapi directory' field at e.g. "
            f"C:\\Program Files\\Lumerical\\v242\\api\\python  ({exc})") from exc


# Samples per symbol the eye analyser needs to fold a waveform sensibly.
EYE_SAMPLES_PER_SYMBOL = 16

KNOWN_ENA_RESULTS = ['input 1/S21', 'input 1/transmission', 'input 1/gain',
                     'S21', 'transmission', 'gain', 'ENA_1', 'model']


def uses_tl_line(p: dict) -> bool:
    """True when the schematic's electrode is the scripted TL line."""
    return str(p.get("ic_electrode_model", "TW block")).strip().lower().startswith("tl")


class ManualWiringNeeded(RuntimeError):
    """The schematic was built, but a wire inside the Compound could not be
    drawn from the script. The project is saved; the message says which wire."""


class InterconnectBuilder(TLElementsMixin):
    """Builds, runs and reads back a traveling-wave MZM schematic."""

    def __init__(self, lumapi_path: str, hide: bool = False,
                 log: Optional[Callable[[str], None]] = None):
        self.log = log or (lambda m: print(m))
        self._lumapi = load_lumapi(lumapi_path)
        self.sim = self._lumapi.INTERCONNECT(hide=bool(hide))
        self.topology = None
        self.mode = "ena"
        self.uses_y_branch = False
        self._wiring = []
        self.pending_manual = []
        self.electrode_model = "TW block"
        self.far_end = None             # where the far-end voltage is read, if anywhere
        self.diagnose = False           # TL line: also read the modulation voltage (input 3)
        self.ena_inputs = 1

    # ---------------- low level helpers (from the original launcher) ----
    def setp(self, el, candidates, value, required=True):
        for c in candidates:
            try:
                self.sim.setnamed(el, c, value)
                return True
            except Exception:
                continue
        if required:
            raise KeyError(f"{el}: none of {candidates} accepted")
        return False

    def add(self, candidates, name, x, y):
        x, y = getattr(self, "_pos", {}).get(name, (x, y))
        for c in candidates:
            try:
                el = self.sim.addelement(c)
                if el.name != name:          # skip the no-op rename that spams warnings
                    el.name = name
                el.x_position = x
                el.y_position = y
                return el
            except Exception:
                continue
        raise RuntimeError(f"Cannot add {name} from {candidates}")

    def _try_connect(self, a, pa, b, pb) -> bool:
        try:
            self.sim.connect(a, pa, b, pb)
            self._wiring.append(f"{a}:{pa} -> {b}:{pb}")
            return True
        except Exception:
            return False

    def connect(self, a, ports_a, b, ports_b, required=True):
        """
        Wire two elements, trying every spelling of each port name.

        The element library does not name its pins consistently across
        versions, and a single refused name used to abort the whole build --
        which is how an eye schematic ended up on screen with no modulators in
        it: the drive chain was wired before the interferometer, so one bad
        port name upstream meant the arms were never created at all. Both
        halves of that are fixed: names are resolved here, and the optical core
        is now built and wired before anything electrical is attached.
        """
        last = None
        for pa in ports_a:
            for pb in ports_b:
                try:
                    self.sim.connect(a, pa, b, pb)
                    self._wiring.append(f"{a}:{pa} -> {b}:{pb}")
                    return (pa, pb)
                except Exception as exc:
                    last = exc
        if not required:
            self.log(f"  (optional link {a} -> {b} not made)")
            return None
        raise PortNameError(
            f"Could not wire {a} -> {b}. Tried {ports_a} against {ports_b}. "
            f"INTERCONNECT said: {last}")

    def report_ports(self, *elements) -> dict:
        """
        Discover what each element's ports are really called, by probing.

        INTERCONNECT has no portable "list the ports" call, and its error text
        does not enumerate them -- it only ever says it cannot find the name
        you asked for. So this asks a different question: connect the element
        to *itself* on a candidate name. A port that does not exist gives "can
        not find port"; a port that does exist gives some other complaint
        (connecting an element to itself, a port already in use, mismatched
        signal types). Any answer that is not "can not find port" therefore
        means the name is real.

        Run it when a build stops on a port name. The list it prints is the
        answer, not a hint.
        """
        out = {}
        for el in elements:
            found = []
            for name in P_ALL:
                try:
                    self.sim.connect(el, name, el, name)
                    found.append(name)          # accepted outright
                except Exception as exc:
                    msg = str(exc).lower()
                    if "find port" not in msg and "no such port" not in msg \
                            and "does not exist" not in msg:
                        if "find element" in msg:
                            found = ["(element not in the schematic)"]
                            break
                        found.append(name)
            out[el] = found
            self.log(f"  ports of {el}: {', '.join(found) if found else '(none found)'}")
        return out

    # ---------------- build --------------------------------------------
    def build(self, p: dict, files: dict, mode: str = "ena") -> str:
        """
        Build the whole schematic from a normalised parameter dict and the
        loss/z0/nm table paths. Returns the topology actually built.

        A push-pull build needs one electrical output to feed two electrodes
        (one per arm). Not every INTERCONNECT build allows that, so if the
        fan-out is refused we throw the half-wired schematic away and build the lumped
        equivalent from a clean slate. Patching a partially connected
        schematic in place is what used to leave the session wedged: the
        repair tried to connect ports that were still occupied, the exception
        escaped, and the GUI was left holding a broken session.
        """
        p = P.normalise(p)
        self.mode = mode
        if uses_tl_line(p):
            if not files.get("tl"):
                raise RuntimeError("Electrode model 'TL line' needs the TL tables: export "
                                   "them with export_lumerical_tables (it writes them when "
                                   "ic_electrode_model is 'TL line').")
            # One line, one output per arm: nothing to fan out, no fallback.
            self.topology = self._build_once(
                p, files, pushpull=str(p["drive_config"]) == "push-pull", mode=mode)
            return self.topology
        if int(p.get("n_bends", 0)) > 0:
            if not files.get("bend_sections"):
                raise BendsNotSupported("n_bends > 0 but the tables were exported "
                                        "without the per-section bend files.")
            # No lumped fallback here: a single modulator cannot carry a
            # segmented electrode, so a refused fan-out is reported as is.
            self.topology = self._build_once(
                p, files, pushpull=str(p["drive_config"]) == "push-pull", mode=mode)
            return self.topology
        if str(p["drive_config"]) == "push-pull":
            try:
                self.topology = self._build_once(p, files, pushpull=True, mode=mode)
                return self.topology
            except _FanOutUnsupported:
                self.log("  This INTERCONNECT build will not fan one electrical "
                         "output out to two electrodes.")
            except PortNameError:
                # Rebuilding as a lumped equivalent would hit the same port
                # name, so there is nothing to fall back to. Let it out with
                # its diagnostic intact.
                raise
            except Exception as exc:
                self.log(f"  Push-pull build failed ({type(exc).__name__}: {exc}).")
            self.log("  Rebuilding from scratch as a lumped push-pull equivalent.")
            self.topology = self._build_once(p, files, pushpull=False,
                                             lumped_pp=True, mode=mode)
            return self.topology

        self.topology = self._build_once(p, files, pushpull=False, mode=mode)
        return self.topology

    def _build_once(self, p: dict, files: dict, pushpull: bool,
                    lumped_pp: bool = False, mode: str = "ena") -> str:
        sim = self.sim
        sim.new()
        sim.switchtodesign()
        sim.deleteall()
        self._wiring = []
        self.pending_manual = []
        self.far_end = None
        tl = uses_tl_line(p)
        self.electrode_model = "TL line" if tl else "TW block"
        if tl:
            n_mod = sum(1 for x in electrode_layout(p) if x["kind"] == "mod")
            self._pos = self._tl_positions(n_mod)
        else:
            secs = files.get("bend_sections") if int(p.get("n_bends", 0)) > 0 else None
            self._pos = self._bend_positions(len(secs)) if secs else {}
        # In eye mode the sample rate has to resolve a symbol, not just the
        # top of the microwave band: the element folds the waveform on the
        # symbol period, and a handful of samples per symbol gives it nothing
        # to fold. 16 per symbol is the usual floor. At the 320 GHz default a
        # 100 Gb/s NRZ eye would get 3.2, which is why it produced nothing.
        fs_GHz = float(p["ic_sample_rate_GHz"])
        if mode == "eye":
            levels = 4 if str(p["mod_format"]).upper() == "PAM4" else 2
            sym_rate = float(p["bitrate_Gbps"]) / (1 if levels == 2 else 2)
            needed = EYE_SAMPLES_PER_SYMBOL * sym_rate
            if fs_GHz < needed:
                self.log(f"  Sample rate raised from {fs_GHz:.0f} to "
                         f"{needed:.0f} GHz: an eye at {sym_rate:.0f} GBd needs "
                         f"at least {EYE_SAMPLES_PER_SYMBOL} samples per symbol "
                         f"and {fs_GHz:.0f} GHz gives {fs_GHz/sym_rate:.1f}.")
                fs_GHz = needed
        sim.set("sample rate", fs_GHz * 1e9)

        f_opt = 299792458.0 / (float(p["lambda_nm"]) * 1e-9)

        # ---- 1. optical source ----
        self.add(['CW Laser'], 'CWL_1', 115, 195)
        self.setp('CWL_1', ['frequency'], f_opt)
        self.setp('CWL_1', ['power'], 10 ** (float(p["P_laser_dBm"]) / 10) / 1000)
        self.setp('CWL_1', ['linewidth'], 0)
        self.setp('CWL_1', ['enable RIN', 'RIN enable'], False, required=False)
        self.setp('CWL_1', ['linewidth distribution', 'linewidth_distribution'],
                  'Lorentzian', required=False)

        # ---- 2. splitter / combiner ----
        self.uses_y_branch = self._add_y_branches(p)

        # ---- 3. bias / static arm-phase error ----
        phase_rad = np.deg2rad(float(p["bias_phase_deg"]) + float(p["arm_phase_imbalance_deg"]))
        self.add(['Optical Phase Shift'], 'PHS_1', 640, 285)
        self.setp('PHS_1', ['input parameter'], 'constant', required=False)
        self.setp('PHS_1', ['phase shift'], float(phase_rad))

        # ---- 4. arm-2 excess loss (asymmetric over-etch + split error) ----
        # a1 = sqrt(rho), a2 = sqrt(1-rho).10^(-loss/20), so an even split with
        # an extra loss - 10.log10((1-rho)/rho) dB on arm 2 gives the same field
        # ratio, and the field ratio is all the interference knows about.
        rho = min(max(0.5 + float(p["split_err"]), 1e-6), 1 - 1e-6)
        d_split = 0.0 if self.uses_y_branch else -10.0 * np.log10((1.0 - rho) / rho)
        d_loss = float(p["arm_loss_imbalance_dB"]) + d_split
        if abs(d_split) > 1e-9:
            self.log(f"  Splitter {100*rho:.1f}:{100*(1-rho):.1f} folded into the "
                     f"arm-2 attenuator as {d_split:+.3f} dB (this build has no "
                     f"Y branch and the SPLT element has no ratio field); "
                     f"total arm-2 loss {d_loss:.3f} dB.")
        self.has_attenuator = False
        if abs(d_loss) > 1e-9:
            try:
                self.add(['Optical Attenuator'], 'ATT_1', 730, 285)
                # An attenuator cannot add power, so a negative imbalance is
                # applied to the other arm instead by flipping which arm the
                # reference is. Keep it on arm 2 and make it non-negative.
                self.setp('ATT_1', ['attenuation'], max(d_loss, 0.0))
                if d_loss < 0:
                    self.log(f"  arm-2 imbalance is negative ({d_loss:.3f} dB): "
                             f"arm 1 is the lossier one. The attenuator is held "
                             f"at 0 dB; swap the arms to model it directly.")
                self.has_attenuator = True
            except Exception as exc:
                self.log(f"  arm-2 attenuator not available ({exc}); "
                         f"loss imbalance applied in the Python model only.")

        # ---- 5. modulator coefficients ----
        L_OM = 1e-6
        vpi = float(p["Vpi_V"])
        d = float(p["vpi_imbalance_frac"])
        c1 = -np.pi / (vpi * L_OM)
        c2 = +np.pi / (vpi * (1.0 + d) * L_OM)

        def add_modulator(name, x, y, coeff):
            self.add(['Optical Modulator Measured', 'Optical Modulator (Measured)'],
                     name, x, y)
            self.setp(name, ['configuration'], 'bidirectional')
            self.setp(name, ['length'], L_OM)
            self.setp(name, ['electrode type'], 'lumped')
            self.setp(name, ['input parameter'], 'coefficients')
            self.setp(name, ['phase coefficient c', 'c'], coeff)
            for k in ('a', 'b', 'd'):
                self.setp(name, [f'phase coefficient {k}', k], 0.0, required=False)
            for k in ('a', 'b', 'c', 'd'):
                self.setp(name, [f'absorption coefficient {k}', f'absorption {k}'],
                          0.0, required=False)

        # ---- 6. traveling-wave electrode(s) ----
        # A GSG line is one microwave mode, but each arm's light rides it at
        # its own group index, so each arm sees its own walk-off. The TW
        # element carries a single `optical index`, so a true push-pull build
        # gets one electrode per arm: identical microwave tables, identical
        # source and load, driven by the same signal, differing only in n_g.
        # With ng_imbalance = 0 the two are identical and the result is the
        # same as one electrode feeding both arms.
        ng = float(p["ng"])
        dn = float(p.get("ng_imbalance", 0.0))
        ng1, ng2 = ng * (1.0 + dn / 2.0), ng * (1.0 - dn / 2.0)
        self.bend_sections = (files.get("bend_sections")
                              if int(p.get("n_bends", 0)) > 0 and not tl else None)
        if tl:
            self.tw_names = []      # the TL line electrode is built after the drive
        elif self.bend_sections:
            pass                    # electrodes are built per section in _wire_arms_bends
        elif pushpull:
            self.tw_names = ['TW_1', 'TW_2']
            self._add_tw('TW_1', p, files, ng1, 420, -45)
            self._add_tw('TW_2', p, files, ng2, 420, 420)
            self.log(f"  Two electrodes, one per arm: n_g = {ng1:.5f} (arm 1) and "
                     f"{ng2:.5f} (arm 2).")
        else:
            self.tw_names = ['TW_1']
            # Single-arm drive only modulates arm 1, so arm 1's index is the
            # one that matters. The lumped push-pull fallback has one electrode
            # for two arms and cannot carry a difference.
            self._add_tw('TW_1', p, files, ng if lumped_pp else ng1, 420, -45)
            if lumped_pp and abs(dn) > 0:
                self.log(f"  ng_imbalance = {dn:g} is NOT in this schematic: the "
                         f"lumped fallback has one electrode for both arms. "
                         f"The Python bandwidth includes it; this one will not.")

        # ---- 7. detector ----
        self.add(['PIN Photodetector', 'Photodetector'], 'PIN_1', 950, 210)
        self.setp('PIN_1', ['responsivity'], 1)
        self.setp('PIN_1', ['frequency at max power'], False, required=False)
        self.setp('PIN_1', ['frequency'], f_opt, required=False)
        for q in ('thermal noise', 'shot noise', 'power saturation'):
            self.setp('PIN_1', [f'enable {q}', f'{q} enable'], False, required=False)

        # ---- 8. electrical drive and sink ----
        # The optical half of the schematic is identical in both modes. What
        # changes is what drives the electrode and what reads the detector: a
        # network analyser for the small-signal response, a PRBS/NRZ pair and an
        # eye analyser for the time domain. Building them from the same code
        # path is the point -- an eye and a bandwidth then describe the same
        # device by construction.
        # ---- 9. wiring ----
        # Order matters. The interferometer is built and wired first, because
        # it is the part that has been validated and the part worth keeping if
        # anything downstream refuses. The drive and the detector sink go on
        # last, so a port name this build spells differently costs one clear
        # error instead of a schematic with no modulators in it.
        self.connect('CWL_1', P_OUT, 'SPLT_1', self.p_split_in)
        self.connect('SPLT_2', self.p_comb_out, 'PIN_1', P_IN)
        if tl:
            topo = self._wire_arms_tl(p, pushpull, add_modulator, c1, c2, ng1, ng2)
        elif self.bend_sections:
            topo = self._wire_arms_bends(p, files, pushpull, add_modulator, c1, c2,
                                         ng1, ng2)
        else:
            topo = self._wire_arms(p, pushpull, lumped_pp, add_modulator, c1, c2, L_OM)

        if mode == "eye":
            self._add_eye_chain(p)
            self.connect('PIN_1', P_OUT, 'EYE_1', P_IN)
            if tl:
                self._build_tl_electrode(p, files, 'NRZ_1', pushpull, mode)
            else:
                self._drive_electrodes('NRZ_1')
            self._wire_eye_reference(p)
            if tl:
                self._wire_far_end_eye_reference()
            self._check_eye_wiring()
        else:
            self._add_ena(p)
            self.connect('PIN_1', P_OUT, 'ENA_1', P_IN1)
            if tl:
                self._build_tl_electrode(p, files, 'ENA_1', pushpull, mode)
            else:
                self._drive_electrodes('ENA_1')
        self.log(f"  Wiring resolved: {len(self._wiring)} links.")
        return topo

    def _add_tw(self, name: str, p: dict, files: dict, ng: float, x: int, y: int,
                length_m: Optional[float] = None, zsrc: Optional[str] = None,
                zload: Optional[str] = None):
        """One travelling-wave electrode loaded with the fitted line tables.
        *zsrc* / *zload* replace the constant source / termination with
        frequency-dependent tables (a section inside a bent electrode)."""
        self.add(['Traveling Wave Electrode'], name, x, y)
        self.setp(name, ['length'], float(p["L_target_mm"]) * 1e-3 if length_m is None
                  else float(length_m))
        self.setp(name, ['optical index'], float(ng))
        self.setp(name, ['transfer function'], 'modulation voltage')

        nm_ok = (self.setp(name, ['microwave index type'], 'table', required=False) and
                 self.setp(name, ['load microwave index from file',
                                  'microwave index from file'], True, required=False) and
                 self.setp(name, ['microwave index filename', 'microwave index file'],
                           files["nm"], required=False))
        if nm_ok:
            self.log(f"  {name}: dispersive n_m(f) table loaded from nm.txt")
        else:
            nm60 = float(np.loadtxt(files["nm"], comments='#')[:, 1].mean())
            self.setp(name, ['microwave index type'], 'constant')
            self.setp(name, ['microwave index'], nm60)
            self.log(f"  {name}: n_m table unsupported -> constant n_m = {nm60:.4f}")

        self.setp(name, ['loss type'], 'table')
        self.setp(name, ['load loss from file', 'loss from file'], True)
        self.setp(name, ['loss filename', 'loss file'], files["loss"])
        self.setp(name, ['characteristic impedance type'], 'table')
        self.setp(name, ['load characteristic impedance from file',
                         'characteristic impedance from file'], True)
        self.setp(name, ['characteristic impedance filename',
                         'characteristic impedance file'], files["z0"])

        # INTERCONNECT takes a single constant reactance, so any L/C parasitic
        # is collapsed to its value at the probe frequency. The Python model
        # keeps the full frequency dependence -- expect the two to diverge if
        # you push the parasitics hard.
        f_probe = float(p["f_probe_GHz"])
        zs = complex(rlc_impedance(np.array([f_probe]), float(p["Zs_R"]),
                                   float(p["Zs_L_pH"]), float(p["Zs_C_fF"]))[0])
        zt = complex(rlc_impedance(np.array([f_probe]), float(p["Rt_R"]),
                                   float(p["Rt_L_pH"]), float(p["Rt_C_fF"]))[0])
        self.setp(name, ['source resistance'], float(np.real(zs)))
        self.setp(name, ['source reactance'], float(np.imag(zs)))
        self.setp(name, ['terminating resistance'], float(np.real(zt)))
        self.setp(name, ['terminating reactance'], float(np.imag(zt)))
        if zsrc is None and zload is None and name == 'TW_1' and \
                (abs(np.imag(zs)) > 1e-9 or abs(np.imag(zt)) > 1e-9):
            self.log(f"  NOTE: source/load reactance frozen at {f_probe:.1f} GHz "
                     f"(Xs={np.imag(zs):+.2f}, Xt={np.imag(zt):+.2f} ohm).")
        for tbl, kind in ((zsrc, 'source'), (zload, 'terminating')):
            if tbl is None:
                continue
            self.setp(name, [f'{kind} impedance type'], 'table')
            self.setp(name, [f'load {kind} impedance from file'], True)
            self.setp(name, [f'{kind} impedance filename'], tbl)
        self.setp(name, ['junction capacitance', 'constant junction capacitance'],
                  0, required=False)
        self.setp(name, ['junction resistance', 'constant junction resistance'],
                  0, required=False)


    def _add_y_branches(self, p: dict) -> bool:
        """
        Build the input splitter and output combiner, preferring Y branches.

        The Y element is what a thin-film LN interferometer actually has at
        each end, and unlike the SPLT element it takes a power coupling
        coefficient in [0, 1], so an imperfect split is a property rather than
        something to work around. It also conserves power the way a real Y
        does -- T and 1-T redistribute rather than dissipate -- which the
        attenuator workaround could not, and which matters as soon as the
        absolute received power decides whether the eye is noise limited.

        Port semantics are unambiguous: 'port 1' is the single side, 'port 2'
        and 'port 3' are the pair, and the coupling coefficient T is the
        port 1 <-> port 3 power transmission with port 1 <-> port 2 getting
        1 - T. Arm 1 hangs off port 2 and arm 2 off port 3, so a fraction rho
        of the power into arm 1 means T = 1 - rho.

        Returns True if Y branches were used, False if this build only has the
        SPLT element and the split error has to be folded into the attenuator.
        """
        rho = min(max(0.5 + float(p["split_err"]), 1e-6), 1 - 1e-6)
        y_loss = float(p["y_branch_loss_dB"])
        try:
            for name, x, y in (('SPLT_1', 280, 195), ('SPLT_2', 780, 210)):
                self.add(['Waveguide Y Branch'], name, x, y)
                self.setp(name, ['configuration'], 'bidirectional', required=False)
                self.setp(name, ['input parameter'], 'coupling coefficient')
                self.setp(name, ['insertion loss'], y_loss, required=False)
                # The output combiner stays at 50:50. A fabrication error
                # affects both Y branches in a real device, but the Python
                # model puts the whole split error at the input, and the two
                # halves of the toolkit agreeing matters more here than the
                # second decimal place of the extinction ratio.
                t = (1.0 - rho) if name == 'SPLT_1' else 0.5
                self.setp(name, ['coupling coefficient 1'], t)
                self.setp(name, ['coupling coefficient 2'], t, required=False)
                self.setp(name, ['phase shift'], 0.0, required=False)
            if abs(rho - 0.5) > 1e-9:
                self.log(f"  SPLT_1: Y branch, {100*rho:.1f}:{100*(1-rho):.1f} "
                         f"power split (coupling coefficient {1-rho:.4f}).")
            if y_loss > 0:
                self.log(f"  Y branches: {y_loss:.2f} dB excess loss each "
                         f"({2*y_loss:.2f} dB on the link).")
            self._set_split_ports(True)
            return True
        except Exception as exc:
            self.log(f"  Waveguide Y Branch not available ({exc}); "
                     f"falling back to the Optical Splitter.")

        self.add(['Optical Splitter', 'Optical Splitter/Coupler'], 'SPLT_1', 280, 195)
        self.setp('SPLT_1', ['configuration'], 'splitter', required=False)
        self.setp('SPLT_1', ['number of ports', 'number of output ports'], 2,
                  required=False)
        self.setp('SPLT_1', ['split ratio'], 'even')
        self.add(['Optical Combiner', 'Optical Splitter/Coupler', 'Optical Splitter'],
                 'SPLT_2', 780, 210)
        self.setp('SPLT_2', ['configuration'], 'combiner', required=False)
        self.setp('SPLT_2', ['number of ports', 'number of input ports'], 2,
                  required=False)
        self.setp('SPLT_2', ['split ratio'], 'even')
        self._set_split_ports(False)
        if y_loss > 0:
            self.log(f"  NOTE: the Optical Splitter has no insertion-loss "
                     f"property, so the {y_loss:.2f} dB per Y branch is NOT in "
                     f"this schematic (it is in the Python eye). It is "
                     f"common-mode, so the ER and the bandwidth still agree; "
                     f"only the absolute received power differs, by "
                     f"{2*y_loss:.2f} dB.")
        return False

    def _set_split_ports(self, y: bool):
        """Which port names the splitter and combiner answer to."""
        if y:
            self.p_split_in, self.p_split_a, self.p_split_b = P_Y1, P_Y2, P_Y3
            self.p_comb_out, self.p_comb_a, self.p_comb_b = P_Y1, P_Y2, P_Y3
        else:
            self.p_split_in, self.p_split_a, self.p_split_b = P_IN, P_OUT1, P_OUT2
            self.p_comb_out, self.p_comb_a, self.p_comb_b = P_COMB_OUT, P_IN1, P_IN2

    def _add_ena(self, p: dict):
        self.add(['Network Analyzer'], 'ENA_1', 340, -350)
        # The TL line build reads the far-end voltage on input 2 (and, when
        # diagnosing, the first modulation voltage on input 3). The port count
        # is set here, before anything is wired: changing it rebuilds the
        # analyser's ports, which drops a link already made (the first Step 1
        # run lost the photodetector on input 1 that way: a flat EO trace).
        self.ena_inputs = 1
        if uses_tl_line(p):
            want = 3 if self.diagnose else 2
            if self.setp('ENA_1', ['number of input ports', 'number of inputs',
                                   'input ports'], want, required=False):
                self.ena_inputs = want
        self.setp('ENA_1', ['analysis type'], 'impulse response')
        self.setp('ENA_1', ['signal source', 'source'], 'internal', required=False)
        self.setp('ENA_1', ['source kind', 'kind'], 'power', required=False)
        self.setp('ENA_1', ['power', 'source power'], 0.001, required=False)
        self.setp('ENA_1', ['input parameter'], 'start and stop', required=False)
        self.setp('ENA_1', ['start frequency'], 0, required=False)
        self.setp('ENA_1', ['stop frequency'], float(p["f_max_GHz"]) * 1e9, required=False)
        self.setp('ENA_1', ['number of points', 'number of frequency points'],
                  int(p["ic_ena_points"]), required=False)
        self.setp('ENA_1', ['remove dc', 'remove DC'], True, required=False)
        self.setp('ENA_1', ['peak analysis', 'peak_analysis'], 'disable', required=False)

        # Impulse-response analysis is a time-domain method, so the sweep
        # ceiling has to stay well inside the Nyquist frequency of the circuit
        # sample rate or the top of the band is reconstructed from too few
        # samples per cycle and rolls off for numerical rather than physical
        # reasons. Half the sample rate is the hard limit; 40 % is a working one.
        f_nyq = 0.5 * float(p["ic_sample_rate_GHz"])
        if float(p["f_max_GHz"]) > 0.8 * f_nyq:
            self.log(f"  WARNING: sweep ceiling {float(p['f_max_GHz']):.0f} GHz is "
                     f"{100*float(p['f_max_GHz'])/f_nyq:.0f} % of the Nyquist "
                     f"frequency ({f_nyq:.0f} GHz at a {float(p['ic_sample_rate_GHz']):.0f} "
                     f"GHz sample rate). Raise the sample rate to at least "
                     f"{2.5*float(p['f_max_GHz']):.0f} GHz or the top of the "
                     f"INTERCONNECT trace is a sampling artifact, not physics.")

    def _add_eye_chain(self, p: dict):
        """
        PRBS -> NRZ -> (electrode) and photodiode -> eye analyser.

        Port and property names here follow the element reference rather than
        the pattern the rest of the schematic uses, because these three
        elements do not follow it:

          PRBS  one port, 'output'; property is 'bitrate', one word
          NRZ   input port is 'modulation' (it takes a *digital* signal), and
                the edge rates are 'rise period'/'fall period', expressed as a
                fraction of the bit period, not as times
          EYE   ports 'input' and an optional 'reference'; 'number of levels'
                is what makes it read a PAM eye rather than a binary one

        The NRZ generator has no bitrate of its own: it takes the rate from
        the digital signal arriving at 'modulation', which is why the rate is
        set on the root element and on PRBS_1 and nowhere else.
        """
        levels = 4 if str(p["mod_format"]).upper() == "PAM4" else 2
        sym_rate = float(p["bitrate_Gbps"]) / (1 if levels == 2 else 2)
        rate_Hz = sym_rate * 1e9
        n_bits = (1 << int(p["prbs_order"])) - 1

        if not self._set_root("bitrate", rate_Hz):
            self.log("  Root 'bitrate' not settable; each element carries its own.")

        self.add(['PRBS Generator'], 'PRBS_1', 115, -120)
        self.setp('PRBS_1', ['bitrate', 'bit rate'], rate_Hz, required=False)
        self.setp('PRBS_1', ['order'], int(p["prbs_order"]), required=False)
        self.setp('PRBS_1', ['automatic seed'], False, required=False)
        # A whole PRBS period, so the pattern closes on itself and the eye is
        # not a partial sample of it.
        self.setp('PRBS_1', ['time window'], n_bits / rate_Hz, required=False)
        self._set_root("time window", n_bits / rate_Hz)

        vpp = float(p["drive_Vpp_V"])
        drive_bw = float(p["drive_bw_GHz"]) or 0.7 * sym_rate
        # 10-90 % rise expressed as a fraction of the bit period. A 4th-order
        # Bessel of bandwidth B has a 10-90 % rise of about 0.35/B, and the
        # Python eye uses exactly that bandwidth, so the two drivers match.
        rise_frac = min(0.9, max(0.05, 0.35 * sym_rate / drive_bw))

        self.add(['NRZ Pulse Generator'], 'NRZ_1', 265, -120)
        self.setp('NRZ_1', ['amplitude'], vpp, required=False)
        self.setp('NRZ_1', ['bias'], -vpp / 2.0, required=False)
        self.setp('NRZ_1', ['rise period'], rise_frac, required=False)
        self.setp('NRZ_1', ['fall period'], rise_frac, required=False)
        self.connect('PRBS_1', P_OUT, 'NRZ_1', P_DIGI_IN)

        self.add(['Eye Diagram'], 'EYE_1', 1100, 210)
        self.setp('EYE_1', ['bitrate', 'bit rate'], rate_Hz, required=False)
        self.setp('EYE_1', ['number of levels'], levels, required=False)
        self.setp('EYE_1', ['eye period'], 2, required=False)
        self.setp('EYE_1', ['ignore start periods'], 4, required=False)
        self.setp('EYE_1', ['calculate measurements'], True, required=False)

        if levels == 4:
            self.log("  NOTE: the eye analyser is set to 4 levels, but PRBS_1 "
                     "and NRZ_1 produce a two-level drive. A real PAM4 drive "
                     "needs a 4-level coder between them; the Python eye does "
                     "model PAM4 properly.")
        self.log(f"  Eye drive: PRBS-{int(p['prbs_order'])} at {sym_rate:.1f} GBd, "
                 f"{vpp:.2f} Vpp centred on the bias point, rise/fall "
                 f"{rise_frac:.2f} of a bit period.")

    def _wire_eye_reference(self, p: dict):
        """
        Connect the eye analyser's timing reference.

        The 'reference' port is not optional in practice. Its documented job is
        "automatic delay compensation of the input signal": it is what tells
        the element where the bit boundaries are, so with nothing connected to
        it the element has no timing to fold the received waveform against and
        produces no eye and no results -- not merely a BER of zero.

        The reference is the electrical drive from NRZ_1, which is what the
        Ansys transceiver examples use. If this build will not fan the NRZ
        output out to both the electrode and the analyser, a second PRBS/NRZ
        pair with the same order and the same fixed seed emits an identical
        waveform, which is the trick the Ansys differential-drive note uses for
        the same reason.

        The element also has a 'bit pattern input' port, off by default, which
        takes the transmitted bits directly and makes the measured BER exact.
        It is deliberately left off: the tutorials do not use it, it needs a
        second fan-out of its own, and an enabled port with nothing plugged
        into it is worse than no port.
        """
        self.setp('EYE_1', ['bit pattern input'], False, required=False)
        self.setp('EYE_1', ['signal reference input'], True, required=False)

        if self._try_connect_any('NRZ_1', P_OUT, 'EYE_1', P_EYE_REF):
            self.log("  EYE_1 reference: the electrical drive from NRZ_1.")
            self._warn_if_inverted(p)
            return

        # The fan-out was refused. Duplicate the generator instead.
        try:
            levels = 4 if str(p["mod_format"]).upper() == "PAM4" else 2
            rate_Hz = float(p["bitrate_Gbps"]) * 1e9 / (1 if levels == 2 else 2)
            vpp = float(p["drive_Vpp_V"])
            for el, props in (('PRBS_1', None), ('PRBS_2', True)):
                if props:
                    self.add(['PRBS Generator'], 'PRBS_2', 115, 60)
                    self.setp('PRBS_2', ['bitrate', 'bit rate'], rate_Hz,
                              required=False)
                    self.setp('PRBS_2', ['order'], int(p["prbs_order"]),
                              required=False)
                self.setp(el, ['automatic seed'], False, required=False)
                self.setp(el, ['seed'], 1, required=False)

            self.add(['NRZ Pulse Generator'], 'NRZ_2', 265, 60)
            for k, v in (('amplitude', vpp), ('bias', -vpp / 2.0)):
                self.setp('NRZ_2', [k], v, required=False)
            drive_bw = float(p["drive_bw_GHz"]) or 0.7 * (rate_Hz / 1e9)
            rise_frac = min(0.9, max(0.05, 0.35 * (rate_Hz / 1e9) / drive_bw))
            for k in ('rise period', 'fall period'):
                self.setp('NRZ_2', [k], rise_frac, required=False)
            self.connect('PRBS_2', P_OUT, 'NRZ_2', P_DIGI_IN)
            self.connect('NRZ_2', P_OUT, 'EYE_1', P_EYE_REF)
            self.log("  EYE_1 reference: a duplicate PRBS/NRZ pair with the "
                     "same order and seed, because this build would not fan "
                     "the NRZ output out to two destinations.")
            self._warn_if_inverted(p)
            return
        except Exception as exc:
            self.log(f"  duplicate drive chain not available ({exc}).")

        self.log("  WARNING: EYE_1 has no reference, so it has no timing to "
                 "fold the waveform against and will produce no eye and no "
                 "results. Connect NRZ_1's output to EYE_1's 'reference' port "
                 "by hand in the schematic.")

    def _check_eye_wiring(self):
        """
        Confirm the eye analyser has both of the links it cannot work without,
        rather than trusting that every connect call did what it said.

        EYE_1 needs the detected waveform on 'input' and a timing reference on
        'reference'. Missing either, it produces nothing at all, and finding
        that out from an empty results window is a poor way to learn it.
        """
        have = {w.split(' -> ')[1].split(':')[1] for w in self._wiring
                if w.split(' -> ')[1].startswith('EYE_1:')}
        missing = [n for n, ports in (("detected signal", P_IN),
                                      ("timing reference", P_EYE_REF))
                   if not have & set(ports)]
        if missing:
            self.log(f"  WARNING: EYE_1 is missing its {' and its '.join(missing)}. "
                     f"It has: {', '.join(sorted(have)) or 'nothing'}. The eye "
                     f"will not compute.")
        else:
            self.log(f"  EYE_1 wired: {', '.join(sorted(have))}.")

    def _try_connect_any(self, a, ports_a, b, ports_b) -> bool:
        """connect(), but a refusal is an answer rather than an error."""
        try:
            return self.connect(a, ports_a, b, ports_b, required=False) is not None
        except Exception:
            return False

    def _warn_if_inverted(self, p: dict):
        """
        Say so when a transmitted '1' will come out as the LOW optical level.

        Given a reference, the eye labels levels by the bit that produced them
        rather than by power order, so an MZM biased on the falling side of its
        transfer curve legitimately decodes level one below level zero. The
        element then reports things like "level zero mean greater than level
        one mean" and "eye considered closed", which look like failures and are
        not. The sign is known in advance -- dP/dv at the bias -- so there is no
        reason to be surprised by it.
        """
        from .physics import arm_models
        arm1, arm2 = arm_models(p)
        slope = 2 * arm1.a * arm2.a * np.sin(arm2.phi0 - arm1.phi0) \
            * (arm1.g - arm2.g)
        full = 2 * arm1.a * arm2.a * abs(arm1.g - arm2.g)
        if full > 0 and abs(slope) < 1e-3 * full:
            self.log("  WARNING: this bias sits at a turning point of the "
                     "transfer curve (dP/dV = 0), so there is no small-signal "
                     "modulation at all -- the output responds at twice the "
                     "drive frequency instead. The eye and the EO bandwidth "
                     "are both meaningless here. Quadrature is 90 deg.")
        elif slope < 0:
            self.log("  NOTE: at this bias a '1' bit produces the LOW optical "
                     "level (dP/dV < 0). With a reference connected the eye "
                     "labels levels by the transmitted bit, so it will report "
                     "level zero above level one and may call the eye closed. "
                     "That is the labelling, not the device. Add 180 deg to the "
                     "bias to flip it.")

    def _set_root(self, prop, value) -> bool:
        """Set a root-element property, whichever way this build spells it."""
        for attempt in (lambda: self.sim.setnamed("::Root Element::", prop, value),
                        lambda: self.sim.set(prop, value)):
            try:
                attempt()
                return True
            except Exception:
                continue
        return False

    def _wire_arms(self, p, pushpull, lumped_pp, add_modulator, c1, c2, L_OM) -> str:
        """Wire the interferometer and report the topology actually built."""
        if pushpull:
            add_modulator('OM_1', 560, 120, c1)
            add_modulator('OM_2', 560, 300, c2)
            self.connect('SPLT_1', self.p_split_a, 'OM_1', P_BI1)
            self.connect('OM_1', P_BI2, 'SPLT_2', self.p_comb_a)
            self.connect('SPLT_1', self.p_split_b, 'OM_2', P_BI1)
            self.connect('OM_2', P_BI2, 'PHS_1', P_BI1)
            tail, tail_port = self._wire_arm2_tail()
            self.connect(tail, tail_port, 'SPLT_2', self.p_comb_b)

            # One electrode per arm; the drive fans out to both electrodes
            # (see _drive_electrodes), so each OM has a private modulation port.
            self.connect('TW_1', P_OUT, 'OM_1', P_MOD)
            self.connect('TW_2', P_OUT, 'OM_2', P_MOD)
            self.log("  Topology: TRUE PUSH-PULL -- two electrodes, one per arm, "
                     "same drive, opposite-sign phase coefficients, per-arm n_g.")
            return "push-pull"

        c_drive = (c1 - c2) if lumped_pp else c1
        add_modulator('OM_1', 560, 120, c_drive)
        self.connect('SPLT_1', self.p_split_a, 'OM_1', P_BI1)
        self.connect('OM_1', P_BI2, 'SPLT_2', self.p_comb_a)
        self.connect('SPLT_1', self.p_split_b, 'PHS_1', P_BI1)
        tail, tail_port = self._wire_arm2_tail()
        self.connect(tail, tail_port, 'SPLT_2', self.p_comb_b)
        self.connect('TW_1', P_OUT, 'OM_1', P_MOD)

        if lumped_pp:
            vpi_eff = np.pi / (abs(c_drive) * L_OM)
            self.log(f"  Topology: LUMPED PUSH-PULL EQUIVALENT -- one modulator with "
                     f"c = {c_drive:.4g} (= |c1|+|c2|). Same EO |S21| and same "
                     f"effective V_pi ({vpi_eff:.3f} V); chirp is NOT modelled.")
            return "push-pull (lumped equivalent)"

        self.log("  Topology: SINGLE-ARM drive (one modulated arm, static phase in "
                 "the other). Chirp parameter = 1, V_pi is the full single-arm V_pi.")
        return "single-arm"

    @staticmethod
    def _bend_positions(n_sec: int) -> dict:
        """
        Non-overlapping grid for a bent electrode, one column per section:

            drive row      PRBS  NRZ    SPAR_1        SPAR_2 ...
            arm-1 TW row          TW_1_1        TW_1_2 ...
            arm-1 optics          OM_1_1  ODL   OM_1_2 ...
            centre line    CWL  SPLT_1          ...        SPLT_2  PIN  EYE
            arm-2 optics          OM_2_1  ODL   OM_2_2 ...  PHS  ATT
            arm-2 TW row          TW_2_1        TW_2_2 ...

        Rows are 150-180 apart and columns 300 apart, leaving room for each
        element's property annotations underneath it.
        """
        Y = dict(drive=-330, tw1=-150, opt1=30, mid=180, opt2=330, tw2=510)
        x0, pitch = 520, 300
        xs = [x0 + k * pitch for k in range(n_sec)]
        x_end = xs[-1]
        pos = {"PRBS_1": (100, Y["drive"]), "NRZ_1": (260, Y["drive"]),
               "ENA_1": (260, Y["drive"]),
               "CWL_1": (100, Y["mid"]), "SPLT_1": (280, Y["mid"]),
               "PHS_1": (x_end + 150, Y["opt2"]), "ATT_1": (x_end + 270, Y["opt2"]),
               "SPLT_2": (x_end + 400, Y["mid"]), "PIN_1": (x_end + 560, Y["mid"]),
               "EYE_1": (x_end + 720, Y["mid"]),
               "PRBS_2": (x_end + 560, Y["drive"]), "NRZ_2": (x_end + 720, Y["drive"])}
        for k, x in enumerate(xs, start=1):
            for arm, (ro, rt) in ((1, ("opt1", "tw1")), (2, ("opt2", "tw2"))):
                pos[f"OM_{arm}_{k}"] = (x, Y[ro])
                pos[f"TW_{arm}_{k}"] = (x - 110, Y[rt])
                if k < n_sec:
                    # left of the next section's TW column, so the vertical
                    # drive wire to the arm-2 electrode runs between blocks
                    pos[f"ODL_{arm}_{k}"] = (x + 100, Y[ro])
            pos[f"SPAR_{k}"] = (x - 110, Y["drive"])
        return pos

    def _wire_arms_bends(self, p, files, pushpull, add_modulator, c1, c2, ng1, ng2) -> str:
        """
        Segmented electrode: per arm, one TW + OM per modulating section, the
        OMs joined optically by Optical Delays (the light's transit through the
        bend and the next section), and per section a shared Electrical N Port
        S-Parameter (S21 = V_th/V_s, RF transit included; a flat 1 for the
        first section) giving that section its Thevenin drive. Every drive
        path is the same kind of filter, so INTERCONNECT's processing latency
        is common to all sections and cancels. The bends themselves are not elements:
        their impedance, loss and delay are carried by the sections' source /
        terminating impedance tables and by the drive chains, which is what
        makes this exact while every section keeps the fitted line tables.

        The TW output is referenced to the light LEAVING its section (the
        Xu et al. form INTERCONNECT cites, which is also eo_transfer's), so each
        OM stands at its section's exit and the delay between two OMs is
        n_g (bend optical length + next section length) / c.
        """
        secs = self.bend_sections
        L_mod = sum(s["L_m"] for s in secs) or 1.0
        arms = [(1, c1, ng1)] + ([(2, c2, ng2)] if pushpull else [])
        self.tw_names, self.drive_chains = [], []
        dx = 230
        for arm, c, ng_a in arms:
            y_opt = 120 if arm == 1 else 300
            y_tw = -45 if arm == 1 else 465
            prev = None
            for s in secs:
                k = s["k"]
                x = 560 + (k - 1) * dx
                om, tw = f"OM_{arm}_{k}", f"TW_{arm}_{k}"
                add_modulator(om, x, y_opt, c * s["L_m"] / L_mod)
                self._add_tw(tw, p, files, ng_a, x - 140, y_tw, length_m=s["L_m"],
                             zsrc=s["zsrc"], zload=s["zload"])
                self._fix_filter(tw)
                self.tw_names.append(tw)
                self.connect(tw, P_OUT, om, P_MOD)
                if prev is None:
                    self.connect('SPLT_1', self.p_split_a if arm == 1 else self.p_split_b,
                                 om, P_BI1)
                else:
                    dl = f"ODL_{arm}_{k - 1}"
                    self.add(['Optical Delay'], dl, x - 115, y_opt)
                    self.setp(dl, ['delay'], ng_a * (s["bend_opt_m"] + s["L_m"]) / C0)
                    self.connect(prev, P_BI2, dl, P_BI1)
                    self.connect(dl, P_BI2, om, P_BI1)
                prev = om
            if arm == 1:
                self.connect(prev, P_BI2, 'SPLT_2', self.p_comb_a)
            else:
                self.connect(prev, P_BI2, 'PHS_1', P_BI1)
                tail, tail_port = self._wire_arm2_tail()
                self.connect(tail, tail_port, 'SPLT_2', self.p_comb_b)
        if not pushpull:
            self.connect('SPLT_1', self.p_split_b, 'PHS_1', P_BI1)
            tail, tail_port = self._wire_arm2_tail()
            self.connect(tail, tail_port, 'SPLT_2', self.p_comb_b)

        for s in secs:
            k = s["k"]
            spar = f"SPAR_{k}"
            self.add(['Electrical N Port S-Parameter', 'Electrical S Parameter'],
                     spar, 200 + k * 120, -330)
            self.setp(spar, ['load from file'], True)
            self.setp(spar, ['s parameters filename'], s["spar"])
            self.setp(spar, ['s parameters convention'], 'engineering', required=False)
            self._fix_filter(spar)
            self.drive_chains.append((k, spar))
        nb = len(secs) - 1
        lens = " + ".join("%.2f" % (s["L_m"] * 1e3) for s in secs)
        kind = "PUSH-PULL" if pushpull else "SINGLE-ARM"
        self.log(f"  Topology: {kind} with {nb} bend(s): {len(secs)} electrodes per arm "
                 f"(TW_<arm>_<electrode> + OM, {lens} mm), {nb} optical delay(s) per arm, "
                 f"one drive S-parameter per electrode (SPAR_k = voltage reaching electrode k).")
        return ("push-pull" if pushpull else "single-arm") + f", {nb} bend(s)"

    # ---------------- electrode model "TL line" -------------------------
    @classmethod
    def _tl_positions(cls, n_sec: int) -> dict:
        """The bent-electrode grid, with the TL chain on the arm-1 electrode
        row: SRC, then EL_k under each section's OMs and BEND_k between them,
        then LOAD. createcompound later puts the Compound at their centroid."""
        pos = cls._bend_positions(n_sec)
        x0, pitch, y = 520, 300, -150
        pos["SRC"] = (x0 - 260, y)
        for k in range(1, n_sec + 1):
            pos[f"EL_{k}"] = (x0 + (k - 1) * pitch - 110, y)
            if k < n_sec:
                pos[f"BEND_{k}"] = (x0 + (k - 1) * pitch + 40, y)
        pos["LOAD"] = (x0 + (n_sec - 1) * pitch + 60, y)
        pos["EYE_2"] = (x0 + n_sec * pitch + 420, -150)
        return pos

    def _wire_arms_tl(self, p, pushpull, add_modulator, c1, c2, ng1, ng2) -> str:
        """
        The optical half of the TL line build: per arm, one OM per modulating
        section with the coefficient c L_k / L_mod, joined by Optical Delays of
        n_g (optical length of the bends before the next section + that
        section) / c. The TL line's modulation output is referenced to the
        light LEAVING its section, like the TW block's, so each OM stands at
        its section's exit, as in the TW build with bends.

        Records in self.tl_outputs which element output drives which OM:
        arm 1 takes 'modulation' (n_g1), arm 2 'modulation 2' (n_g2).
        """
        lay = electrode_layout(p)
        L_mod = sum(x["L_rf"] for x in lay if x["kind"] == "mod") or 1.0
        arms = [(1, c1, ng1)] + ([(2, c2, ng2)] if pushpull else [])
        self.tl_outputs = []
        for arm, c, ng_a in arms:
            y_opt = 120 if arm == 1 else 300
            prev, gap, k = None, 0.0, 0
            for x in lay:
                if x["kind"] != "mod":
                    gap += x["L_opt"]
                    continue
                k += 1
                om = f"OM_{arm}_{k}"
                add_modulator(om, 560 + (k - 1) * 230, y_opt, c * x["L_rf"] / L_mod)
                self.tl_outputs.append(
                    (f"EL_{k}", "modulation" if arm == 1 else "modulation 2", om))
                if prev is None:
                    self.connect('SPLT_1', self.p_split_a if arm == 1 else self.p_split_b,
                                 om, P_BI1)
                else:
                    dl = f"ODL_{arm}_{k - 1}"
                    self.add(['Optical Delay'], dl, 445 + (k - 1) * 230, y_opt)
                    self.setp(dl, ['delay'], ng_a * (gap + x["L_opt"]) / C0)
                    self.connect(prev, P_BI2, dl, P_BI1)
                    self.connect(dl, P_BI2, om, P_BI1)
                prev, gap = om, 0.0
            if arm == 1:
                self.connect(prev, P_BI2, 'SPLT_2', self.p_comb_a)
            else:
                self.connect(prev, P_BI2, 'PHS_1', P_BI1)
                tail, tail_port = self._wire_arm2_tail()
                self.connect(tail, tail_port, 'SPLT_2', self.p_comb_b)
        if not pushpull:
            self.connect('SPLT_1', self.p_split_b, 'PHS_1', P_BI1)
            tail, tail_port = self._wire_arm2_tail()
            self.connect(tail, tail_port, 'SPLT_2', self.p_comb_b)
        n_sec = sum(1 for x in lay if x["kind"] == "mod")
        nb = n_sec - 1
        kind = "PUSH-PULL" if pushpull else "SINGLE-ARM"
        self.log(f"  Topology: {kind}, electrode model TL line: {n_sec} electrode section(s)"
                 + (f" and {nb} bend(s)" if nb else "") + ", one modulator per section per "
                 f"arm (n_g {ng1:.5f}" + (f" / {ng2:.5f}" if pushpull else "") + ").")
        return ("push-pull" if pushpull else "single-arm") + \
            (f", {nb} bend(s)" if nb else "") + ", TL line"

    COMPOUND = "ELECTRODE"

    def _build_tl_electrode(self, p, files, drive: str, pushpull: bool, mode: str):
        """
        The electrical half of the TL line build, as one Compound:

            drive -> SRC (Zs) -> EL_1 -> BEND_1 -> EL_2 -> ... -> EL_N -> LOAD (Rt)

        Built at root level and wired first (so the drive link enters the
        selection and createcompound keeps it), then grouped; every
        modulation output and the far-end output become Output ports of the
        Compound, wired to their OMs and to the far-end reader.
        """
        tl = files["tl"]
        meta, d = tl["meta"], os.path.dirname(tl["json"])
        top_Hz = float(meta["table_top_GHz"]) * 1e9
        n_freq = max(201, int(float(meta["table_top_GHz"]) * 4) + 1)
        lib = str(p.get("tl_library_name", "")).strip() or None
        els = meta["elements"]

        self.make_source("SRC", 260, -150, float(p["Zs_R"]), float(p["Zs_L_pH"]) * 1e-12,
                         float(p["Zs_C_fF"]) * 1e-15, top_Hz, n_freq)
        names = ["SRC"]
        for i, e in enumerate(els):
            mod = bool(e["modulating"])
            self.make_tl(e["name"], 400, -150, os.path.join(d, e["table"]),
                         float(e["line_length"]), float(e["ng"]), modulating=mod,
                         far_end=(i == len(els) - 1), library_name=lib,
                         fir_taps=self.BEND_FIR_TAPS,
                         ng2=float(e["ng2"]) if (mod and pushpull) else None)
            names.append(e["name"])
        self.make_load("LOAD", 900, -150, float(p["Rt_R"]), float(p["Rt_L_pH"]) * 1e-12,
                       float(p["Rt_C_fF"]) * 1e-15, top_Hz, n_freq)
        names.append("LOAD")
        self.connect(drive, P_OUT, "SRC", ['port 1'])
        for a, b in zip(names[:-1], names[1:]):
            self.connect(a, ['port 2'], b, ['port 1'])

        outputs = [(el, port, f"to {om}", om, P_MOD) for el, port, om in self.tl_outputs]
        last = els[-1]["name"]
        if mode == "eye":
            self._add_far_end_eye(p)
            outputs.append((last, "far end", "far end", "EYE_2", P_IN))
            self.far_end = "EYE_2"
        else:
            if self.ena_inputs >= 2:
                outputs.append((last, "far end", "far end", "ENA_1", ["input 2"]))
                self.far_end = "ENA_1 input 2"
            else:
                # The output still has to end on a relay: an output left
                # dangling inside the Compound makes its solver refuse it.
                outputs.append((last, "far end", "far end", None, None))
                self.log("  ENA_1 takes only one input in this build: the far-end "
                         "voltage is a Compound output with nothing connected.")
        if not self.make_compound(self.COMPOUND, names, outputs):
            raise RuntimeError("the electrode Compound could not be made or its "
                               "'scattering data analysis' could not be switched on")
        if mode != "eye":
            # The photodetector link is the one the port-count change used to
            # drop; make sure it is there (a duplicate is refused, harmlessly).
            pin = next((w.split(" -> ")[0].split(":", 1)[1] for w in self._wiring
                        if w.startswith("PIN_1:") and "ENA_1:" in w), P_OUT[0])
            if self._try_connect('PIN_1', pin, 'ENA_1', 'input 1'):
                self.log("  ENA_1 input 1 was not connected to PIN_1; reconnected.")
            if self.diagnose:
                probe = self.tl_outputs[0]
                if self.ena_inputs >= 3 and self.connect(
                        self.COMPOUND, [f"to {probe[2]}"], 'ENA_1', ['input 3'],
                        required=False) is not None:
                    self.log(f"  Diagnosis: ENA_1 input 3 reads {probe[0]} '{probe[1]}' "
                             f"(the voltage driving {probe[2]}), fanned out from the "
                             f"Compound port.")
                else:
                    self.log("  Diagnosis: the modulation voltage could not be routed to "
                             "ENA_1 input 3 (no third input, or no fan-out).")
        taps = self.setp(self.COMPOUND, ['number of fir taps'], self.BEND_FIR_TAPS,
                         required=False)
        if taps:
            self._fix_filter(self.COMPOUND)
        self.log(f"  {self.COMPOUND}: {len(names)} elements (" + " -> ".join(names) + "), "
                 f"{len(outputs)} outputs, scattering data analysis on; Compound filter "
                 + (f"{self.BEND_FIR_TAPS} taps." if taps else
                    "left at INTERCONNECT's default (no tap property on the Compound)."))
        lc = [k for k in ("Zs_L_pH", "Zs_C_fF", "Rt_L_pH", "Rt_C_fF") if float(p[k]) != 0]
        if lc:
            self.log(f"  Source and termination carry their full frequency dependence "
                     f"({', '.join(lc)}), not the value at one frequency.")
        if self.pending_manual:
            for m in self.pending_manual:
                self.log(f"  MANUAL WIRE NEEDED: {m}")

    def _add_far_end_eye(self, p: dict):
        """An electrical eye on the voltage across the termination, with the
        same symbol settings as EYE_1."""
        levels = 4 if str(p["mod_format"]).upper() == "PAM4" else 2
        rate_Hz = float(p["bitrate_Gbps"]) * 1e9 / (1 if levels == 2 else 2)
        self.add(['Eye Diagram'], 'EYE_2', 1100, -150)
        self.setp('EYE_2', ['bitrate', 'bit rate'], rate_Hz, required=False)
        self.setp('EYE_2', ['number of levels'], levels, required=False)
        self.setp('EYE_2', ['eye period'], 2, required=False)
        self.setp('EYE_2', ['ignore start periods'], 4, required=False)
        self.setp('EYE_2', ['calculate measurements'], True, required=False)
        self.setp('EYE_2', ['bit pattern input'], False, required=False)
        self.setp('EYE_2', ['signal reference input'], True, required=False)

    def _wire_far_end_eye_reference(self):
        src = 'NRZ_2' if any(w.startswith('NRZ_2:') for w in self._wiring) else 'NRZ_1'
        if self._try_connect_any(src, P_OUT, 'EYE_2', P_EYE_REF):
            self.log(f"  EYE_2 (voltage across the termination) reference: {src}.")
        else:
            self.log(f"  WARNING: EYE_2 has no timing reference ({src} would not fan out "
                     f"once more). Connect {src}'s output to EYE_2 'reference' by hand.")

    # The Network Analyzer's output stands for half the source EMF (Step 0:
    # every row read 2x the model with EMF = 1), so V/EMF = (ENA ratio) / 2.
    ENA_EMF_FACTOR = 0.5

    def far_end_trace(self):
        """(f_GHz, V_termination / EMF) from ENA_1 input 2, or None if the far
        end is not read by the analyser in this build."""
        if self.far_end != "ENA_1 input 2":
            return None
        f, H, _c, _l = self.complex_trace('ENA_1', input_port=2)
        return f, H * self.ENA_EMF_FACTOR

    # Same digital-filter size for every table-driven element of a bent
    # electrode. INTERCONNECT turns each into an FIR filter; if their lengths
    # (and so any processing latency) differ, the sections are summed out of
    # step, which shows up as flat half-power traces across the eye.
    BEND_FIR_TAPS = 1024

    def _fix_filter(self, el):
        self.setp(el, ['digital filter type'], 'FIR', required=False)
        self.setp(el, ['number of taps estimation'], 'disabled', required=False)
        self.setp(el, ['number of fir taps'], self.BEND_FIR_TAPS, required=False)
        self.setp(el, ['maximum number of fir taps'], max(4096, self.BEND_FIR_TAPS),
                  required=False)
        self.setp(el, ['single tap filter'], False, required=False)

    def _drive_electrodes(self, src: str):
        """Feed the drive signal to every electrode. With two electrodes the
        source output fans out; that is the one step a build can refuse."""
        if getattr(self, "bend_sections", None):
            src_out = None
            for k, spar in self.drive_chains:
                if src_out is None:
                    src_out, _ = self.connect(src, P_OUT, spar, P_SPAR1)
                elif not self._try_connect_any(src, [src_out], spar, P_SPAR1):
                    raise _FanOutUnsupported(f"{src} cannot also drive {spar}")
                tws = [tw for tw in self.tw_names if tw.endswith(f"_{k}")]
                sp_out, tw_in = self.connect(spar, P_SPAR2, tws[0], P_IN)
                for tw in tws[1:]:
                    if not self._try_connect(spar, sp_out, tw, tw_in):
                        raise _FanOutUnsupported(f"{spar} cannot drive a second electrode")
            return
        src_out, tw_in = self.connect(src, P_OUT, self.tw_names[0], P_IN)
        for tw in self.tw_names[1:]:
            if not self._try_connect(src, src_out, tw, tw_in):
                raise _FanOutUnsupported(
                    f"{src} cannot drive a second electrode ({tw})")

    def _wire_arm2_tail(self):
        """Insert the arm-2 attenuator if present; return the element and the
        port-name candidates that feed the combiner."""
        if self.has_attenuator:
            self.connect('PHS_1', P_BI2, 'ATT_1', P_IN)
            return ('ATT_1', P_OUT)
        return ('PHS_1', P_BI2)

    def dump_ena(self, path: str, element: str = 'ENA_1') -> list:
        """Every frequency-domain dataset of *element* to a CSV (result,
        dataset, f_GHz, re, im). Returns the result names."""
        import csv
        names = []
        try:
            names = [str(n) for n in self.sim.getresultnames(element)]
        except Exception:
            pass
        with open(path, "w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["result", "dataset", "f_GHz", "re", "im"])
            for n in names:
                try:
                    res = self.sim.getresult(element, n)
                except Exception:
                    continue
                for label, f, d in self._collect_datasets(res):
                    for fi, di in zip(f, d):
                        wr.writerow([n, label, f"{fi / 1e9:.6f}", f"{di.real:.9e}",
                                     f"{di.imag:.9e}"])
        return names

    # ---------------- run & read back -----------------------------------
    def run(self, save_path: Optional[str] = None):
        what = ("time-domain eye simulation" if self.mode == "eye"
                else "impulse-response sweep")
        if self.pending_manual:
            # Running with an output that reaches nothing measures nothing.
            if save_path:
                self.sim.save(save_path)
            raise ManualWiringNeeded(
                "The schematic is built but not run: " + "; ".join(self.pending_manual)
                + (f". Project saved: {save_path}" if save_path else "")
                + ". Then press Run in INTERCONNECT.")
        if save_path:
            # Saved before the run too: if INTERCONNECT crashes, the project is
            # still there to open and run by hand, with its own error message.
            self.sim.save(save_path)
        self.log(f"  Running {what} in INTERCONNECT...")
        self.sim.run()
        if save_path:
            self.sim.save(save_path)
            self.log(f"  Project saved: {save_path}")

    def close(self):
        try:
            self.sim.close()
        except Exception:
            pass

    # -- the original launcher's robust ENA dataset probing, kept verbatim
    #    in behaviour but quieter and returning data instead of printing it.
    @staticmethod
    def _collect_datasets(res, prefix=''):
        out = []
        if not isinstance(res, dict):
            return out
        f = None
        for k, v in res.items():
            if k.lower() in ('f', 'frequency', 'freq'):
                f = np.asarray(v, dtype=float).ravel()
                break
        for k, v in res.items():
            if k.lower() in ('f', 'frequency', 'freq'):
                continue
            if isinstance(v, dict):
                out += InterconnectBuilder._collect_datasets(v, prefix=f"{prefix}{k}/")
                continue
            if f is None:
                continue
            try:
                d = np.asarray(v, dtype=complex).ravel()
            except Exception:
                continue
            if d.size == f.size:
                out.append((f"{prefix}{k}", f, d))
        return out

    def ena_trace(self, p: dict, element: str = 'ENA_1', norm_window=None):
        """
        Returns (f_GHz, S21_normalised_dB, bw_GHz).

        The ENA exposes several similarly-named datasets depending on version;
        this probes all of them and picks the one that actually rolls off,
        exactly as the original launcher did.

        *norm_window* is the (f_lo, f_hi) GHz reference window the closed-form
        model used, and passing it is what makes the two numbers comparable.
        The physics on the two sides already agreed to ~1e-14 dB; what used to
        differ was only this -- the reference level and where the -3 dB search
        was allowed to start. Anchoring INTERCONNECT on f_norm_GHz while the
        model averaged a plateau shifted the reference by a few tenths of a dB,
        and on a shallow roll-off a few tenths of a dB is tens of GHz. Omitting
        it falls back to the old point-anchored behaviour.
        """
        level = float(p["bw_level_dB"])
        if norm_window is None:
            f_n = float(p["f_norm_GHz"])
            norm_window = (f_n, f_n)

        cands = []
        try:
            cands += [str(n) for n in self.sim.getresultnames(element)]
        except Exception:
            pass
        for n in KNOWN_ENA_RESULTS:
            if n not in cands:
                cands.append(n)
        # Input 2 (the TL line build's far-end voltage) is not an EO response.
        cands = [n for n in cands if not re.match(r"\s*input\s*[2-9]", n.lower())]

        rows, seen = [], set()
        for n in cands:
            try:
                res = self.sim.getresult(element, n)
            except Exception:
                continue
            for label, f, d in self._collect_datasets(res):
                if label in seen:
                    continue
                seen.add(label)
                is_real = np.allclose(d.imag, 0.0, atol=1e-12)
                interps = [('dB', d.real)] if is_real else []
                mag = np.abs(d)
                mag[mag == 0] = 1e-300
                interps.append(('lin', 20 * np.log10(mag)))
                for tag, s_dB in interps:
                    s, bw, _ref, clipped = normalise_and_measure(
                        f / 1e9, s_dB, norm_window, level)
                    rows.append({'label': f"{label} [{tag}]", 'f': f, 's': s,
                                 'bw': None if clipped else bw,
                                 'min': float(np.min(s))})

        if not rows:
            raise RuntimeError(f"No frequency-domain dataset could be read from {element}.")

        f_max_GHz = rows[0]['f'][-1] / 1e9
        crossing = [r for r in rows if r['bw'] is not None and r['bw'] < f_max_GHz - 1.0]
        best = min(crossing, key=lambda r: r['min']) if crossing else min(rows, key=lambda r: r['min'])
        self.log(f"  ENA dataset selected: {best['label']}")
        return best['f'] / 1e9, best['s'], (best['bw'] if best['bw'] else f_max_GHz)


    # -- eye read-back ------------------------------------------------
    EYE_METRICS = {
        'extinction ratio': 'er_dB',
        'eye height': 'eye_height',
        'eye opening': 'eye_opening',
        'eye amplitude': 'eye_amplitude',
        'Q factor': 'q_factor',
        'jitter': 'jitter',
        'crossing': 'crossing',
        'BER': 'ber',
    }

    def eye_metrics(self, element: str = 'EYE_1') -> dict:
        """
        Whatever scalar metrics this build's eye analyser exposes.

        Element result names move around between INTERCONNECT versions, so this
        asks the element what it has rather than assuming, and returns only what
        came back. An empty dict means the eye was drawn but no scalars could be
        read -- look at it in INTERCONNECT rather than trusting a guess.
        """
        out = {}
        try:
            names = [str(n) for n in self.sim.getresultnames(element)]
        except Exception:
            return out
        for n in names:
            key = None
            for pat, short in self.EYE_METRICS.items():
                if pat.lower() in n.lower():
                    key = short
                    break
            if key is None or key in out:
                continue
            try:
                v = self.sim.getresult(element, n)
            except Exception:
                continue
            if isinstance(v, dict):
                v = next((x for x in v.values() if np.isscalar(x)), None)
            try:
                out[key] = float(np.asarray(v).ravel()[0])
            except Exception:
                continue
        return out


# ---------------------------------------------------------------------------
# Parameters that can also be swept on the INTERCONNECT side (spot checks)
# ---------------------------------------------------------------------------
# Each entry maps a GUI value to (property candidates, value for arm 1, value
# for arm 2). The value is applied to every electrode in the schematic -- two
# in a push-pull build, one otherwise -- so the electrodes can never drift apart
# on a property they are supposed to share.
def _ng_arms(p, ng, dn):
    return ng * (1.0 + dn / 2.0), ng * (1.0 - dn / 2.0)


LUMERICAL_SWEEPABLE = {
    "Rt_R": (['terminating resistance'], lambda p, v: (float(v), float(v))),
    "Zs_R": (['source resistance'], lambda p, v: (float(v), float(v))),
    "L_target_mm": (['length'], lambda p, v: (float(v) * 1e-3,) * 2),
    "ng": (['optical index'],
           lambda p, v: _ng_arms(p, float(v), float(p.get("ng_imbalance", 0.0)))),
    "ng_imbalance": (['optical index'],
                     lambda p, v: _ng_arms(p, float(p["ng"]), float(v))),
    "Vpi_V": (None, None),     # handled by rebuilding the coefficient
}


def verify_points(builder: InterconnectBuilder, p: dict, key: str,
                  values: Sequence[float],
                  progress: Optional[Callable[[int, int, str], None]] = None,
                  norm_window=None) -> dict:
    """
    Re-run INTERCONNECT at a handful of points of an already-built schematic so
    the fast Python sweep can be spot-checked against the solver.

    Only properties that map onto an existing element property are supported;
    anything else would need a full rebuild and is better done in Python.
    """
    if key not in LUMERICAL_SWEEPABLE or LUMERICAL_SWEEPABLE[key][0] is None:
        raise ValueError(f"'{key}' cannot be re-swept in place; it needs a rebuild.")
    if getattr(builder, "electrode_model", "TW block") == "TL line":
        raise ValueError("In-place re-sweeps are available for the TW-block build only. "
                         "With the TL line, rebuild at each point.")
    if getattr(builder, "bend_sections", None):
        raise ValueError("In-place re-sweeps are not available for a bent electrode: "
                         "its source/termination live in per-section tables. Rebuild "
                         "at each point instead.")
    tws = list(getattr(builder, "tw_names", ['TW_1']))
    if key == "ng_imbalance" and len(tws) < 2:
        raise ValueError("ng_imbalance needs the two-electrode push-pull build; "
                         f"this schematic has {len(tws)} electrode.")
    props, conv = LUMERICAL_SWEEPABLE[key]
    out = {"values": list(values), "bw_GHz": []}
    for i, v in enumerate(values):
        builder.sim.switchtodesign()
        per_arm = conv(p, v)
        for tw, val in zip(tws, per_arm):
            builder.setp(tw, props, val)
        builder.run()
        _, _, bw = builder.ena_trace(p, norm_window=norm_window)
        out["bw_GHz"].append(float(bw))
        if progress:
            progress(i + 1, len(values), f"{key} = {v:g} -> {bw:.2f} GHz")
    return out


def tl_diagnosis(b: InterconnectBuilder, files: dict, p: dict, res, out_dir: str) -> str:
    """
    After a diagnostic TL line run (b.diagnose = True, ENA mode): every ENA_1
    dataset to tl_diagnosis.csv, and each input compared with its Python
    prediction -- input 1 the EO response, input 2 the voltage across the
    termination, input 3 the modulation voltage of the first section, arm 1.
    Says where the signal is lost: electrical (input 3 wrong) or optical
    (input 3 right, input 1 wrong).
    """
    from . import scripted_line as SL
    lines = ["TL line build -- diagnosis"]
    A = lines.append
    names = b.dump_ena(os.path.join(out_dir, "tl_diagnosis.csv"))
    A(f"ENA_1 results: {', '.join(names) or '(none)'}")
    A(f"wiring: {len(b._wiring)} links; inside the Compound: "
      + "; ".join(w for w in b._wiring if "RELAY" in w))
    tl = files["tl"]
    pushpull = str(p["drive_config"]) == "push-pull"
    els, opt = SL.device_chain(tl, second=pushpull)
    Zs, Zt = SL.device_terminations(tl, els[0]["f_Hz"])
    r = SL.chain_response(els, Zs, Zt, opt_lengths=opt)
    fP = r.f_Hz / 1e9
    band = (1.0, 0.95 * float(p["f_max_GHz"]))
    preds = {1: ("EO response vs Python device_response", res.f_GHz, res.H),
             2: ("voltage across the termination vs model", fP, r.far_end[-1]),
             3: ("modulation voltage EL_1 arm 1 vs model", fP, r.vavg[0])}
    A(f"{'input':6s} {'what':42s} {'scale':>8s} {'max dB':>8s} {'max deg':>8s} "
      f"{'BW ref':>8s} {'BW IC':>8s}   raw |H| dB at 1 / 20 / 50 / 90 GHz")
    for k in range(1, b.ena_inputs + 1):
        what, f_ref, H_ref = preds[k]
        try:
            f, H, cplx, label = b.complex_trace('ENA_1', input_port=k)
        except Exception as exc:
            A(f"{k:<6d} {what:42s} not readable: {exc}")
            continue
        raw = " / ".join(f"{20 * np.log10(max(abs(np.interp(x, f, np.abs(H))), 1e-300)):.2f}"
                         for x in (1, 20, 50, 90))
        try:
            c = SL.compare_traces(f_ref, H_ref, f, H, band,
                                  convention="physics" if cplx else None)
            A(f"{k:<6d} {what:42s} {c['scale_abs']:8.4f} {c['max_dB']:8.3f} "
              f"{c['max_deg'] if cplx else float('nan'):8.2f} {c['bw_ref_GHz']:8.2f} "
              f"{c['bw_test_GHz']:8.2f}   {raw}   [{label}]")
        except Exception as exc:
            A(f"{k:<6d} {what:42s} compare failed ({exc}); raw {raw} [{label}]")
    A("Reading: scale is |IC / model| at 0.5-3 GHz (2 expected for inputs 2 and 3: the "
      "ENA drives EMF/2). Input 3 right and input 1 flat -> the loss is between the "
      "Compound and the photodetector; input 3 flat too -> inside the Compound.")
    rep = "\n".join(lines)
    with open(os.path.join(out_dir, "tl_diagnosis.txt"), "w") as fh:
        fh.write(rep + "\n")
    return rep
