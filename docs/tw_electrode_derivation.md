# The travelling-wave electrode block: what it does and why

This note derives the transfer function of a travelling-wave (TW) electrode
from first principles. It then maps every line of our implementation
(`eo_transfer` in `mzm_interconnect/physics.py`) onto the derivation. The goal
is that you can redo it on paper and answer "what exactly comes out of the
block?" without notes.

Convention: phasors are written as e^{+jωt}. That is the engineering
convention and the one `physics.py` uses.

---

## 1. The one-sentence answer

The TW block outputs the **modulation voltage**: the RF line voltage averaged
along the electrode as seen by a photon travelling through it at the optical
group velocity.

    V_mod(t) = (1/L) ∫₀ᴸ V(z, t + z/v_o) dz        v_o = c/n_g

The optical modulator downstream multiplies it by π/Vπ to get the phase:
φ(t) = π·V_mod(t)/Vπ.

V_mod is **not** a voltage at any physical point on the line. It is neither
the input voltage nor the far-end voltage. It is an *effective* voltage. In
the frequency domain it is the source voltage filtered by the EO transfer
function H(f), which this note derives.

The consequence: the block has an electrical input and a "modulation" output,
but no RF output port that a further line (a bend, a second electrode) could
load. The source and the load are internal parameters (Zs, Zt). That is why it
cannot be cascaded, and why we wrote the TL line element
(`docs/scripted_tl_element.md`).

---

## 2. Physical picture

- A voltage wave enters the electrode at z = 0 and travels at
  v_m = c/n_m, attenuated by α.
- Part of it reflects at the load Zt, travels back and reflects again at the
  source Zs, and so on.
- A photon enters at z = 0 at time t and reaches position z at time t + z/v_o.
- At every position the photon picks up phase proportional to the local field,
  i.e. to the local voltage *at the moment the photon is there*.
- The total phase is the sum of those contributions along the length. That
  sum is the integral above.

Three things reduce the result relative to the ideal case:

| Mechanism | Parameter | Effect |
|---|---|---|
| Velocity mismatch (walk-off) | Δn = n_m − n_g | the photon sees a voltage whose phase rotates along z, and the contributions partially cancel |
| RF loss | α(f), growing ~√f (skin effect) plus ~f (dielectric) | the voltage at the far end is smaller |
| Impedance mismatch | Zs, Zt ≠ Zc | reflections: a backward wave (strongly walked off, since it counter-propagates) and a source-divider error |

---

## 3. Derivation

### 3.1 The voltage on the line

The telegrapher's equations for a uniform line with propagation constant
γ = α + jβ_m (β_m = ω·n_m/c) and characteristic impedance Zc give

    V(z) = V⁺ e^{−γz} + V⁻ e^{+γz}
    I(z) = (V⁺ e^{−γz} − V⁻ e^{+γz}) / Zc

### 3.2 Boundary condition at the load (z = L)

V(L)/I(L) = Zt gives

    V⁻ = Γ_L V⁺ e^{−2γL},      Γ_L = (Zt − Zc)/(Zt + Zc)

### 3.3 Input impedance and the source divider (z = 0)

The impedance seen looking into the loaded line is

    Zin = Zc · (Zt + Zc tanh γL) / (Zc + Zt tanh γL)

The source (EMF Vs, internal impedance Zs) sees a divider:

    V(0) = Vs · Zin / (Zs + Zin)

and V(0) = V⁺(1 + Γ_L e^{−2γL}), so

    V⁺ = Vs · Zin / [ (Zs + Zin)(1 + Γ_L e^{−2γL}) ]

Multiply the numerator and the denominator by (Zt + Zc)e^{γL}:

    V⁺ = Vs · (Zt + Zc) e^{γL} · p1
    V⁻ = Vs · (Zt − Zc) e^{−γL} · p1

    p1 = Zin / [ (Zs + Zin) · ( (Zt + Zc) e^{γL} + (Zt − Zc) e^{−γL} ) ]

### 3.4 The photon's average

A photon entering at time t is at z at time t + z/v_o. The phasor of the
voltage it sees there is V(z)·e^{jω(t + z/v_o)} = V(z)·e^{jβ_o z}·e^{jωt},
with β_o = ω·n_g/c. Therefore

    V_mod = (1/L) ∫₀ᴸ V(z) e^{jβ_o z} dz

Both terms are integrals of an exponential:

    ∫₀ᴸ e^{−(γ − jβ_o)z} dz = (1 − e^{−u₊L}) / u₊     u₊ = γ − jβ_o = α + j(β_m − β_o)
    ∫₀ᴸ e^{+(γ + jβ_o)z} dz = (e^{u₋L} − 1) / u₋      u₋ = γ + jβ_o

The quantity that matters for the forward wave is **u₊ = α + j(β_m − β_o)**:
loss plus walk-off. For the backward wave, u₋ contains β_m + β_o, so its
phase rotates very fast along z and its average is small. Reflections are
therefore mostly lost modulation, plus ripple.

### 3.5 The result

    H(f) = V_mod / Vs
         = p1 · [ (Zt + Zc) e^{γL} (1 − e^{−u₊L}) / (u₊L)
                + (Zt − Zc) e^{−γL} (e^{u₋L} − 1) / (u₋L) ]

---

## 4. Limit checks (do these on paper)

**DC (γ → 0, β_o → 0).** Zin → Zt, both brackets → 1, so

    H(0) = Zt/(Zs + Zt)

This is just the resistive divider, as it must be.

**Matched (Zs = Zt = Zc) and lossless.** p1 = 1/(4Zc e^{γL}) and the backward
term vanishes:

    |H| = ½ · |sinc(ΔβL/2)|,      Δβ = ω(n_m − n_g)/c

- ½ is the matched divider.
- |sinc(x)| = 0.707 at x = 1.39, so the walk-off-limited bandwidth is

      f_3dB ≈ 1.39·c / (π·|n_m − n_g|·L) = 0.443·c / (|Δn|·L)

  For example, Δn = 0.05 and L = 14 mm give about 190 GHz.

**Matched and velocity-matched (Δn = 0), with loss.**

    |H|/H(0) = (1 − e^{−αL}) / (αL)

This reaches 0.707 at αL = 0.74 Np, i.e. **6.4 dB total electrical loss at
f_3dB**. That rule of thumb links an RF loss figure directly to an EO
bandwidth.

**Mismatched load, lossless.** |H| ripples with period Δf = c/(2·n_m·L):
the round-trip frequency of the line. For n_m = 2.2 and L = 14 mm that is
4.9 GHz, which is the ripple seen in the Step 0 runs.

---

## 5. How the code implements it (`eo_transfer`, `physics.py`)

| Code | Equation |
|---|---|
| `beta_opt = ng*omega/C0`, `beta_rf = nm*omega/C0` | β_o, β_m |
| `alpha_Np_m = alpha_dB_cm*100*NP_PER_DB` | α in Np/m (1 Np = 8.686 dB) |
| `gamma = alpha_Np_m + 1j*beta_rf` | γ |
| `zin = Zc*((Zt+Zc*tanh_gL)/(Zc+Zt*tanh_gL))` | Zin, §3.3 |
| `M`, `N`, `p1 = zin/(M*exp(gL)+N*exp(-gL))` | p1, §3.3 |
| `up = L*(alpha + 1j*(beta_rf-beta_opt))` | u₊L |
| `un = L*(-alpha + 1j*(-beta_rf-beta_opt))` | −u₋L |
| `p2 = (Zt+Zc)*(1-exp(up))/up + (Zt-Zc)*(1-exp(un))/un` | the bracket of §3.5, rewritten |
| `np.where(abs(u) < 1e-12, …)` | avoids 0/0 at DC; (1 − e^x)/x → −1 |

Rewriting the bracket shows that the code returns

    eo_transfer = −e^{−jβ_o L} · H(f)

- **The minus sign** is an overall sign. It does not affect |H| or any
  bandwidth (it is noted in `scripted_tl_element.md`).
- **e^{−jβ_o L}** is a pure delay of n_g·L/c: the code references the phase to
  the light *leaving* the electrode, whereas §3.4 references it to the light
  entering. A pure delay does not change the magnitude response. It matters
  only when electrodes are chained, and the chain model accounts for it.

---

## 6. The INTERCONNECT TW block versus this formula

What the Step 0 runs established (`docs/scripted_tl_element.md`):

- The INTERCONNECT TW block computes the same quantity, the modulation
  voltage, and references it to the light entering the electrode.
- It is **not** an exact line solution. Against §3.5 it is off by 0.16 dB and
  5.8° at Zs/Zt = 50/55 Ω, and by 1.06 dB and 14° at 30/80 Ω, mostly below
  20 GHz. We have not identified which approximation it makes.
- Our TL line element reproduces §3.5 to 0.04 dB / 0.4° inside a Compound.

This is what was missing at the meeting: the block's output is the
photon-averaged voltage, an effective quantity derived above, not a node
voltage.

---

## 7. Exercises (to be done on paper, then checked against the code)

1. Derive Zin from V(z), I(z) and the load condition.
2. Derive H(0) and the matched-lossless sinc result from §3.5.
3. Show that the backward-wave term is negligible when Zt = Zc, and estimate
   its size for Zt = 1.2·Zc at 50 GHz.
4. Derive the 6.4 dB rule (solve (1 − e^{−x})/x = 1/√2).
5. Predict before running: with Δn = 0, does raising Zt above Zc increase or
   decrease the low-frequency response, and the bandwidth? Then check it in
   the GUI.
6. Explain in two sentences why an arm with a different n_g (group-index
   imbalance) has a different H(f), and which term in §3.5 carries it.
