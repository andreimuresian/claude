# EO crosstalk from fields: toy problems (P1 to P7)

Work on paper. Check each answer with the checker (no solution is shown unless you ask for it):

    python3 docs/learning/check.py P3 -36.0          # one number
    python3 docs/learning/check.py P2 0.98 0.05      # several numbers, in the order the problem asks
    python3 docs/learning/check.py hint P3 1         # hint level 1 (nudge), 2 (key idea), 3 (the step)
    python3 docs/learning/check.py solution P3       # full worked solution (asks for confirmation)

The checker knows a few typical wrong results and tells you which step to look at. Hints and solutions are stored
encoded in `keys.dat`, so you cannot read them by accident.

Common data for all problems (unless a problem says otherwise):
- Line length $L = 8.75$ mm, along $z$ from $0$ to $L$. Light enters at $z = 0$ and travels in $+z$.
- Optical group index $n_g = 2.27$, $c = 299\,792\,458$ m/s.
- Phasors use CST's convention: a field is $\mathrm{Re}\{E(z)\,e^{+j\omega t}\}$.
- The local index change of an optical arm is proportional to the instantaneous $E_y$ in its gap.

---

**P1. Light passing through a field that oscillates in place.**
On line A, the field in the gap is the same at every $z$: $E(z) = E_0$, at $f = 20$ GHz.
Light takes a finite time to cross the line, and the field changes while it travels.

Define the efficiency $\eta$ as the amplitude of the oscillating optical phase, divided by the amplitude that
the light would get if it saw the peak field $E_0$ over the whole length $L$.

Enter $\eta$ (a number between 0 and 1).

**P2. Travelling waves, forward and backward.**
The field is now a wave $E(z) = E_0\,e^{-j\beta_m z}$ with $\beta_m = 2\pi f n_m/c$, $n_m = 2.20$ and $f = 50$ GHz.

Enter two numbers:
1. $\eta$ for this wave;
2. $\eta$ for the same wave travelling backward, $E(z) = E_0\,e^{+j\beta_m z}$.

What do the two numbers say about which waves on the victim line can modulate its light?

**P3. A FEXT-like wave on the victim line (single arm, velocities matched).**
- Line A carries $E_A(z) = E_0\,e^{-j\beta_m z}$ with $n_m = n_g$, at $f = 40$ GHz.
- Line B carries a forward wave whose amplitude grows linearly from zero, as far-end crosstalk does:
  $E_B(z) = \kappa\,(z/L)\,E_0\,e^{-j\beta_m z}$.
- At the far end, $|E_B(L)/E_A(L)|$ is $-30$ dB.
- Each modulator has a single arm, in the gap where these fields are given.

Enter the EO crosstalk $|X| = |\text{response of modulator B} / \text{response of modulator A}|$, in dB.

**P4. The same, with velocity mismatch.**
Same as P3, but $n_m = 2.00$ and $f = 60$ GHz.

Enter two numbers:
1. $\eta$ of line A alone;
2. $|X|$ in dB.

Why does $|X|$ move in the direction it does compared with P3?

**P5. FEXT and NEXT together.**
Same as P3 ($n_m = n_g$, $f = 40$ GHz). Line B now also carries a backward wave of constant amplitude, at the
same level as the far-end value of the forward wave: $\kappa E_0\,e^{+j\beta_m z}$ with $|\kappa| = -30$ dB.

Enter $|X|$ in dB. How much of it is due to the backward wave?

**P6. Push-pull: which combination of the two gaps?**
Each line is a CPW (coplanar waveguide) with one optical arm in each gap. The crystal axis is along $+y$ in both
arms, so $\Delta n \propto +E_y$ in both. The MZM (Mach-Zehnder modulator) responds to the phase difference
between its two arms.

All fields below have the same $z$ dependence, so the propagation factors cancel. The values are $E_y$ phasors
in units of $E_0$:

| | Gap on the $+y$ side | Gap on the $-y$ side |
|---|---|---|
| Line A | $1.00$ | $-0.96$ |
| Line B | $0.020 + 0.010j$ | $0.012 - 0.004j$ |

Enter $|X|$ in dB and the phase of $X$ in degrees.

**P7. Real data: eight blocks, 20 GHz (Cordoba geometry).**
Use `eo_exercise1_data_20GHz.csv` and the setting in `eo_exercise1.md`:
- $L = 8$ mm;
- line A is centred at $y = +0.3125$ mm, line B at $y = -0.3125$ mm;
- $f = 20$ GHz;
- the CSV gives $E_y$ in each gap, averaged over 1 mm blocks.

Enter $|X|$ in dB and its phase in degrees.

In your notes, state what you assumed inside each block, and whether that assumption matters for $X$.
