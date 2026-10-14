# The scripted TL electrode: derivation, and how it compares with the native TW block

This note derives, from first principles, everything the scripted electrode
computes, element by element: SRC, the TL line (EL_k), LOAD, the relays and the
Compound around them. It then compares the result, port by port, with the
native INTERCONNECT Traveling Wave Electrode (TW block).

Read `tw_electrode_derivation.md` first. That note derives the **physics**,
H(f) = V_mod/V_s for one line between Zs and Zt. Its formula is our Python
model (`physics.eo_transfer`). It is not the native block's internal
algorithm: Ansys does not publish that algorithm, and the native block differs
from the formula by up to 1 dB (§11). The scripted block is our way of getting
the **same physics** inside INTERCONNECT, in a form that can be cascaded.

Checks: `docs/scripted/check_scripted.py` (numpy only) verifies §3, §6 and §8
to 1e-15, and gives the slice convergence of §9.

Convention: the maths uses e^{+jωt}. §10 explains why the LSF writes the
conjugate.

---

## 0. Two corrections before starting

1. **There are no infinitesimal modulation blocks.** The scripted element
   evaluates the overlap integral (1/L)∫V(z)e^{jβ_o z}dz in **closed form**.
   That is possible because V(z) is a sum of two exponentials, so each term
   integrates exactly. One element gives the exact integral. The idea of
   "many small slices" is the alternative we rejected: N short line pieces,
   each with its own lumped modulator. §9 shows that this is a Riemann sum
   approximating the same integral, with an error that falls only as about
   (β·Δz)².
2. **The scripted block is not a single element.** It is a small circuit
   (§1). The physics sits in two places: the EL elements (line plus integral)
   and the network solve that INTERCONNECT performs on the Compound. SRC and
   LOAD are the boundary conditions. The relays are plumbing.

---

## 1. The circuit

```
         ┌──────────── ELECTRODE (Compound, "scattering data analysis" on) ─────────────┐
 drive ──┤relay├─ SRC(Zs) ─ EL_1 ─ [BEND_1 ─ EL_2 ─ …] ─ LOAD(Zt)                       │
 (ENA or │                   │ │                                                           │
  NRZ)   │                   │ └ modulation 2 ──┤relay├── to OM of arm 2                   │
         │                   └── modulation  ───┤relay├── to OM of arm 1                   │
         │                   (last EL) far end ─┤relay├── to ENA input 2 / EYE_2           │
         └──────────────────────────────────────────────────────────────────────────────────┘
```

| Element | Script | Ports | Role in the maths |
|---|---|---|---|
| SRC | `source_setup.lsf` | port 1, port 2 (bidirectional) | Thevenin source: EMF behind Zs (§6.1) |
| EL_k (TL line) | `tl_element_setup.lsf` | port 1, port 2 (bidirectional); modulation, modulation 2, far end (outputs) | exact line S-matrix (§3) + exact overlap integral (§4–5) |
| BEND_k | same script, `modulating = 0` | port 1, port 2 | line with its own table, no integral |
| TL electrode (bent build) | `tl_electrode_setup.lsf` | as EL_k | all sections and bends in one element (§7) |
| LOAD | `termination_setup.lsf` | port 1 | Zt (§6.2) |
| relays | created by INTERCONNECT | input, output | one per Compound pin; passes the signal through, no physics |

Port types matter:

- A **bidirectional** port carries a wave in each direction. Reflections
  travel through it. These ports make up the RF network.
- An **output** port only emits. It has S-entries *from* the RF ports *to*
  itself, and none in the other direction. It therefore draws no current and
  does not load the line: it is an ideal probe. The modulation port is a
  probe that measures the photon-averaged voltage instead of a node voltage.

---

## 2. Waves and port quantities

Each RF port has a voltage V and a current I (flowing *into* the element). With
reference impedance R0 (50 Ω, the same for every element), the voltage waves
are

    a = (V + R0·I)/2   (incident, entering the element)
    b = (V − R0·I)/2   (leaving the element)

and, inverted,

    V = a + b,     I = (a − b)/R0

An element is defined by **b = S·a**: the leaving waves are linear in the
incident ones. INTERCONNECT only ever handles a and b. V and I are our own
bookkeeping. R0 is arbitrary: it changes the numbers in S but not the physics,
as long as all elements use the same R0 (the lesson of the cascade work).

`wave_convention = "power"` uses a = (V/√R0 + √R0·I)/2. The RF S-matrix is
identical; only the output ports rescale by √R0 (variable `ws` in the LSF). We
use "voltage".

---

## 3. The line's S-matrix (EL_k, LSF section 2)

The line has propagation constant γ = α + jωn_m/c and impedance Zc, both read
from the table at each frequency. Inside the line V(z) = V⁺e^{−γz} + V⁻e^{+γz}.

**Derivation by bounces.** Put R0 outside on both sides and Zc inside.

- At each end, a wave meets an impedance step. The reflection coefficient is
  Γ = (Zc − R0)/(Zc + R0) going from outside to inside, and −Γ going from
  inside to outside. The transmission coefficients are 1 + Γ and 1 − Γ.
- A wave entering at port 1:
  - reflects immediately with Γ;
  - the rest crosses the line (factor e^{−γL}), partly leaves at port 2
    (1 − Γ), partly reflects back (−Γ), and so on.

Summing the geometric series with ratio Γ²e^{−2γL} gives

    S11 = S22 = Γ (1 − e^{−2γL}) / (1 − Γ² e^{−2γL})
    S21 = S12 = (1 − Γ²) e^{−γL} / (1 − Γ² e^{−2γL})

**Cross-check with ABCD** (the form used in the CST work):

    S11 = (A + B/R0 − C·R0 − D)/Δ,  S21 = 2/Δ,  Δ = A + B/R0 + C·R0 + D

with A = D = cosh γL, B = Zc sinh γL, C = sinh γL/Zc. The two forms agree to
1e-16 (check script).

**Limits.** With Zc = R0, Γ = 0, so S11 = 0 and S21 = e^{−γL}: a pure delayed,
attenuated wave. With L = 0, S11 = 0 and S21 = 1: no element.

---

## 4. From incident waves to the voltage inside the line (LSF section 5)

The element must give the modulation for **any** incident waves. Everything is
linear, so it is enough to compute two unit cases and superpose:

    V_mod = T1·a1 + T2·a2

where T1 is the modulation for a1 = 1, a2 = 0, and T2 for a1 = 0, a2 = 1.
**These two functions of frequency are the only things the modulation port
stores.** Which a1 and a2 actually occur depends on the source, the load and
the bends, and INTERCONNECT finds them (§6).

**Case 1 (a1 = 1, a2 = 0).** b1 = S11, so at port 1

    V(0) = 1 + S11,     I(0) = (1 − S11)/R0

**Case 2 (a1 = 0, a2 = 1).** b1 = S12 = S21, so

    V(0) = S21,         I(0) = −S21/R0

**From V(0), I(0) to the two waves inside.** At z = 0, V(0) = V⁺ + V⁻ and
Zc·I(0) = V⁺ − V⁻. Hence

    V⁺ = (V(0) + Zc·I(0))/2,     V⁻ = (V(0) − Zc·I(0))/2

These are the LSF variables `Vp1, Vm1` (case 1) and `Vp2, Vm2` (case 2). Note
that Zc, not R0, appears here: these are the true waves on the line, not the
bookkeeping waves.

---

## 5. The overlap integral in closed form (LSF section 5)

The photon enters at z = 0 at time t and is at z at time t + z/v_o. As in
`tw_electrode_derivation.md` §3.4:

    V_avg = (1/L) ∫₀ᴸ V(z) e^{jβ_o z} dz,     β_o = ω n_g / c

Substitute V(z):

    ∫₀ᴸ V⁺ e^{(−γ + jβ_o)z} dz = V⁺·F1,   F1 = (e^{q1 L} − 1)/q1,  q1 = −γ + jβ_o
    ∫₀ᴸ V⁻ e^{(+γ + jβ_o)z} dz = V⁻·F2,   F2 = (e^{q2 L} − 1)/q2,  q2 = +γ + jβ_o

- **Forward wave.** q1 = −α − j(β_m − β_o) is small when the line is
  velocity matched and lossless. Then F1 → L: full contribution.
- **Backward wave.** q2 contains β_m + β_o, so F2 is small: the counter-
  propagating wave averages out (the same conclusion as in the TW note).
- **Small q.** If |qL| < 1e-6, e^{qL} − 1 cancels numerically. The LSF then
  uses the series L(1 + qL/2 + (qL)²/6), which is the variable `sm`.

Finally, the reference:

    T = (V⁺F1 + V⁻F2) · e^{−jβ_o L} / L

The factor e^{−jβ_o L} is a pure delay of n_g L/c. It refers the phase to the
light **leaving** the line, so that the OM standing at the electrode exit
sees the modulation at the right time. The 1/L makes it an average.

So EL_k stores, for each frequency:

| Entry | Value |
|---|---|
| S(port1←port1), S(port2←port2) | S11 |
| S(port2←port1), S(port1←port2) | S21 |
| S(modulation←port1) | T1 at n_g |
| S(modulation←port2) | T2 at n_g |
| S(modulation 2←port1/2) | T1, T2 at n_g2 (the same V⁺ and V⁻, only β_o changes) |
| S(far end←port1) | S21 (because V(L) = a2 + b2 = 0 + S21) |
| S(far end←port2) | 1 + S22 |

---

## 6. Source, load, and the network solve

### 6.1 SRC: a Thevenin source as a two-port

The physical driver is an EMF V_emf behind Zs. INTERCONNECT drives with
waves, so SRC translates between the two:

    S(port2←port1) = S(port1←port2) = T_f = 2R0/(Zs + R0)
    S(port2←port2) = Γ_s = (Zs − R0)/(Zs + R0)
    S(port1←port1) = −Γ_s

The driver (an ENA or an NRZ source, both matched at R0) sends a wave
a_drv = V_emf/2 into port 1. This is the "EMF/2" of Step 0, point 5.

**Proof that this is a Thevenin source.** At port 2, call a the wave going
into the line and b the wave coming back from it. SRC gives

    a = T_f·a_drv + Γ_s·b

The line-side port quantities are V = a + b and R0·I = a − b, with I flowing
into the line. Then

    V + Zs·I = a(R0 + Zs)/R0 + b(R0 − Zs)/R0
             = V_emf + b(Zs − R0)/R0 + b(R0 − Zs)/R0
             = V_emf

which is exactly **V(0) = V_emf − Zs·I(0)**, the source equation used in the
TW note. Port 1's −Γ_s only makes the element reciprocal, because the
Compound solver refuses one-way elements. The wave it reflects ends in the
matched driver and changes nothing.

With an L/C pad, Zs = (R + jωL) ∥ 1/(jωC), tabulated per frequency.

### 6.2 LOAD

A one-port with b = Γ_L·a, where Γ_L = (Zt − R0)/(Zt + R0). This is
equivalent to V(L)/I(L) = Zt, the load equation of the TW note.

### 6.3 The network solve (what the Compound does)

Write the unknown waves entering the line as a1 and a2, and the waves leaving
it as b1 and b2:

    a1 = T_f·a_drv + Γ_s·b1         (SRC)
    a2 = Γ_L·b2                     (LOAD)
    b1 = S11·a1 + S21·a2            (line)
    b2 = S21·a1 + S11·a2            (line)

Eliminating b gives a 2×2 linear system for a1 and a2. The output is
V_mod = T1·a1 + T2·a2. INTERCONNECT does exactly this, for any number of
elements: it collects all elements' b = S·a, adds a_i = b_j for every wire,
and solves the linear system at each frequency.

**Why it must be a Compound with scattering data analysis.** Outside a
Compound, each element becomes its own time-domain filter, with a latency of
half the filter length. Every bounce of a reflection passes through those
filters again and arrives late, which is Step 0's 0.45–2.8 dB error. Inside
the Compound, the system above is solved in frequency first, and the whole
circuit becomes **one** filter with one latency. The latency is then a pure
delay, harmless for EO bandwidth and the eye.

**Relays.** A Compound's pin is represented inside it by a relay element. A
wire from `EL_1:modulation` to the relay labelled *External Port =
modulation* is what makes that output visible at the Compound pin and hence
at the OM. Relays have no S-matrix of their own and carry no physics.

---

## 7. Equality with the TW formula: the central result

**Claim.** For one straight line, the modulation output of the scripted
circuit equals the TW formula H·V_emf (`tw_electrode_derivation.md` §3.5),
delayed by e^{−jβ_o L}.

**Proof.** V(z) on the line is the general solution V⁺e^{−γz} + V⁻e^{γz},
with two unknowns. The circuit imposes two conditions on it:

- V(0) = V_emf − Zs·I(0) (§6.1);
- V(L) = Zt·I(L) (§6.2).

The TW derivation imposes the same two conditions. Two linear equations in
two unknowns have a unique solution, so V(z) is the same function. The same
integral of the same V(z) gives the same V_mod, apart from the reference
factor e^{−jβ_o L}.

**Numerical check.** Agreement to 1e-15 relative, with Zs = 30 Ω,
Zt = 80 Ω, complex Zc, √f loss, and 0–100 GHz (check script). Earlier, the
full Python mirror agreed to 1.5e-11 (`scripted_tl_element.md`).

So the two models do not merely agree numerically: they are the same
mathematics, split differently. The TW formula solves boundaries, line and
integral in one expression. The scripted block puts the line and the
integral in EL (§3–5), the boundaries in SRC and LOAD (§6), and lets
INTERCONNECT do the algebra. That split is what lets a bend, a second
electrode or a pad sit between them.

### Bent electrode (TL electrode element, `tl_electrode_setup.lsf`)

The same method applies piece by piece:

- **S-matrix.** Multiply the ABCD matrices of all pieces (sections and bends)
  and convert to S. S22 ≠ S11 when the layout is asymmetric.
- **V and I at each section's entry.** Step them forward with the inverse of
  a piece's ABCD:

      V(z+ℓ) = cosh γℓ·V − Zc sinh γℓ·I
      I(z+ℓ) = −sinh γℓ/Zc·V + cosh γℓ·I

- **Each modulating section k** gives its own F1 and F2 integral, as in §5.
  It is then:
  - weighted by L_k/L_mod;
  - delayed by e^{−jβ_o·L_tail}, the light's transit through everything after
    it.
- **Sum** over the sections to get one modulation output per arm.

The optical delays between sections are therefore phases, not Optical Delay
elements. That removes the start-up artefact described in
`scripted_tl_element.md`.

---

## 8. What goes in and what comes out

| | Native TW block | Scripted block (SRC + EL + LOAD in a Compound) |
|---|---|---|
| RF input | one electrical input (the drive) | Compound pin to SRC port 1 (the drive wave, EMF/2) |
| RF output | none; the line ends inside the block | none at the Compound level; internally EL port 2 is a real port connected to LOAD, a bend or another line |
| Modulation output | 1: photon-averaged voltage, referenced to the light **entering** | 1 per arm (modulation, modulation 2): the same quantity, referenced to the light **leaving** |
| Far-end voltage | not available | optional `far end` output: the voltage across Zt |
| Zs, Zt | scalar properties of the block; a reactance taken at one frequency | separate elements; full frequency tables, including R+L∥C pads |
| Line data | the same tables (loss, n_m, Zc) | the same tables, in `electrode_line.txt` |
| Line solution | not published; 0.16 dB/5.8° (50/55 Ω) and 1.06 dB/14° (30/80 Ω) off the exact solution | exact; 0.0045 dB as a 2-port, 0.04 dB/0.4° inside a Compound (filter residue) |
| Cascading (bends, pads, coupled lines) | impossible | native: just more elements |
| Push-pull, n_g imbalance | two blocks (drive fanned out) | one line, two outputs |
| Time domain | one filter | one Compound filter (needs scattering data analysis on) |

In both cases the **output is a voltage**, V_mod, in volts per volt of EMF.
It goes to the OM, which gives φ = π·V_mod/Vπ through its modulation
coefficient. Neither block outputs light.

The native block's exact port names should be read off its symbol in the
GUI. We used it only as one electrical input and one modulation output.

---

## 9. Why not many small slices?

The "small modulation blocks" picture would be: cut the line into N pieces of
length Δz, put one OM on each piece driven by its local voltage, and add the
phases. That replaces the integral by a midpoint sum:

    V_avg ≈ (1/N) Σ_k V(z_k) e^{jβ_o z_k}

The midpoint rule's error is proportional to (Δz)² times the second
derivative of the integrand. Here that is about (β·Δz)², where β is the
fastest phase rate. For the backward wave that is β_m + β_o, roughly twice
the RF wavenumber.

Check script, 14 mm line at 60 GHz:

| N slices | 1 | 2 | 5 | 10 | 20 | 50 |
|---|---|---|---|---|---|---|
| relative error | 19 % | 12 % | 2.9 % | 2.6 % | 0.46 % | 0.046 % |

Reaching 0.01 dB (0.1 %) needs about 40 slices, plus 40 OMs and 40 optical
delays, each of which carries the time-domain artefacts we found. The closed
form gives the N → ∞ limit with one element. The slice picture is still the
correct way to *think* about the integral: the integral is that sum with
Δz → 0.

---

## 10. Implementation details (not physics, but needed to read the code)

- **Conjugation (`phase_convention`).** INTERCONNECT works in e^{−iωt}. A
  phase written as e^{+jωt} maths would be read as an advance, and
  INTERCONNECT would shift the filter by half its length to make it causal.
  That is the 512-sample latency Step 0 first measured. The LSF writes
  −angle (the variable `ps = −1`). Magnitudes are unchanged.
- **Magnitude and unwrapped phase.** `setsparameter` takes |S| and its phase
  per frequency. The phase is unwrapped so that interpolation between table
  points does not jump across ±π.
- **DC point.** If the table starts above 0 Hz, the first row is copied to
  0 Hz, so that the filter is defined down to DC and not extrapolated.
- **`setfir`.** 1024 taps per entry. This sets how well the filter
  reproduces the tables, hence Step 0's 0.04 dB residue.
- **dB → Np.** The LSF uses the exact ln10/20 and `eo_transfer` the rounded
  1/8.686. This is the 1e-5 difference noted in `scripted_tl_element.md`.

---

## 11. What the native block does that we cannot explain

The native block computes the same quantity (§8). Against the exact solution,
it errs mostly below 20 GHz, with the line's round-trip ripple, and the error
grows with the mismatch. We tested complex Zc handling, the n_g reference and
single-reflection simplifications, and none of them reproduces it. The honest
statement is: *"The native block is an approximate line solution of
undocumented form; we replaced it with an exact one and verified the
replacement against an independent derivation."*

---

## 12. What carries over to crosstalk

| Part | Carries over? |
|---|---|
| Waves, S-matrices, R0 bookkeeping (§2) | as is, with 4 ports |
| Line S-matrix (§3) | becomes 4×4, via even/odd modes (each mode is a §3 line) |
| V⁺ and V⁻ from port quantities (§4) | per mode, after a modal transformation of V and I |
| Closed-form overlap integral (§5) | as is: each line's voltage is a sum of 4 exponentials, so there are 4 F-terms |
| Superposition into T-functions (§4) | as is: 4 incident waves, so 4 T-entries per modulation output |
| SRC/LOAD and the network solve (§6) | as is; victim-line terminations are LOAD elements |
| Compound requirement (§6.3) | as is |

That is why the scripted block is the template for crosstalk: only §3–4
change, and they change by turning scalars into matrices.

---

## 13. Exercises

1. Derive S11 and S21 of §3 by summing the bounce series.
2. Show that for a1 = 1, a2 = 0 with Zc = R0, V⁻ = 0 and V⁺ = 1. Then show
   that T1 reduces to F1·e^{−jβ_oL}/L. What is it at DC?
3. Redo the Thevenin proof of §6.1. What does SRC become when Zs = R0?
4. Write the 2×2 system of §6.3 and solve it for Zs = Zt = Zc = R0. Show that
   V_mod reduces to ½·e^{−jβ_oL}·F1/L, the matched TW result.
5. Explain in two sentences why the modulation port does not load the line.
6. Predict: keep Zs, Zt and the line fixed and change R0 from 50 Ω to 20 Ω.
   Does V_mod change? (Hint: §7. Check it by editing R0 in the script.)
7. For the bent electrode, explain why section k is delayed by L_tail, and
   why the delay uses n_g (light), not n_m.
