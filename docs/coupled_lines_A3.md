# Coupled lines, part A3: the modes

Follows `coupled_lines_A1_A2.md`, which ended with the eigenvalue problem
$(\mathbf{Z}\mathbf{Y} - \gamma^2\mathbf{1})\mathbf{V}_0 = 0$. This note says
what its solutions are, how to use them, and what they mean physically.

Checks: `docs/coupled/check_A3.py` (numpy, scipy).

---

## 1. The picture: two pendulums joined by a spring

![Coupled pendulums](coupled/pendulums.png)

Two identical pendulums hang side by side, joined by a weak spring.

- **Mode 1, swinging together.** The spring is never stretched, so it does
  nothing. Each pendulum ticks at its natural rate.
- **Mode 2, swinging opposite.** The spring is stretched and compressed every
  swing, which adds a restoring force. They tick slightly faster.

These are the only two motions that repeat unchanged. They exist because of
the structure (two pendulums plus a spring), whether or not anyone moves them.

**Push only the left pendulum.** Its starting state is half of mode 1 plus
half of mode 2. The two halves tick at slightly different rates and slowly
drift out of step. As they do, the motion moves from the left pendulum to the
right one, and later back. That is called **beating**. The right pendulum was
never pushed: it moves because it is part of both modes.

**The translation to our lines:**

| Pendulums | Coupled lines |
|---|---|
| two pendulums | two signal lines (A = aggressor, B = victim) |
| spring | mutual capacitance $C_m$ and mutual inductance $L_m$ |
| swinging together | even mode, voltages $(1, 1)$ |
| swinging opposite | odd mode, voltages $(1, -1)$ |
| ticking rate | propagation constant $\gamma = \alpha + j\beta$ (rate of phase change **per metre**) |
| time | position $z$ along the line |
| motion moving to the right pendulum | crosstalk: voltage appearing on line B |

**Where the analogy stops.** Pendulums beat in *time*; our modes beat in
*space*, along the line. And our lines lose energy (the pendulums here do
not), so a long enough line damps everything before the beat completes (§5).

---

## 2. The modes, formally

### 2.1 Modes are eigenvectors

From A2, a voltage pattern that travels along the line keeping its shape,
$\mathbf{V}(z) = \mathbf{V}_0\,e^{-\gamma z}$, must satisfy

$$
\mathbf{Z}\mathbf{Y}\,\mathbf{V}_0 = \gamma^2\,\mathbf{V}_0 .
$$

So $\mathbf{V}_0$ is an **eigenvector** of the $2\times2$ matrix
$\mathbf{Z}\mathbf{Y}$ and $\gamma^2$ its **eigenvalue**. A $2\times2$ matrix
has two of each: two modes, with propagation constants $\gamma_1$ and
$\gamma_2$, and voltage patterns $\mathbf{t}_1$ and $\mathbf{t}_2$. Collect
them in a matrix and a diagonal matrix:

$$
\mathbf{T}_V = \begin{pmatrix} \mathbf{t}_1 & \mathbf{t}_2 \end{pmatrix},
\qquad
\boldsymbol{\Gamma} = \begin{pmatrix} \gamma_1 & 0 \\ 0 & \gamma_2 \end{pmatrix},
\qquad
\mathbf{Z}\mathbf{Y}\,\mathbf{T}_V = \mathbf{T}_V\,\boldsymbol{\Gamma}^2 .
$$

### 2.2 Identical lines: the modes are always $(1,1)$ and $(1,-1)$

For identical lines both matrices have the form
$\begin{pmatrix} a & b \\ b & a \end{pmatrix}$, and so does their product.
Then

$$
\begin{pmatrix} a & b \\ b & a \end{pmatrix}\begin{pmatrix} 1 \\ 1 \end{pmatrix} = (a + b)\begin{pmatrix} 1 \\ 1 \end{pmatrix},
\qquad
\begin{pmatrix} a & b \\ b & a \end{pmatrix}\begin{pmatrix} 1 \\ -1 \end{pmatrix} = (a - b)\begin{pmatrix} 1 \\ -1 \end{pmatrix}.
$$

The eigenvectors are $(1,1)$ and $(1,-1)$ **whatever** $a$ and $b$ are, so at
every frequency, with any loss. That is the symmetry argument in one line:
whatever A does to B, B does to A. The eigenvalues are the $z_e y_e$ and
$z_o y_o$ of A2 §3.

$$
\mathbf{T}_V = \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix},
\qquad
\gamma_e = \sqrt{z_e y_e},\quad \gamma_o = \sqrt{z_o y_o}.
$$

### 2.3 Unequal lines: still two modes, but lopsided

If the lines differ (width, gap, or one line next to a ground edge), the
diagonal entries differ and $(1, \pm 1)$ are no longer eigenvectors. There are
still exactly two modes, but each has its own voltage ratio
$\mathbf{t} = (1, R)$ with $R \neq \pm 1$, found numerically.

Example from the check script (one line 25 % more inductive, 20 % less
capacitive): the two modes are $(1,\ 0.032)$ and $(1,\ -41)$. Each mode lives
almost entirely on one line. **Picture:** two pendulums of different lengths
joined by a weak spring hardly exchange energy, because they never stay in
step. Unequal lines therefore couple less.

---

## 3. The general solution

Each mode travels forwards and backwards like a single line. Adding the four
possibilities:

$$
\mathbf{V}(z) = \mathbf{T}_V \left[ e^{-\boldsymbol{\Gamma} z}\,\mathbf{a}^{+} + e^{+\boldsymbol{\Gamma} z}\,\mathbf{a}^{-} \right],
$$

where $\mathbf{a}^{+}$ and $\mathbf{a}^{-}$ hold the forward and backward
amplitudes of the two modes (four numbers, fixed later by the terminations in
A4). This is the single-line $V(z) = V^+e^{-\gamma z} + V^-e^{\gamma z}$, with
two modes instead of one.

### 3.1 Characteristic impedance matrix

For a single line, a forward wave has $V = Z_c I$. For the pair, a forward
wave has $\mathbf{V} = \mathbf{Z}_c\,\mathbf{I}$ with a $2\times2$ matrix.
From $-d\mathbf{V}/dz = \mathbf{Z}\mathbf{I}$ applied to
$\mathbf{V} = \mathbf{T}_V e^{-\boldsymbol{\Gamma} z}\mathbf{a}^+$:

$$
\mathbf{Z}_c = \mathbf{T}_V\,\boldsymbol{\Gamma}^{-1}\,\mathbf{T}_V^{-1}\,\mathbf{Z}.
$$

For identical lines this simplifies to

$$
\mathbf{Z}_c = \frac12 \begin{pmatrix} Z_e + Z_o & Z_e - Z_o \\ Z_e - Z_o & Z_e + Z_o \end{pmatrix}.
$$

- **Diagonal** $\tfrac12(Z_e + Z_o)$: the impedance one line shows when the
  other carries no wave. With our numbers, $36.66\ \Omega$, essentially the
  single-line $Z_c$.
- **Off-diagonal** $\tfrac12(Z_e - Z_o)$: the coupling, $0.044\ \Omega$. In
  words, a forward current on line A comes with a small forward voltage on
  line B.

**Consequence for terminations (picture: a door that fits only one key).** A
termination absorbs all modes only if it equals $\mathbf{Z}_c$, off-diagonal
included. Two separate resistors to ground (each line ending in its own load)
can match the diagonal but not the off-diagonal term. So at a real end, one
mode reflects slightly differently from the other, and part of an even wave
comes back as odd, and vice versa: **mode conversion**. With
$Z_e - Z_o \approx 0.09\ \Omega$ it is tiny, but A4 includes it exactly.

### 3.2 Currents

The current patterns of the modes are the eigenvectors of
$\mathbf{Y}\mathbf{Z}$ (note the order). For reciprocal lines ($\mathbf{Z}$
and $\mathbf{Y}$ symmetric) they follow from the voltage patterns:
$\mathbf{T}_I = (\mathbf{T}_V^{-1})^{\mathsf T}$. For identical lines they are
again $(1,1)$ and $(1,-1)$ (up to scale).

---

## 4. Launching on one line only

At $z = 0$ the drive is $\mathbf{V} = (1, 0)$. Its modal content is
$\mathbf{T}_V^{-1}(1,0)^{\mathsf T}$:

$$
\begin{pmatrix} 1 \\ 0 \end{pmatrix} = \tfrac12\begin{pmatrix} 1 \\ 1 \end{pmatrix} + \tfrac12\begin{pmatrix} 1 \\ -1 \end{pmatrix}.
$$

Each half travels with its own $\gamma$. With matched ends (no backward
waves):

$$
V_A(z) = \tfrac12\left(e^{-\gamma_e z} + e^{-\gamma_o z}\right),
\qquad
V_B(z) = \tfrac12\left(e^{-\gamma_e z} - e^{-\gamma_o z}\right).
$$

Write $\bar\gamma = \tfrac12(\gamma_e + \gamma_o)$ and
$\delta = \tfrac12(\gamma_o - \gamma_e)$. Then

$$
V_A(z) = e^{-\bar\gamma z}\cosh(\delta z),
\qquad
V_B(z) = e^{-\bar\gamma z}\sinh(\delta z).
$$

For a lossless pair $\delta = j\,\Delta\beta/2$ and these are
$\cos(\Delta\beta z/2)$ and $j\sin(\Delta\beta z/2)$: the pendulum beat, in
space. The victim-to-aggressor ratio is

$$
\left|\frac{V_B}{V_A}\right| = \left|\tan\frac{\Delta\beta\,z}{2}\right| \approx \frac{|\Delta\beta|\,z}{2}
\quad\text{for short lines,}
$$

the linear growth of far-end crosstalk with length from A1 (the truck and the
balls), now derived.

---

## 5. Numbers for our pair

With the first-look values from the 1 mm file ($n_o - n_e \approx 2\times10^{-4}$):

| $f$ | Length for complete transfer to B (half a beat) | $\lvert V_B/V_A\rvert$ at 14 mm |
|---|---|---|
| 10 GHz | 75 m | $2.9\times10^{-4}$ ($-71$ dB) |
| 30 GHz | 29 m | $7.5\times10^{-4}$ ($-62$ dB) |

The beat is **tens of metres** long; our electrodes are millimetres. We only
ever see the very first, straight part of the beat, which is why the far-end
crosstalk grows in proportion to length. Loss (2–4 dB/cm) kills both signals
long before the beat could complete.

Unvalidated: one length, CST port regions included (see A1–A2 §4).

---

## 6. Checks (`check_A3.py`)

- Identical lines: the numerical eigenvectors of $\mathbf{Z}\mathbf{Y}$ are
  $(1,1)$ and $(1,-1)$ to $10^{-12}$; the current eigenvectors equal
  $(\mathbf{T}_V^{-1})^{\mathsf T}$.
- $\mathbf{Z}_c$ from the general formula has diagonal $36.662 - 1.016j\ \Omega$
  and off-diagonal $0.044\ \Omega$, giving back $Z_e$ and $Z_o$.
- Forward waves only: launch $\mathbf{I} = \mathbf{Z}_c^{-1}\mathbf{V}$ and
  integrate the telegrapher's equations over 14 mm with no modes assumed.
  $\mathbf{V} = \mathbf{Z}_c\mathbf{I}$ still holds to $10^{-15}$, for
  identical and for unequal lines.
- Unequal lines: modes $(1,\ 0.032)$ and $(1,\ -41)$.

## 7. Exercises

1. Show that $(1,1)$ and $(1,-1)$ are eigenvectors of any matrix
   $\begin{pmatrix} a & b \\ b & a \end{pmatrix}$, and find the eigenvalues.
2. Derive $\mathbf{Z}_c$ for identical lines from
   $\mathbf{Z}_c = \mathbf{T}_V\boldsymbol{\Gamma}^{-1}\mathbf{T}_V^{-1}\mathbf{Z}$.
3. Derive $V_A = e^{-\bar\gamma z}\cosh\delta z$ and
   $V_B = e^{-\bar\gamma z}\sinh\delta z$ from the two exponentials.
4. *Picture.* Explain with the pendulums why unequal lines couple less.
5. *Predict.* If $n_o > n_e$, does the victim's far-end voltage lead or lag
   the aggressor's by 90°? (Use §4.)
