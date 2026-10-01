# The "TL line" scripted element

A custom INTERCONNECT element that replaces the Traveling Wave Electrode (TW)
block where a line has to be **cascaded**, for example electrode, then bend,
then electrode.

The TW block models one line between a fixed source and a fixed load. Its
output is the modulation voltage, so nothing can be connected after it on the
RF side. The TL line element is the same line with real ports at both ends.
INTERCONNECT therefore computes the reflections between it and whatever it is
connected to.

## Ports

| Port | Type | Meaning |
|---|---|---|
| `port 1` | bidirectional, electrical | input end of the line |
| `port 2` | bidirectional, electrical | far end of the line |
| `modulation` | output, electrical | electrodes only: the voltage the light integrates along the line. Same definition as the TW block's "modulation voltage". Goes to the OM `modulation` input. |
| `modulation 2` | output, electrical | optional, electrodes only: the same integral at a second group index `ng2` (arm 2 of a push-pull modulator) |
| `far end` | output, electrical | optional: the line voltage at port 2 |

A **bend** is the same element with `modulating = 0` and its own table. It then
has only ports 1 and 2.

## Properties

| Property | Meaning |
|---|---|
| `line_length` | physical length, m |
| `ng` | optical group index (electrodes) |
| `second_modulation` | 1 to have the `modulation 2` port |
| `ng2` | optical group index of `modulation 2` |
| `R0` | reference impedance of the S-matrix, 50 Ω. The same value for every element in a chain. |
| `table_file` | frequency (Hz), loss (dB/m), microwave index, Re Z0, Im Z0 |
| `modulating` | 1 electrode, 0 bend |
| `far_end_output` | 1 to have the `far end` port |
| `wave_convention` | `voltage` (default) or `power`. Step 0 tells which one INTERCONNECT uses. |
| `fir_taps` | FIR taps per entry (1024) |
| `phase_convention` | `physics` (default) or `engineering`. The maths is written for e^{+jωt}; INTERCONNECT works in e^{−iωt}, so the element writes the phases negated. Written the other way, every delay becomes an advance, and INTERCONNECT shifts each filter by half its length to make it causal. The first Step 0 run measured exactly that: 512 samples of a 1024-tap filter. |

## What it computes (`lumerical/tl_element_setup.lsf`)

The Setup script runs once when the simulation starts, inside INTERCONNECT.

1. It reads the table.
2. It computes γ = α + jωn_m/c and Γ = (Z0 − R0)/(Z0 + R0).
3. It sets the line's exact S-matrix with `setsparameter`:
   - S11 = S22 = Γ(1 − e^{−2γL}) / (1 − Γ²e^{−2γL})
   - S21 = S12 = (1 − Γ²)e^{−γL} / (1 − Γ²e^{−2γL})
4. For the `modulation` port, it computes the exact integral of the line voltage
   seen by the light for a wave entering at port 1 and for a wave entering at
   port 2. Inside the line V(z) = V⁺e^{−γz} + V⁻e^{+γz}, and the integral has a
   closed form, so there is **no slicing and no sampling error**.

The element's table depends only on the element. Changing the bend changes
only `bend_line.txt`; INTERCONNECT recomputes how the bend affects the
electrodes.

The only approximation is the one every INTERCONNECT element has in a time
domain run: the S-matrix becomes a digital filter.

## Files

| File | What it is |
|---|---|
| `mzm_interconnect/lumerical/tl_element_setup.lsf` | the Setup script of the element |
| `mzm_interconnect/lumerical/create_tl_element.lsf` | turns an empty scripted element into a TL line element: properties, ports, setup script |
| `electrode_line.txt` | electrode table. Same line data as `loss.txt` / `z0.txt` / `nm.txt`, in the format the script reads. Written up to the simulation's Nyquist frequency. |
| `bend_line.txt` | bend table: its own loss α(f), flat Z, n_b |
| `tl_elements.json` | the element list, source to load, with lengths |
| `mzm_interconnect/scripted_line.py` | the same calculation in Python, the network solve, the comparison tools |
| `mzm_interconnect/scripted_test.py` | the Step 0 build and report |

## Step 0: is it the same electrode as the TW block?

**GUI:** INTERCONNECT tab → **Step 0: TL line vs TW**. It uses the current
length, n_g, Zs and Rt, and ignores bends.

**Command line:** `python -m mzm_interconnect.cli tl-step0 your_line.s2p`

Step 0 runs as five small simulations. Each runs in a fresh INTERCONNECT
session and is saved as `TL_step0_S#.icp` **before** it runs, so a crash names
its cause and leaves a project you can open and run by hand. INTERCONNECT's own
error message then appears in its Output window.

| Stage | What runs | If it is the first to fail |
|---|---|---|
| S1 | Ansys TW block alone | the session or the Network Analyzer, not the TL line |
| S2 | TL line as a plain 2-port: ENA → SRC → TL → ENA | `setsparameter` on bidirectional electrical ports |
| S3 | TL line with its modulation output, short table (~50 points) | the Output port driven from bidirectional ports |
| S4 | same, full table, both cases | table size or FIR design |
| S5 | S4 inside a Compound with *scattering data analysis* on; a second Compound reads the far-end output (CMP_FE) | a wire inside the Compound, or the Compound's solver refusing the scripted elements |

Source and termination are scripted elements on the lines' reference R0:
`source_setup.lsf` (Zs, a two-port) and `termination_setup.lsf` (Rt, a
one-port). The Electrical Connector is not used; see the results below.

If the script cannot draw the wire inside a Compound, S5 is saved but not run.
Draw the wire from the TL line's output to the `input` pin of the relay labelled
*External Port = modulation* (or *far end*), save, and press **Step 0: run
wired S5** (CLI `tl-step0-saved`): it runs the saved project and adds its rows
to the same report.

A failed stage does not stop the next one: the Compound can work where the
flat row does not. The element tables stop at the run's Nyquist frequency.

The two cases are the GUI's Zs/Rt, and 30 Ω / 80 Ω so the reflections at both
ends are large. Each row is measured by its own Network Analyzer on the
electrode's modulation output (electrical only, no optics):

| Row | Contents |
|---|---|
| REF | Ansys TW block, same tables, Zs and Rt inside |
| FLAT | SRC (Zs) → TL line → LOAD (Rt), modulation output to the analyser |
| CMP | the FLAT row inside a Compound with *scattering data analysis* on |
| CMP_FE | the same Compound, analyser on the TL line's *far end* output (voltage across Rt), compared with the model's V(L) |

**If the build stops** saying scripted elements cannot be created from a script:

1. In the schematic: right-click → *Create scripted element*. Name it `TL_1`.
2. Open `create_tl_element.lsf`. Set the path of `tl_element_setup.lsf` in its
   first lines and run it.
3. If it says the setup script could not be set, paste
   `tl_element_setup.lsf` into the element's *Edit → Scripts → Setup*.
4. Right-click the element → add it to the Custom library, for example as
   `TL Line`.
5. In the GUI (Lumerical group), set **TL line library element** = `TL Line`,
   and press the button again.

### Reading the report (`tl_step0/step0_report.txt`)

For every row, compared with the Python model and with the REF row:

| Column | Meaning |
|---|---|
| `scale` | \|INTERCONNECT ÷ reference\| at 0.5–3 GHz. Against the model it includes the Network Analyzer's own factor (×2 in the first run, for the TW block and the TL line alike). The number that matters is the TL ÷ TW ratio (the "vs REF" rows): it should be 1. |
| `conv` | phase convention of the INTERCONNECT data; `phys` = e^{−iωt}, conjugated before comparing |
| `latency ps` | pure delay added by INTERCONNECT's digital filters, fitted and removed |
| `max dB`, `max deg` | what is left after removing scale and latency |
| `BW ref`, `BW test` | −3 dB bandwidths |

The TW block's phase reference (light leaving or entering the line) differs
from the model only by a pure delay, which is indistinguishable from filter
latency. Step 0 therefore cannot determine it; the bend build is tested
directly (unequal electrodes with a zero-length bend against a straight
electrode).

A FLAT row (outside a Compound) with a large latency cannot be right when the
line is mismatched: the latency is added on every round trip of the
reflections, which moves the ripple. That is why the Compound row is the
reference for chains.

**Pass:** CMP and CMP_FE within about 0.05 dB and 1° of the model up to the
top of the band, in both cases, and the same bandwidth to about 0.1 GHz. FLAT
rows are diagnostics; they cannot pass on a mismatched line.

### What the Step 0 runs established (Jerez line, 14 mm, 50/55 and 30/80 Ω)

1. **The element is exact.** The plain 2-port matches the model to 0.0045 dB
   and 0.005°. `setsparameter` works on bidirectional electrical ports,
   reflections included, and INTERCONNECT works in the physics convention
   e^{−iωt} (the LSF writes conjugated phases).
2. **Outside a Compound, reflections are wrong.** Every pass through an
   element's filter adds half its length (512 samples = 1365 ps for 1024 taps),
   so a reflection returns late: the FLAT/REF ratio ripples with a 1.58 ns
   period (50/55 Ω) and 2.95 ns (30/80 Ω), i.e. one or two extra filter
   passes plus the 212 ps round trip. Errors: 0.45 dB and 2.8 dB.
3. **Inside a Compound the line is solved correctly.** Latency is a single
   128 samples (341 ps). With the scripted load, 0.043 dB / 0.39° at 50/55 Ω.
4. **The Electrical Connector reflects with the opposite sign.** A
   (Zs | R0) connector behaves as a source of R0²/Zs seen from its port 2, and a
   (R0 | Rt) connector with a free port as a load of R0²/Rt. With those
   impedances the Compound rows match the model to 0.04–0.10 dB and 0.4–0.6°
   (30 Ω → 83.3 Ω, 55 Ω → 45.5 Ω, 80 Ω → 31.3 Ω). Hence the scripted source.
5. **The Network Analyzer's output is an incident wave of EMF/2** (a matched
   50 Ω source): every row, TW and TL, reads 2 × the model at low frequency.
6. **The TW block references its modulation voltage to the light entering the
   electrode** (its latency is 512 samples − n_g·L/c = 1258.8 ps); the TL line
   and the model reference it to the light leaving. Irrelevant for one
   electrode; the chain model handles it for bends.
7. **The TW block is not an exact line.** Against the exact model it is off by
   0.16 dB / 5.8° at 50/55 Ω (BW 98.2 vs 99.6 GHz) and 1.06 dB / 14° at
   30/80 Ω (58.3 vs 65.5 GHz), mostly below 20 GHz, with the line's 4.7 GHz
   round-trip ripple. Complex Z0 (conjugate, real part, modulus), n_g and
   single-reflection simplifications were tested and none reproduces it.

## Checked offline (Python, no INTERCONNECT)

| Check | Agreement |
|---|---|
| TL line chain vs the TW formula (`eo_transfer`), straight 14 mm, 50/53 Ω and 30/80 Ω, complex, to 800 GHz | 1.5e-11 with the same dB→Np constant. The LSF uses the exact ln10/20, and `eo_transfer` the rounded 1/8.686, so the tables differ by 1e-5. |
| Electrode, bend, electrode chain (7 + 0.8 + 7 mm) vs the GUI's segmented cascade | 7.6e-12, bandwidth 95.991 GHz on both |
| Power vs voltage waves | differ by √R0 in the modulation output only, as expected |

`eo_transfer` returns −V_avg, an overall sign that affects neither |H| nor any
bandwidth. The TL line uses the physical sign, positive at DC.

## Step 1: the modulator built with the TL line

"Build + run in INTERCONNECT" and "Build eye in INTERCONNECT" use the TL line
when **Electrode model** (Lumerical group) is `TL line`, the default. `TW block`
builds the Ansys Traveling Wave Electrode as before, for comparison.

```
drive ── ELECTRODE (Compound, scattering data analysis on) ───────────────
          SRC(Zs) ─ EL_1 ─ BEND_1 ─ EL_2 ─ … ─ EL_N ─ LOAD(Rt)
                    │ │            │ │          │ │  └ far end ── ENA_1 input 2 / EYE_2
                    │ └ modulation 2 → OM_2_1   │ └ modulation 2 → OM_2_N   (arm 2, n_g2)
                    └── modulation  → OM_1_1    └── modulation  → OM_1_N    (arm 1, n_g1)
          OM_a_k joined by Optical Delays n_g,a·(bends + next section)/c
```

- **One line for both arms.** Each electrode section has a second modulation
  output, `modulation 2`. It integrates the same line voltage with the light at
  arm 2's group index (`ng2`). With `ng_imbalance` = 0 both outputs are
  identical, so no drive fan-out and no duplicated electrode are needed.
- **Source and termination with parasitics.** `TL source` and `TL load`
  compute Zs and Zt = (R + jωL) ∥ 1/(jωC), the GUI's formula
  (`physics.rlc_impedance`), as tables up to the simulation's Nyquist
  frequency. The TW block took one reactance at the probe frequency. With
  L = C = 0 they are the constant Step 0 elements.
- **Voltage across the termination.** The last section's `far end` output is
  read back:
  - In the ENA build it goes to ENA_1 input 2. The INTERCONNECT tab then shows
    a third panel, |V_term/V_EMF| in dB, against the Python value
    (`scripted_line.far_end_model`). The log gives their ratio at 0.5–3 GHz,
    which should be 1.000. The ENA reading is divided by 2: its output is
    EMF/2 (Step 0, point 5).
  - In the eye build it goes to an electrical eye, EYE_2, with the same
    reference as EYE_1. Its metrics are logged.
- **Exactly the same optics as the TW build.** OM coefficients c·L_k/L_mod,
  and the optical delays between sections. The TL output is referenced to the
  light leaving its section, like the TW output, so the OMs stand at the
  section exits.
- **Wiring.** The electrical elements are built and wired at root level, so the
  drive link enters the selection and `createcompound` keeps it. They are then
  grouped. Each output becomes an Output port of the Compound, wired outside to
  its OM, ENA or EYE_2, and inside to its own relay. If a relay wire cannot be
  drawn from the script, the project is saved but not run, and the message
  names the wire to draw by hand.
- **Compound filter.** The build tries to set 1024 FIR taps on the Compound and
  logs whether this INTERCONNECT accepts the property. The 0.04–0.1 dB residual
  of Step 0 may come from the Compound's default, shorter filter.
- **Library element.** A library element made with an older
  `create_tl_element.lsf` lacks `second_modulation` and `ng2`. Make it again,
  or leave "TL line library element" empty so the build creates the elements
  itself.

### Step 1 checks, in order

1. **Straight electrode, ENA.** The TL build's EO bandwidth must match the
   Python one. The far-end ratio must be 1.000. Compare with `TW block` at the
   same settings: the difference is the TW block's own error (Step 0, point 7).
2. **Split electrode.** Set `n_bends` = 1 with bend length 0 and two sections
   summing to the straight length. The result must equal check 1.
3. **Real bends** against the GUI's segmented model.
4. **Group-index imbalance** (for example 0.02) against the GUI, which
   includes it (`device_response`).
5. **Eye** against the Python eye. EYE_2 shows the termination voltage.

Offline (`tools/validate_tl_line.py`, 15 checks): the second output against
the cascade at arm 2's n_g; `rlc_z` (as in the LSF) against
`physics.rlc_impedance`; an R+L+C source and load against `eo_transfer`; the
far-end voltage against the closed form V(0)/(cosh γL + Z0/Zt·sinh γL).
