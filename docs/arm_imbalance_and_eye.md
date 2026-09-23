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

### What each one costs in INTERCONNECT

Ordered from "just set a property" to "needs a different schematic", against
the element reference:

**1. Arm loss imbalance -- fully representable, two ways.**
`Optical Attenuator` (ATT) in arm 2, property `attenuation` in dB. This is what
the builder does. The alternative is the OM element's own `absorption
coefficient a`, the constant term of its absorption polynomial, which puts the
loss inside the modulator where it physically belongs and saves an element.
Either is exact.

**2. Splitter imbalance -- fully representable, on the Y branch rather than
the splitter.** The SPLT element's `split ratio` accepts only `even` or `none`,
so it genuinely cannot express a 55:45 split. The `Waveguide Y Branch` (Y)
element can: `coupling coefficient 1` is a power transmission coefficient in
[0, 1], and it is also the element a thin-film LN interferometer actually has
at each end. The builder now uses Y branches by default and falls back to SPLT
only if this build has no Y element.

Port semantics are unambiguous, which is a secondary benefit: `port 1` is the
single side, `port 2` and `port 3` are the pair, with T the port 1 <-> port 3
power transmission and 1 - T going to port 2. Arm 1 hangs off port 2 and arm 2
off port 3, so a fraction rho into arm 1 means `coupling coefficient = 1 - rho`.

The substantive gain is the power budget. T and 1 - T *redistribute* power,
which is what a real Y does; the old workaround folded the split error into the
arm-2 attenuator, and an attenuator *dissipates*. Both give exactly the same
field ratio, so the extinction ratio, the chirp and the bandwidth were already
right -- but the absolute received power was not, and that is what decides
whether an eye is noise limited or ISI limited. The Y element also has an
`insertion loss` property, exposed as `y_branch_loss_dB`, for the real excess
loss of each branch (0.1-0.3 dB is typical). It is common-mode: 0.2 dB per
branch leaves the bandwidth at 70.511 GHz and the eye ER at 15.4 dB, and scales
the OMA by 10^(-0.4/10) = 0.912, exactly as it should.

The output combiner is left at 50:50. A fabrication error affects both Y
branches in a real device and the two imbalances compound, but the Python model
puts the whole split error at the input, and the two halves of the toolkit
agreeing matters more here than the second decimal place of the extinction
ratio. Say the word if you want the output error as its own parameter.

**3. Static phase imbalance -- fully representable, with one caveat.**
`Optical Phase Shift` (PHS), property `phase shift`, in radians. The caveat is
that this is a fixed *phase*, not a fixed *path length*: a real delta-n_eff.L
imbalance grows with optical frequency and gives the interferometer a finite
free spectral range, and PHS will not reproduce that. For wavelength-dependent
behaviour you need an actual length difference between the arms -- two
waveguide elements, or two OM elements with different `length`.

**4. V_pi imbalance -- fully representable.** With `input parameter` set to
`coefficients`, the two OM elements carry different `phase coefficient c`. Only
the product of the coefficient and `length` matters, so you can equivalently
vary `length`; the builder varies the coefficient and keeps the length at 1 um
in both arms.

**5. Group-index imbalance -- NOT representable as currently wired.** One TW
element feeds both modulators and carries a single `optical index`, so both
arms necessarily see the same walk-off. There are two routes, and both cost
something:

  * give each arm its own TW element. That is the honest fix, and it is also
    the prerequisite for a genuine differential drive, so it is the one worth
    doing -- but it needs a second drive path (a second PRBS/NRZ pair with a
    digital NOT between them, per the Ansys note) or an electrical splitter.
  * switch the OM elements to `electrode type = 'traveling wave'` and give each
    its own `optical index`. This works, but the OM's built-in electrode takes
    scalar `microwave loss` and `microwave index` rather than the frequency
    tables the TW element accepts, so you would be throwing away the fitted
    alpha(f), Zc(f) and n_m(f) -- which is the whole point of the extraction.
    Not worth it.

**6. Voltage-dependent loss imbalance (residual amplitude modulation).**
Representable through `absorption coefficient a..d`, and left at zero here
because undoped LiNbO3 has no electro-absorption worth modelling. In a silicon
depletion-mode modulator it would be the first thing to set.

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

## 7. The eye analyser needs a reference, or it computes nothing

The EYE element's `reference` port is not optional in practice. Its documented
job is *automatic delay compensation of the input signal*: it is what tells the
element where the bit boundaries are, so that it can fold the received waveform
on the symbol period. With nothing connected to it there is no timing to fold
against, and the element produces **no eye and no results at all** -- not
merely a missing BER. It is enabled by default, which is why it appears in a
fresh schematic as an unconnected pin waiting for something.

The builder connects it to the electrical drive from `NRZ_1`, which is what the
Ansys transceiver examples do. If a build will not fan the NRZ output out to
both the electrode and the analyser, a duplicate `PRBS_2`/`NRZ_2` pair with the
same order and the same fixed seed emits an identical waveform -- the trick the
Ansys differential-drive note uses for the same reason. After wiring, the
builder checks that `EYE_1` has both the detected signal and the reference and
says so, rather than leaving an empty results window to deliver the news.

The element also has a `bit pattern input` port, off by default, which takes
the transmitted bits directly and makes the *measured* BER exact rather than
recovered. It is deliberately left disabled: the tutorials do not use it, it
needs a fan-out of its own, and an enabled port with nothing plugged into it is
worse than no port.

### Sample rate

An eye needs the sample rate to resolve a *symbol*, not just the top of the
microwave band. Sixteen samples per symbol is the usual floor. The toolkit's
default 320 GHz is chosen for the network-analyser sweep and gives only 3.2
samples per symbol at 100 Gb/s, which is not enough for the element to fold
anything, so in eye mode the builder raises the rate to
`16 x symbol rate` and says by how much.

### Level labelling

Once a reference is connected the element labels levels by the transmitted bit
rather than by power order. An MZM biased on the falling side of its transfer
curve then legitimately decodes level one *below* level zero, and the element
reports it in language that reads like a failure ("level zero mean greater than
level one mean", "eye considered closed"). It is the labelling, not the device.
The sign is known in advance from dP/dV at the bias, so the builder predicts it
and says which way round the eye will come out; add 180 degrees to the bias to
flip it.

At exactly 0 or 180 degrees that slope is zero: the modulator sits at a turning
point, there is no small-signal modulation at all, and the output responds at
twice the drive frequency. Both the eye and the EO bandwidth are meaningless
there, and both sides of the toolkit say so rather than reporting a number.
