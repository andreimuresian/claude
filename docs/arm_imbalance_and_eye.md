# Arm imbalance in a push-pull TW-MZM: what moves the bandwidth, what closes the eye

Reference note for the imbalance study. Everything here is implemented in
`mzm_interconnect/physics.py` (`arm_models`, `link_response`) and
`mzm_interconnect/eye.py`, and the numbers quoted are reproducible from the
Sweep tab.

## 1. The five mechanisms, and why V_pi is not the only one

A single fabrication error drives several effects at once, but they are
physically independent and they enter the model in different places. An
asymmetric rib over-etch in one arm changes that arm's mode, and through it:

| # | Mechanism | Physical origin | Parameter | Where it enters |
|---|-----------|-----------------|-----------|-----------------|
| 1 | Amplitude imbalance | different propagation loss (sidewall scattering, mode size) | `arm_loss_imbalance_dB` | field weight `a2` |
| 2 | Amplitude imbalance | Y-branch / MMI split away from 50:50 | `split_err` | field weights `a1`, `a2` |
| 3 | Static phase | different `n_eff` over the arm length | `arm_phase_imbalance_deg` | `phi0_2` |
| 4 | Modulation efficiency | different overlap integral `Gamma` between optical mode and RF field | `vpi_imbalance_frac` | `g2 = -pi/(Vpi(1+d))` |
| 5 | Walk-off | different optical group index `n_g` | `ng_imbalance` | `H2(f)` |

The causal chain "over-etch -> loss imbalance -> finite ER" runs through
mechanism 1, **not** through V_pi. The chain "over-etch -> different overlap ->
different V_pi -> residual chirp" runs through mechanism 4. They are two
separate consequences of the same defect and they do different things: loss
imbalance caps the extinction ratio and does not produce chirp; V_pi imbalance
produces chirp and barely touches the extinction ratio.

In INTERCONNECT the five map onto four different elements, not onto one:

* 1 -> `Optical Attenuator` in arm 2 (`ATT_1`)
* 2 -> `Optical Splitter` split ratio (`SPLT_1`)
* 3 -> `Optical Phase Shift` (`PHS_1`)
* 4 -> the two `Optical Modulator Measured` phase coefficients `c1`, `c2`
* 5 -> not expressible with one shared `Traveling Wave Electrode`; it needs a
  second `TWE` with its own `optical index`, which is also what the Ansys
  travelling-wave example proposes for a differential drive.

Two further knobs on the OM element are deliberately left at zero. The
`absorption coefficient a..d` fields give voltage-dependent loss, i.e.
electro-absorption; in undoped LiNbO3 there is none worth modelling, unlike a
depletion-mode Si modulator where residual amplitude modulation is real. The
`length` field is arbitrary here (only the product with the phase coefficient
matters) and is fixed at 1 um in both arms.

## 2. Why arm imbalance cannot move the -3 dB point

At the output combiner, two-beam interference gives

    P = a1^2 + a2^2 + 2 a1 a2 cos(dphi0 + m1(t) - m2(t))

with `m_i` the phase modulation in arm i. Linearising about the bias point for
a small drive `v`, and writing `m_i(f) = g_i H_i(f) V(f)` with `g_i = pi/Vpi_i`
signed by the drive polarity,

    dP(f) = -2 a1 a2 sin(dphi0) [ g1 H1(f) - g2 H2(f) ] V(f)

Everything outside the bracket is a **frequency-independent scalar**:

* amplitude imbalance enters only through `2 a1 a2`;
* bias error enters only through `sin(dphi0)`;
* V_pi imbalance enters only through the weights `g1` and `g2`.

A frequency-flat factor cancels exactly when the response is normalised to its
low-frequency value, which is how a -3 dB bandwidth is defined. So mechanisms
1-4 **cannot** move the bandwidth, however large they get.

Mechanism 5 is different: a group-index mismatch makes `H1` and `H2` genuinely
different functions of frequency, because each arm has its own walk-off
`|n_m - n_g,i|` against the same microwave. The bracket is then a sum of two
differently-shaped curves and the -3 dB point does move.

Measured on the synthetic 8 mm line, L = 8 mm, Rt = 40 ohm, balanced baseline
70.511 GHz:

| Imbalance | Link -3 dB | Shift |
|---|---|---|
| none | 70.511 GHz | - |
| 2.0 dB arm loss | 70.511 GHz | +0.000 |
| splitter 55:45 | 70.511 GHz | -0.000 |
| 30 % V_pi mismatch | 70.511 GHz | +0.000 |
| 30 deg bias error | 70.511 GHz | +0.000 |
| all four together | 70.511 GHz | +0.000 |
| **1 % n_g mismatch** | 69.673 GHz | **-0.839** |
| **5 % n_g mismatch** | 55.570 GHz | **-14.941** |

1 % of `n_g` mismatch between two arms of the same wafer is already an
implausibly large number for an over-etch that only changes the rib by tens of
nanometres, so in practice **the EO bandwidth of this device is insensitive to
arm imbalance**. That is the answer to give: the bandwidth measurement will not
see the defect, and the eye will.

## 3. What the imbalances actually do

Sweep of `arm_loss_imbalance_dB`, 100 Gb/s NRZ, noise off:

| Loss imbalance | Electrode BW | Link BW | Static ER | Eye ER | Eye Q | OMA |
|---|---|---|---|---|---|---|
| 0.0 dB | 70.511 | 70.511 | inf | 15.53 dB | 20.12 | 37.79 mA |
| 1.0 dB | 70.511 | 70.511 | 24.81 dB | 15.05 dB | 20.12 | 33.68 mA |
| 2.0 dB | 70.511 | 70.511 | 18.81 dB | 13.86 dB | 20.12 | 30.02 mA |
| 3.0 dB | 70.511 | 70.511 | 15.34 dB | 12.43 dB | 20.12 | 26.76 mA |

The static ER ceiling follows the closed form for two unequal fields,
`ER = 20 log10((1+rho)/(1-rho))` with `rho = a1/a2`. Note that `Q` is untouched:
loss imbalance lifts the zero rail and shrinks the OMA proportionally, so with
ISI-limited (not noise-limited) rails the signal-to-distortion ratio is
unchanged. Under a noise-limited receiver it would degrade, because OMA falls
while the noise does not.

Bias error moves the operating point off quadrature: the eye becomes
asymmetric, the crossing moves off 50 %, and second-harmonic distortion appears.
30 degrees of bias error took Q from 19.9 to 9.9 in the same sweep -- a much
bigger eye penalty than 2 dB of loss imbalance, and still zero bandwidth
penalty.

## 4. Chirp: real, small, and invisible back-to-back

The chirp parameter follows from the same weights:

    alpha = (g1 + g2)/(g1 - g2) = d/(2 + d)

for a fractional V_pi mismatch `d`. So 10 % mismatch gives alpha = 0.048 and
30 % gives alpha = 0.130 -- an order of magnitude below the alpha = 1 of
single-arm drive. This is the quantitative reason push-pull is worth having.

Chirp is a phase effect. A photodiode is square-law, so **a back-to-back eye is
almost blind to it**: what changes the back-to-back eye when `d` is varied is
the change in `Vpi_eff = 1/(1/Vpi1 + 1/Vpi2)`, i.e. the drive-to-V_pi ratio,
not the chirp. Chirp only becomes distortion once dispersion has converted
phase into amplitude. To see it, set `fibre_km` above zero.

The honest result of doing that: at 100 Gb/s NRZ over standard SMF the
dispersion penalty is dominated by the signal bandwidth itself, not by this
much chirp. The link is already closed at ~1-2 km (Q = 12.1 at 0.5 km, 4.1 at
1 km, 1.0 at 2 km for the balanced case), and across `d` from -30 % to +30 %
the 0.5 km Q moves only between 12.12 and 12.37. For realistic V_pi imbalance,
**the chirp penalty is not measurable at any distance where this format works
at all.** Chirp from V_pi imbalance is a real effect that is worth quoting as a
number and not worth worrying about.

## 5. Practical notes

* Set `drive_Vpp_V` near `Vpi_eff`. Over-driving past the null folds the
  transfer function back on itself and closes the eye while looking like a
  bandwidth problem; the static P(V) panel beside the eye makes this obvious
  at a glance.
* Receiver noise is negligible at the default +13 dBm laser -- 20 mA of
  photocurrent -- so Q is ISI-limited. Drop `P_laser_dBm` to a realistic
  received power (-10 dBm and below) before reading Q as a link margin.
* The `Eye diagram` tab and the `Build eye in INTERCONNECT` button are driven
  from the same fitted line, the same V_pi and the same imbalances, so a
  disagreement between them is a modelling difference, not a bookkeeping one.

## 6. Reading the eye, and checking it without measured data

Four things carry almost all the information, and each points at a cause:

| What you see | What it means | Which knob |
|---|---|---|
| The "0" rail sits above zero | finite extinction ratio | `arm_loss_imbalance_dB`, `split_err` |
| Rails unequal distance from the crossing; crossing off 50 % | the bias is not at quadrature | `bias_phase_deg`, `arm_phase_imbalance_deg` |
| Rails thick and sloped, eye narrow in time | intersymbol interference: the bit rate is too close to the bandwidth | `bitrate_Gbps` vs the EO bandwidth, `drive_bw_GHz` |
| Rails flattened, eye stops improving with more drive | over-driven past the null | `drive_Vpp_V` against V_pi,eff |

The right-hand panel exists to settle the last one at a glance: if the green
drive band runs past the minimum of P(V), the eye is being folded, and no
amount of bandwidth will fix it.

`tools/validate_eye.py` checks the model in fourteen places where the answer is
known before you run it -- three closed forms (static ER, chirp, bandwidth
invariance), the ISI-free limit, crossing symmetry, monotonic closure with bit
rate, and the power scaling of the noise. Run it against your own line:

    python tools/validate_eye.py path/to/line.s2p --L-meas 2.5 --L 16.5 --Rt 53

It prints what was expected, where the expectation comes from, and what the
model produced. That is not the same as validating against a measured eye, but
it does tell you whether the arithmetic is doing what the physics says it must.

**The cheapest real calibration point is a DC transfer curve.** Sweeping the
bias voltage and recording output power gives V_pi, the static extinction ratio
and the insertion loss from one measurement, and those three numbers pin down
`Vpi_V`, `arm_loss_imbalance_dB` and `split_err` together. Everything dynamic in
the eye is built on top of them, so a model that reproduces the DC curve is
already most of the way to being trustworthy.
