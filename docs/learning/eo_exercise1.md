# Exercise 1: EO crosstalk at 20 GHz from field data, on paper

Goal: compute the EO crosstalk $X = I_B/I_A$ yourself from a reduced data set, deriving every step. Ask for a hint
when stuck; do not ask for the method. When you have a number (magnitude in dB and phase), give it to Claude, who has
the answer key (not in the repository) and will only say how far off you are and in which step to look.

## Setting
- Two identical CPW lines, 8 mm long, along $z$ from 0 (driven end of line A) to 8 mm. Line A is centred at
  $y = +0.3125$ mm, line B at $y = -0.3125$ mm. Signal width 35 µm, gaps 4.15 µm.
- Each line feeds one MZM; push-pull: the two optical arms of a modulator sit in the two gaps of its line.
- RF drive: port at $z = 0$ of line A, 50 Ω everywhere. Frequency 20 GHz.
- Optical wave: travels in $+z$, group index $n_g = 2.27$. $c = 2.998\times10^8$ m/s.
- The phase that matters for the modulation is accumulated by the optical wave as it moves along the line while the
  RF field oscillates.

## Data: `eo_exercise1_data_20GHz.csv`
Eight blocks of 1 mm. For each block, the average complex phasor of $E_y$ (V/m, CST peak-phasor convention,
$e^{+j\omega t}$) at the centre of each gap, 1 µm above the LN, for both gaps of both lines. The column names give the
gap's $y$ position (mm). Note that $E_y$ is a component along $+y$, not a voltage.

## Tasks
1. **Derivation.** Write the phase shift accumulated by an optical wave entering at $z = 0$ at time $t_0$ and moving with
   $v = c/n_g$ through a region with field $\mathrm{Re}\{E(z)e^{j\omega t}\}$. Reduce it to a complex number times
   $e^{j\omega t_0}$ and identify the complex number. (This is $H$.)
2. **Push-pull.** For one line, write the two gap voltages from the two $E_y$ columns (decide the signs from the
   geometry) and how the two arms combine in push-pull. Which combination of the two columns survives?
3. **Discretise.** Replace the integral by a sum over the 8 blocks. State what you assume about the field and the
   kernel inside a block.
4. **Compute** $I_A$, $I_B$ and $X = I_B/I_A$: magnitude in dB and phase.
5. **Interpret.** Look at $|B|$ block by block. How does it grow along $z$? Use that to argue why $X$ comes out close to
   FEXT minus 6 dB (FEXT here is $|S_{41}| \approx -60$ dB at 20 GHz).
6. **Error.** Is 1 mm fine enough at 20 GHz? At 30 GHz? Give the criterion in terms of $n_g$, the index of the waves on
   line B, and the block length.
