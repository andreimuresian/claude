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
| `far end` | output, electrical | optional: the line voltage at port 2 |

A **bend** is the same element with `modulating = 0` and its own table. It then
has only ports 1 and 2.

## Properties

| Property | Meaning |
|---|---|
| `line_length` | physical length, m |
| `ng` | optical group index (electrodes) |
| `R0` | reference impedance of the S-matrix, 50 Ω. The same value for every element in a chain. |
| `table_file` | frequency (Hz), loss (dB/m), microwave index, Re Z0, Im Z0 |
| `modulating` | 1 electrode, 0 bend |
| `far_end_output` | 1 to have the `far end` port |
| `wave_convention` | `voltage` (default) or `power`. Step 0 tells which one INTERCONNECT uses. |
| `fir_taps` | FIR taps per entry (1024) |

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
| S2 | TL line as a plain 2-port: ENA → CNC → TL → ENA | `setsparameter` on bidirectional electrical ports |
| S3 | TL line with its modulation output, short table (~50 points) | the Output port driven from bidirectional ports |
| S4 | same, full table, both cases | table size or FIR design |
| S5 | S4 inside a Compound | the Compound's S-parameter solver |

A failed stage does not stop the next one: the Compound can work where the
flat row does not. The element tables stop at the run's Nyquist frequency.

The two cases are the GUI's Zs/Rt, and 30 Ω / 80 Ω so the reflections at both
ends are large. Each row is measured by its own Network Analyzer on the
electrode's modulation output (electrical only, no optics):

| Row | Contents |
|---|---|
| REF | Ansys TW block, same tables, Zs and Rt inside |
| FLAT | Electrical Connector (Zs → R0) → TL line → Electrical Connector (R0 → Rt) |
| CMP | the FLAT row inside a Compound with *scattering data analysis* on |

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
| `scale` | INTERCONNECT ÷ model at 0.5–3 GHz. It carries the conventions, and the report names the one it matches: ×1 as modelled, ×0.5 or ×2 for the source convention, ×√50 for power waves. It also gives its phase; 180° means the opposite sign. |
| `max dB`, `max deg` | largest magnitude and phase difference over the band, after removing `scale` |
| `dGD ps` | mean group-delay difference |
| `BW ref`, `BW test` | −3 dB bandwidths |

The REF line also states which phase reference the TW block uses: light
leaving the line, or light entering it. The documentation doesn't say. It
decides where the optical delays go in a bend build.

**Pass:** FLAT and CMP within about 0.05 dB and 1° of REF up to the top of the
band, the same bandwidth to about 0.1 GHz, and a scale that is a known
convention factor. For reflections between blocks, trust the CMP row.

### What Step 0 settles that the documentation does not

1. `setsparameter` on **electrical** ports, including reflections (port 1 → port 1).
2. How a Network Analyzer or NRZ output entering an Electrical Connector is
   interpreted: EMF or incident wave.
3. Whether INTERCONNECT uses voltage or power waves.
4. The TW block's phase reference.
5. Whether the Compound row differs from the flat row (delays that INTERCONNECT
   inserts on bidirectional ports outside a Compound).

## Checked offline (Python, no INTERCONNECT)

| Check | Agreement |
|---|---|
| TL line chain vs the TW formula (`eo_transfer`), straight 14 mm, 50/53 Ω and 30/80 Ω, complex, to 800 GHz | 1.5e-11 with the same dB→Np constant. The LSF uses the exact ln10/20, and `eo_transfer` the rounded 1/8.686, so the tables differ by 1e-5. |
| Electrode, bend, electrode chain (7 + 0.8 + 7 mm) vs the GUI's segmented cascade | 7.6e-12, bandwidth 95.991 GHz on both |
| Power vs voltage waves | differ by √R0 in the modulation output only, as expected |

`eo_transfer` returns −V_avg, an overall sign that affects neither |H| nor any
bandwidth. The TL line uses the physical sign, positive at DC.

## Next

**Step 1:** electrode, bend and electrode as TL line elements in one Compound,
driving OM, optical delay and OM, compared with the GUI:
- the complex EO response from the Network Analyzer;
- the Compound's exported S-parameters against `scripted_line.chain_response`;
- the detected waveform, written by a Probe, against the Python eye.
