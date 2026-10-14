# How we work: grounded results, not black boxes

Written after the arm-imbalance review (October 2026). It records what went
wrong, what the reviewers asked for, and the rules we follow from now on so
that everything presented can be defended from first principles.

## 1. What happened at the review

The reviewers (two directors, a manager, a senior RF designer) did not
question the numbers. They questioned the understanding behind them:

| Question | What was missing |
|---|---|
| "What exactly comes out of the TW block?" | Inputs, outputs and units of a block used in the work |
| "A Vπ imbalance can change the EO bandwidth" | The conditions under which a claim holds (true only if both arms have the same H(f)) |
| "Why does this eye shrink symmetrically, that one asymmetrically?" | A model predicting the direction and size of the effect |
| "Over-etch example without the Δn_g it produces" | The link from physical cause to the simulated parameter |

The manager's point: numbers come from simulations; **expected behaviour must
come from the engineer**. Simulation confirms or refutes an expectation. It
does not replace one. Experimental validation comes later; physical and
mathematical justification comes first.

## 2. The problem with the way we worked

Claude produced working code and plots quickly, but the derivations lived
inside the code. Results could be shown but not explained. Speed is not the
issue. The issue is that **ownership of the reasoning had moved to the tool**.
That is acceptable for plumbing (GUI, file I/O, INTERCONNECT automation). It
is not acceptable for physics that is presented or used for a decision.

## 3. The understanding threshold

A result is ready to present only when all five are true, without notes and
without Claude:

1. **Interface.** I can state the inputs and outputs of every block, with
   units and physical meaning.
2. **Derivation.** I can derive the governing equation on paper, every step,
   as in an exam.
3. **Prediction.** Before running, I can predict the sign, the scaling
   (linear, quadratic, √f…) and a rough magnitude.
4. **Limits.** I know what happens at zero imbalance, DC, lossless, matched,
   and the result agrees.
5. **Explanation.** I can explain it to a colleague in two minutes with a
   whiteboard, and answer "why?" twice in a row.

**Depth rule.** Equation level for anything presented or used for a decision.
Tooling may stay a black box provided it has passed tests against known
answers.

## 4. How we work from now on

**Derivation before code.** For each new physics block Claude writes the
derivation first, in `docs/`. I redo it on paper; Claude checks my version.
Code comes after.

**Code mirrors equations.** Each physics function cites the equation and
document it implements; variable names follow the derivation.

**Every script ships with limit checks**, e.g. "zero mismatch gives H = H₀",
"Vπ₁ = Vπ₂ gives no chirp", "DC gives the resistive divider". Trust comes
from checking, not from trusting Claude.

**Predict, then simulate.** Before each run I write down the expected
outcome. A mismatch is either a bug or a gap in understanding, and both get
resolved before the result is shown.

**Every claim has its conditions.** "X does not affect Y" is always written
as "X does not affect Y when …".

**Every example is linked to the model.** A physical example on a slide (an
over-etch) must be quantified through to the simulated parameter (Δn_g), or
left out.

**Picture first, then equations.** Every concept gets a mental image before
its maths: a physical example, an analogy or an illustration (for crosstalk:
the truck dropping balls, where the ones rolling with it pile up and the ones
rolling back form a queue). The derivation then makes the picture precise. A
formula without a picture is superficial understanding, and a picture without
its limits is a guess, so each analogy states where it stops being true. Depth
is chosen per topic: full derivation where the result is presented or drives
a decision; a correct picture is enough elsewhere.

**Claude explains, not only delivers.** When Claude introduces a formula or a
method, it states where it comes from, what it assumes and how to check it.
When I cannot follow, I ask until I can, before using it.

## 5. Not looking like a bullshitter

What separates an engineer from a bullshitter is not knowing everything. It
is the honesty and structure of the answer.

- **Answer from the mechanism, not from the plot.** "It shrinks because the
  bias moved off quadrature, so the midline shifts at first order while the
  amplitude drops only at second order" beats "it looks like it shrinks".
- **Separate what you know from what you assume.** Say "assumed", "simulated",
  "measured" explicitly; never blur them.
- **Say "I don't know" precisely.** "I have not checked how INTERCONNECT
  defines that output; I expect it is the photon-averaged voltage, and I will
  confirm" is credible. Improvising is not.
- **Never present a number you cannot reproduce by an order-of-magnitude
  estimate.** If the simulation and the hand estimate disagree, explain why
  before the meeting.
- **No unearned generalisations.** Prefer a narrower claim you can defend to a
  broad one you cannot.
- **Anticipate the questions.** For every slide, write the three hardest
  questions and their answers before the meeting.

## 6. Immediate plan

1. TW electrode block: derivation done (`docs/tw_electrode_derivation.md`).
   Redo it on paper, including its exercises.
2. Arm-imbalance eye models: Vπ/amplitude imbalance, bias error, split ratio,
   skew, group-index mismatch, each with closed-form level positions and
   predicted symmetric or asymmetric closure.
3. Vπ imbalance and EO bandwidth: the weighted-average H with its conditions.
4. Over-etch: mode-solver sweep of n_g against rib width and etch depth, or
   remove the example.
5. Revise the deck so that every result has its expected behaviour stated
   next to it.
