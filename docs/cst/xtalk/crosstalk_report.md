# Crosstalk of two coupled TFLN electrodes from a 2-D cross-section

What was done, step by step, with the equations actually used. Pitch 200 µm unless stated. Scripts are in `docs/cst/xtalk/`; each section names the one that produces its numbers.

**Notation**

| Symbol | Meaning |
|---|---|
| GSG | ground–signal–ground coplanar waveguide (CPW) |
| Ports | 1 → 2 is line A, 3 → 4 is line B; ports 1 and 3 are at the same end |
| NEXT | near-end crosstalk, $S_{31}$ |
| FEXT | far-end crosstalk, $S_{41}$ |
| $z_0$ | port reference impedance, 50 Ω |
| $\gamma=\alpha+j\beta$ | propagation constant; $n=\beta c/(2\pi f)$ is the effective index |
| $L$ | line length |

---

## 1. The 3-D data and their error floor

The coworker's CST runs give 4-port S-matrices (`LINEA0_1MM_*`, `LINEA0_5MM_200UM_PITCH.s4p`).

Lines A and B are geometrically identical, so in an exact solution $S_{21}=S_{43}$. Their complex difference measures the numerical error of the run:

$$e = 20\log_{10}\lvert S_{21}-S_{43}\rvert .$$

At 30 GHz this gives:

| Run | $e$ | FEXT |
|---|---|---|
| 1 mm | −72.7 dB | −70.6 dB |
| 5 mm | −56.3 dB | −56.8 dB |

Crosstalk at or below $e$ is not trustworthy. The phase of $S_{43}/S_{21}$ grows linearly with $f\cdot L$, so the error behaves like a slightly different index on the two lines ($\Delta n\approx 4$–$7\times10^{-4}$). That points to mesh asymmetry (`pitch_compare.py`).

---

## 2. Why chaining five 1 mm blocks failed

**What was done.** Two 4-port blocks are joined by connecting port 2 → next port 1 and port 4 → next port 3. Group each block's ports into a left pair $(1,3)$ and a right pair $(2,4)$, so each S-matrix splits into 2 × 2 blocks $S_{LL}, S_{LR}, S_{RL}, S_{RR}$. The connection is the Redheffer star product (`cascade_naive.py`):

$$
\begin{aligned}
M_1 &= (I - B_{LL}A_{RR})^{-1}, \qquad M_2=(I-A_{RR}B_{LL})^{-1}\\
S_{LL} &= A_{LL} + A_{LR}M_1B_{LL}A_{RL}, \qquad S_{LR}=A_{LR}M_1B_{LR}\\
S_{RL} &= B_{RL}M_2A_{RL}, \qquad S_{RR}=B_{RR}+B_{RL}M_2A_{RR}B_{LR}
\end{aligned}
$$

Applied four times to the 1 mm block, it reproduces the 5 mm through path (S21). It does not reproduce NEXT and FEXT: at 30 GHz, NEXT is −78.7 dB chained against −52.5 dB direct.

**Three suspected causes were tested and ruled out.**

1. **Port phase.** Removing the fitted port model (≈ 3 pH series, 1.5 fF shunt) changes nothing.
2. **50 Ω vs 37 Ω mismatch.** The block was renormalised to 36.66 Ω before chaining (`renorm.py`):
   $$Z = z_0(I+S)(I-S)^{-1}, \qquad S' = (Z-z_rI)(Z+z_rI)^{-1}.$$
   The dips remain.
3. **A/B asymmetry.** The block was symmetrised first, with $P$ the A↔B port swap (`symtest.py`):
   $$S_{\rm sym} = \tfrac12\left(S + PSP\right).$$
   The chained result changes by 0.0 dB.

**What remained.** The 5 mm crosstalk sits at its own error floor (§1), and the chained crosstalk near the 1 mm error floor. Chaining cannot fix either, so a method was needed that does not depend on 3-D crosstalk values.

---

## 3. The 2-D port-mode run

The 1 mm model was modified as follows:
- the lumped ports and PEC bars were removed;
- the protruding Si was trimmed;
- one waveguide port was placed covering both lines: 650 µm wide, from 300 µm above the metal to about 70 µm below the Si;
- the port edge was made a metal frame (electric shielding);
- the time-domain solver was run with "port modes only".

Each run is solved at one "mode calculation frequency": 6, 18, 30, 42 and 60 GHz.

**Number of modes.** With $N$ separate conductors there are $N-1$ quasi-TEM modes. Here there are 6 metal strips plus the frame, so 7 conductors and 6 modes. That is exactly what CST found.

There can't be more quasi-TEM modes. Any further mode has a cutoff frequency (a substrate or box mode). None appeared among the modes computed.

| Mode | β at 30 GHz (1/m) | $n$ | Field pattern (pictures in `modes_montage.png`) |
|---|---|---|---|
| 1 | 1517.63 | 2.414 | each whole line against the frame |
| 2 | 1462.87 | 2.327 | same, other symmetry |
| 3 | 1303.83 | 2.074 | a line's left ground against its right ground (slot) |
| 4 | 1293.67 | 2.058 | same, other symmetry |
| **5** | **1186.97** | **1.8878** | CPW field in the gaps, same sign on A and B: **even** |
| **6** | **1186.02** | **1.8863** | same, opposite sign: **odd** |

---

## 4. Why only modes 5 and 6 carry the crosstalk

Write the transverse state of the line as the voltages of the 6 strips relative to the frame, $\mathbf v\in\mathbb R^6$. The 6 modes form a basis, so any launch is a combination of them. The launch sets the amplitudes; propagation along a uniform line never mixes the modes.

The 3-D lumped-port launch imposes, at each end of each line:

1. **Both grounds of a line at the same potential, signal fed symmetrically between them.** The PEC bar ties them. The slot modes 3 and 4 need the two grounds of a line at *opposite* potentials, so their amplitude is zero. That removes 2 directions.
2. **The current leaving on a signal returns on that line's own grounds.** The port sits between signal and bar. Modes 1 and 2 carry net current on a line, returning through the frame or reference, so their amplitude is zero. That removes 2 more.

That leaves $6-2-2=2$ directions: "line A in its CPW mode" and "line B in its CPW mode". These are spanned by the even and odd pair modes 5 and 6. So for a single-line launch,

$$\mathbf v_{\rm launch}=(1,0)_{\rm A,B}=\tfrac12(1,1)+\tfrac12(1,-1)=\tfrac12\,\mathbf v_{\rm even}+\tfrac12\,\mathbf v_{\rm odd}.$$

**Caveats.**
- Each line is only *approximately* mirror-symmetric about its own signal, because the neighbour breaks the symmetry. A small conversion into modes 3 and 4 is therefore possible.
- The agreement of §8 suggests this conversion is small for straight lines.
- In the lab, the probe or pad must satisfy the same two conditions. Bends without ground bridges violate condition 1.

---

## 5. Even/odd impedance ratio from the exported fields

CST's "Line Impedance" is computed from the total power and the sum of all conductor currents. The help text says this "differs from the commonly used definition". It is not the line-A impedance, so it was not used for the split.

Instead (`port_voltages_sweep.py`):

1. **Export.** $E_y(x,y)$ of modes 5 and 6 on a 0.5 µm grid around the metal, at each frequency.
2. **Integrate.** On a grid row through the 2 µm-thick metal, integrate from the left:
   $$V(y) = -\int E_y\,dy .$$
   $E_y=0$ inside metal, so $V$ is constant on each strip: that is the strip potential.
3. **Line voltage.** Signal minus the mean of its own grounds:
   $$V_A = V_{S_A}-\tfrac12\left(V_{G_{A,\rm l}}+V_{G_{A,\rm r}}\right),$$
   and the same for $B$.
4. **Impedance ratio.** Both modes are normalised to the same power $P$. Each line carries $\lvert V\rvert^2/(2Z)$, so
   $$P=\frac{V_A^2+V_B^2}{2Z}\;\Rightarrow\;\frac{Z_e}{Z_o}=\frac{V_{A,e}^2+V_{B,e}^2}{V_{A,o}^2+V_{B,o}^2}.$$
   Using the sum $V_A^2+V_B^2$ also absorbs the ≈ 8 % A/B imbalance of each mode, which comes from the near-degenerate mode mixing (§1).

**Results.**

| | 6 | 18 | 30 | 42 | 60 GHz |
|---|---|---|---|---|---|
| $Z_e/Z_o-1$, rows inside metal (x = 0.5, 1.0, 1.5 µm) | 0.44 % | 0.44 % | 0.45 % | 0.45 % | 0.46 % |
| $Z_e/Z_o-1$, row at metal top (x = 2.0 µm) | 0.30 % | 0.30 % | 0.30 % | 0.30 % | 0.31 % |

The rows disagree because the field peaks sharply at the metal edges: a 1 µm grid gave 0.34–0.66 %, a 0.5 µm grid gives 0.30–0.45 %. **This spread is the uncertainty, and it is the reason the model is drawn as a band** (§7).

The absolute voltage depends on the unknown export normalisation, so only the ratio is used.

---

## 6. Index difference from β

From the info boxes of e5 and e6 (`portmode_betas.txt`), using $n=\beta c/(2\pi f)$:

| f (GHz) | $n_e$ | $n_o$ | $\Delta n$ |
|---|---|---|---|
| 6 | 1.88764 | 1.88614 | 0.00150 |
| 18 | 1.88770 | 1.88619 | 0.00151 |
| 30 | 1.88781 | 1.88630 | 0.00151 |
| 42 | 1.88799 | 1.88646 | 0.00152 |
| 60 | 1.88837 | 1.88680 | 0.00157 |

**The index offset.** The 3-D single line has $n=2.02\to1.93$ over the same band, with loss. The help text gives the reason: "lossy metal is treated as PEC" in the hexahedral port solver. So the 2-D modes miss the gold's internal inductance and loss. That's why the average comes from 3-D and only the *split* comes from 2-D (§7).

---

## 7. The model

### 7.1 One uniform line between 50 Ω ports

A line with impedance $Z$ and propagation constant $\gamma$, length $L$, between $z_0$ ports. Define

$$\Gamma=\frac{Z-z_0}{Z+z_0}, \qquad t=e^{-\gamma L}.$$

Summing the multiple reflections (a geometric series in $\Gamma^2t^2$) gives

$$S_{11}=\frac{\Gamma\,(1-t^2)}{1-\Gamma^2t^2}, \qquad S_{21}=\frac{(1-\Gamma^2)\,t}{1-\Gamma^2t^2}.$$

### 7.2 Two lines: even/odd superposition

Driving port 1 with port 3 idle is $\tfrac12$(even drive) + $\tfrac12$(odd drive) (§4). Each half sees a single line with its own $(Z,\gamma)$, so

$$
S_{11}=\tfrac12(S_{11}^e+S_{11}^o),\quad
S_{21}=\tfrac12(S_{21}^e+S_{21}^o),\quad
\boxed{S_{31}=\tfrac12(S_{11}^e-S_{11}^o)},\quad
\boxed{S_{41}=\tfrac12(S_{21}^e-S_{21}^o)}.
$$

That is all the model computes (`modal_vs_s4p_v3.py`).

### 7.3 What controls FEXT and NEXT

- **FEXT, matched case** ($\Gamma\approx0$):
  $$S_{41}=\tfrac12\left(e^{-j\beta_eL}-e^{-j\beta_oL}\right)\;\Rightarrow\;\lvert S_{41}\rvert=\left\lvert\sin\frac{(\beta_e-\beta_o)L}{2}\right\rvert\approx\frac{\pi f L\,\Delta n}{c}.$$
  It grows linearly with $f$ and $L$, and is set by $\Delta n$.
- **NEXT, small split** $Z_{e,o}=Z(1\pm\delta/2)$:
  $$S_{31}\approx\frac{\delta}{2}\,Z\frac{\partial S_{11}}{\partial Z}\propto \delta\,(1-t^2).$$
  It is set by $\delta=Z_e/Z_o-1$, and vanishes whenever $t^2=1$, i.e. $\beta L=m\pi$:
  $$f_m=\frac{m\,c}{2nL}\approx 15\text{ GHz}\cdot m\ \ (L=5\text{ mm}).$$
  **A uniform line must show these NEXT nulls.**

### 7.4 The three versions

| Version | Average line | Split | Figure |
|---|---|---|---|
| v1 | 2-D, 30 GHz: $n=1.888$, $Z=34.6$ Ω (from CST Z-Line × 2) | $\Delta n$ only, or CST Z-Line split (1.2 %) | `modal_vs_s4p.png` |
| v2 | same | $\Delta n$ + $\delta=0.30$–$0.45$ % | `modal_vs_s4p_v2.png` |
| **v3 (hybrid)** | **3-D single-line fit** $\gamma_{3D}(f)$, $Z_{3D}(f)$ (`cascade/three_lengths_results.npz`) | $\Delta\beta(f)$ from §6, $\delta$ from §5 | `modal_vs_s4p_v3.png` |

The hybrid sets

$$\gamma_{e,o}=\gamma_{3D}\pm\tfrac{j}{2}\Delta\beta(f), \qquad Z_{e,o}=Z_{3D}\left(1\pm\tfrac{\delta}{2}\right), \qquad \delta\in[0.30\,\%,\,0.45\,\%].$$

**The band.** The model is evaluated twice, with $\delta=0.30$ % and $\delta=0.45$ %, and the region between the two curves is shaded. FEXT depends weakly on $\delta$, so its band is thin. NEXT is proportional to $\delta$, so its band is about 3.5 dB thick ($20\log_{10}0.45/0.30$).

---

## 8. Comparison with the 3-D CST runs

Values in dB, CST / model (`modal_vs_s4p_v3.py`):

| | 6 GHz | 18 GHz | 30 GHz | 42 GHz | 60 GHz | Verdict |
|---|---|---|---|---|---|---|
| 1 mm NEXT | −70.8 / −69…−65 | −62.1 / −61…−57 | −59.6 / −58…−55 | −61.2 / −58…−54 | −61.4 / −59…−56 | 1–5 dB high |
| 1 mm FEXT | −80.8 / −97…−84 | −72.4 / −76…−72 | −70.6 / −67…−65 | −70.3 / −63…−61 | −59.0 / −59…−58 | good at 18 and 60 GHz |
| 5 mm FEXT | −66.8 / −68…−66 | −80.0 / −59 | −56.8 / −54 | −50.1 / −51 | −44.1 / −48 | envelope agrees; dips do not |
| 5 mm NEXT | −59.7 / −58…−55 | −64.5 / −68…−62 | −52.5 / −62…−61 | −48.1 / −57…−54 | −46.4 / −56…−55 | 6–10 dB low above 25 GHz |

**Reading.**
- **1 mm:** levels and trends agree. The 1 mm run has the lower error floor (−73 dB), so it is the reliable reference.
- **5 mm FEXT:** the envelope agrees. Single-frequency differences near a dip look large: at 18 GHz the CST curve is in a −80 dB dip that the model doesn't have.
- **5 mm NEXT above 25 GHz:** the model has the nulls of §7.3 (17, 33, 49 GHz); CST has none and rises smoothly to −46 dB. A uniform two-mode line cannot produce that. Either there is extra near-end coupling (port region, ground modes) or numerical error.
- **Why we can't decide yet:** the 5 mm error floor is −56 dB at 30 GHz, so the disputed CST values sit on it. The test is a 5 mm 3-D run with finer mesh around the ports.

## 9. Prediction for 14 mm

From the v3 model with $\delta=0.45$ % (`predict_14mm.py`):

| | 10 GHz | 30 GHz | 60 GHz |
|---|---|---|---|
| FEXT | −55 dB | −48 dB | −43 dB |
| NEXT (line only) | −58 dB | −57 dB | −54 dB |

**Correction:** an earlier estimate from the lossless 2-D line alone gave −46 and −40 dB for FEXT. Including the 3-D losses lowers it by about 2–3 dB.

---

## 10. Slow-wave (T-loaded) lines

**Still effectively uniform.** The tees repeat with period $p$ of a few tens of µm, far below the RF wavelength (several mm), and the first stop band sits near

$$f_B=\frac{c}{2np}\sim\text{THz}.$$

Over 0–60 GHz, the line therefore behaves as a uniform line with one effective $n$, $Z$, $\alpha$ (the Bloch-wave values).

**Still even + odd.** Two identical lines with aligned tees keep the A↔B mirror symmetry, so the pair modes are still even and odd, and §7 applies unchanged with Bloch $\gamma_{e,o}$, $Z_{e,o}$.

**What changes is how to get the four numbers.** A 2-D port sees one cross-section and cannot see the tees. Two options:

1. **3-D eigenmode solve of one period of both lines**, with periodic boundaries along $z$ and a phase shift $\phi=\beta p$. This gives $\beta_e$ and $\beta_o$ directly. Whether CST's eigenmode solver accepts the anisotropic LiNbO₃ needs checking.
2. **Short 3-D runs of $N$ and $2N$ periods.** Convert each 4-port to a 4 × 4 transfer matrix $T$ (as in `deembed4.py`). The eigenvalues of $T_N^{-1}T_{2N}$ are $e^{\pm\gamma_{e,o}Np}$, so the port regions cancel. The eigenvectors give the even/odd voltage patterns and the Bloch impedances.

Option 2 reuses tools already written. It needs only a few periods of geometry, so it stays far cheaper than a 14 mm run.

---

## Files

| Step | Script / data |
|---|---|
| 3-D error floor, pitch study | `pitch_compare.py`, `*.s4p` |
| Cascade and its tests | `cascade_naive.py`, `renorm.py`, `symtest.py`, `deembed4.py` |
| Mode voltages, impedance ratio | `port_voltages_05um.py`, `port_voltages_sweep.py`, `2D port simulation/*.zip` |
| β values | `portmode_betas.txt` |
| Model vs 3-D | `modal_vs_s4p.py` (v1), `modal_vs_s4p_v2.py`, `modal_vs_s4p_v3.py` |
| 14 mm prediction | `predict_14mm.py` |
| Slides | `crosstalk_cross_section.pptx` |
