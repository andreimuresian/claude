"""ALD RF impact on CORDOBA 8 mm lines: slide deck in the company template (python-pptx).
Inputs: the figures and CSVs produced by ../wafer_analysis.py, ../compare_wafers.py and ../fit_check*.py.
Output: ../ALD_RF_impact.pptx"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck_helpers import *          # prs (template, slides removed), text, title, rect, card, stat, table, arrow, ...
D = os.path.join(HERE, "..")
P = lambda *a: os.path.join(D, *a)
new = lambda: prs.slides.add_slide(L_BLANK)


def figp(s, path, x, y, w, h):
    rect(s, x, y, w, h, fill=WHITE, line=BOX)
    W, H = Image.open(path).size; sc = min((w - .1) / W, (h - .1) / H); ww, hh = W * sc, H * sc
    s.shapes.add_picture(path, Inches(x + (w - ww) / 2), Inches(y + (h - hh) / 2), Inches(ww), Inches(hh))


def box(s, x, y, w, h, head, sub, fill=CARD, hc=NAVY, size=12.5):
    rect(s, x, y, w, h, fill=fill, line=BOX)
    text(s, x + .1, y + .07, w - .2, h - .1, [(head, {"bold": True, "color": hc, "size": size + 1})] + [(t, {"size": size}) for t in sub], sa=2)


S = {}
for w in ("4CA0162", "4CA0163"):
    for r in csv.DictReader(open(P(f"out_{w}", "summary_FOM.csv"))):
        S[(w, r["set"], r["FOM"])] = r
def ch(w, st, q, nd=3):
    r = S[(w, st, q)]; return f"{float(r['median_change']):+.{nd}f} ({r['lines_up']}/{r['n']} up)"
FOMS = ["n_m @ 60 GHz", "Re Z0 (ohm), 10-43 GHz avg", "alpha (dB/cm) @ 30 GHz", "alpha (dB/cm) @ 60 GHz", "|S21| (dB) @ 30 GHz", "|S21| (dB) @ 60 GHz"]
LBL = ["n_{m} @ 60 GHz", "Z_{0} (Ω), 10–43 GHz avg", "α (dB/cm) @ 30 GHz", "α (dB/cm) @ 60 GHz", "|S_{21}| (dB) @ 30 GHz", "|S_{21}| (dB) @ 60 GHz"]

# 1 title
s = prs.slides.add_slide(L_TITLE)
text(s, 0, 2.2, 13.33, 1.4, ["RF impact of the 40 nm Al_{2}O_{3} (ALD) layer", "on CORDOBA 8 mm lines"], size=36, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0, 3.75, 13.33, 0.8, "Wafers 4CA0162 and 4CA0163 · 15 lines each · measured before and after ALD · n_{m}, Z_{0}, α, S_{21}",
     size=18, color=MUTED, align=PP_ALIGN.CENTER)

# 2 setup
s = new(); title(s, "Device and measurement set", "CORDOBA push-pull GSG line, 8 mm, coated with 40 nm Al_{2}O_{3}")
figp(s, P("cordoba_cross_section_ald.png"), 0.45, 1.55, 8.2, 4.75)
card(s, 8.85, 1.55, 4.05, 2.35, "Samples", ["2 wafers: **4CA0162**, **4CA0163**", "15 fields per wafer, one 8 mm line each",
     "Same line measured **before** and **after** ALD"], size=12.5)
card(s, 8.85, 4.05, 4.05, 2.25, "Measurement", ["2-port VNA, 40 MHz–60 GHz, 1601 points, 50 Ω", "File checks: reciprocity < 1 %, passivity OK",
     "Excluded: 4CA0163 line 04 (bad ALD file)"], size=12.5)
text(s, 0.5, 6.45, 12.4, 0.5, "Signal 35 µm, gaps 4.15 µm, grounds 49.85 µm, gold 2 µm; ALD conformal on gold walls, SiO_{2} cap and LN slab.", size=12, color=MUTED)

# 3 extraction
s = new(); title(s, "Figures of merit from the Touchstone file", "ABCD de-embedding of the measured 2-port as one uniform line, L = 8 mm")
for i, (h, b) in enumerate((("Touchstone", ["S_{11}, S_{21}, S_{12}, S_{22}"]), ("ABCD", ["A, B, C from the S-matrix", "Z_{ref} = 50 Ω"]),
                            ("Line", ["Z_{c} = √(B/C)", "e^{γL} = A + B/Z_{c}"]), ("Figures of merit", ["α = Re γ (dB/cm)", "n_{m} = c·Im γ / ω", "Z_{0} = Re Z_{c}"]))):
    box(s, 0.5 + i * 3.2, 1.6, 2.75, 1.75, h, b, size=13)
    if i < 3: arrow(s, 3.3 + i * 3.2, 2.3, 0.35)
card(s, 0.5, 3.65, 6.1, 2.95, "S_{21} and S_{11}", ["Measured values, no processing.", "S_{21} in the boxplots: computed from the fitted line",
     "(α, n_{m}, Z_{c}) between 50 Ω ends → the trend, not the pad ripple."], size=13)
card(s, 6.8, 3.65, 6.1, 2.95, "Limit: pads are part of the 2-port", ["Pad/probe reflections travel the 8 mm line:",
     "ripple with period c / (2 n_{m} L) ≈ 8.2 GHz, mostly in Z_{c}.", "After ALD: ripple 0.6 → 2.3 Ω (std), both wafers."], hc=RED, size=13)

# 4 averaging and fitting
s = new(); title(s, "Line averaging and fits", "Fits on each line; the line mean is shown only for display")
table(s, 0.5, 1.55, 6.4, [["FOM", "Fit on each line", "Why"],
      ["α", "a√f + b f + c, a, b ≥ 0", "conductor + dielectric; physical"],
      ["n_{m}", "saturating dispersion", "bounded, no run-away"],
      ["Z_{0}", "mean over 10.0–42.8 GHz", "4 ripple periods: ripple cancels"],
      ["S_{21}", "from the fitted line, 50 Ω", "trend, not pad ripple"]], [1.0, 2.6, 2.8], size=11.5, row_h=0.5)
card(s, 0.5, 4.25, 6.4, 2.6, "Line mean (curves in frequency)", ["At each frequency: plain mean over the lines,",
     "separately before / after ALD (dB values for S-parameters).", "Thick: mean of the per-line fits; dots: values used in the boxplots.",
     "Robust fit (soft-L1): ripple and spikes do not steer it."], size=12.5)
figp(s, P("out_4CA0162", "mean_fit_panel.png"), 7.1, 1.55, 5.8, 5.3)

# 5 value extraction for the boxplots
s = new(); title(s, "One value per line, then boxplots", "Single-point values from the fits; checked for stability and bias")
table(s, 0.5, 1.55, 7.2, [["FOM", "Value per line", "Stability*", "Bias**"],
      ["n_{m}", "fit @ 60 GHz", "≤ 0.002", "≤ 0.004"],
      ["Z_{0}", "raw mean 10–43 GHz", "≤ 0.11 Ω†", "—"],
      ["α", "fit @ 30 GHz", "≤ 0.003 dB/cm", "±0.02 dB/cm"],
      ["α", "fit @ 60 GHz", "0.03–0.07 dB/cm", "−0.06…−0.09 dB/cm"],
      ["S_{21}", "fitted line @ 30, 60 GHz", "follows α", "follows α"]], [0.9, 2.6, 1.8, 1.9], size=11.5, row_h=0.48)
text(s, 0.5, 4.5, 7.2, 0.9, ["* change when the fit stops at 50 GHz   ** raw data near the point minus the fit",
     "† change of the ALD shift for a band moved by half a period or one period shorter"], size=10.5, color=MUTED)
card(s, 7.95, 1.55, 4.95, 2.45, "Why 30 and 60 GHz", ["60 GHz: top of the band, requested reference.", "30 GHz: ≥ 10× more stable for α.",
     "Z_{0} fitted at 60 GHz is off by 2–4 Ω (ripple): not used."], size=12.5)
card(s, 7.95, 4.2, 4.95, 2.65, "Boxplot", ["Box: median, quartiles; whiskers 1.5 × IQR.", "Each line one colour, before (o) → after (s).",
     "Reported: median of the per-line change (paired), not the change of the medians."], size=12.5)

# 6, 7 wafers
for w, n in (("4CA0162", 15), ("4CA0163", 14)):
    s = new(); title(s, f"Wafer {w}: results", f"{n} lines" + (" (line 04 excluded)" if w == "4CA0163" else "") + " · line means with fits (left) · per-line values (right)")
    figp(s, P(f"out_{w}", "mean_fit_panel.png"), 0.4, 1.5, 5.6, 5.15)
    figp(s, P(f"out_{w}", "boxplots_FOM.png"), 6.15, 1.5, 6.8, 5.15)
    text(s, 0.45, 6.75, 12.5, 0.4, "Median change: " + " · ".join(f"{l.split(' (')[0].split(' @')[0]} {ch(w, 'all', q, 2 if 'Z0' in q else 3).split(' (')[0]}"
         + (" @30" if "30" in q else (" @60" if "60" in q and "n_m" not in q else "")) for l, q in zip(LBL, FOMS)), size=11.5, color=MUTED)

# 8 comparison
s = new(); title(s, "Wafer comparison and the high-loss lines", "Per-line change ALD − no ALD: median (lines that went up / lines)")
rows = [["FOM", "4CA0162 (15)", "4CA0162 w/o 00, 04 (13)", "4CA0163 (14)"]]
for l, q in zip(LBL, FOMS):
    nd = 2 if "Z0" in q else 3
    rows.append([l, ch("4CA0162", "all", q, nd), ch("4CA0162", "without 00,04", q, nd), ch("4CA0163", "all", q, nd)])
table(s, 0.45, 1.5, 6.6, rows, [1.9, 1.55, 1.75, 1.55], size=10.5, row_h=0.44, hl=(4,))
card(s, 0.45, 4.75, 3.2, 2.1, "Agree", ["n_{m} up on every line", "Z_{0} down on every line", "α @ 30 GHz up on every line"], hc=GREEN, size=12)
card(s, 3.85, 4.75, 3.2, 2.1, "Differ", ["α increase ≈ 4× larger on 4CA0162", "α @ 60 GHz: +0.21 vs −0.06", "(−0.06 within the ±0.07 uncertainty)"], hc=RED, size=12)
figp(s, P("compare_wafers.png"), 7.25, 1.5, 5.7, 3.4)
card(s, 7.25, 5.05, 5.7, 1.8, "High-loss lines 00, 04 (4CA0162)", ["~2–3 dB/cm more loss at 60 GHz, before and after ALD.",
     "Removing them: n_{m}, Z_{0}, α @ 30 GHz unchanged; α @ 60 GHz 0.21 → 0.16 dB/cm."], size=12)

# 9 conclusions
s = new(); title(s, "Conclusions: measured effect of 40 nm ALD", "Same effect on every line where it exceeds the uncertainty; loss increase is wafer-dependent")
stat(s, 0.5, 1.6, 3.95, 2.25, "+1.5–1.7 %", "n_{m} (+0.035 / +0.038 at 60 GHz), every line, both wafers")
stat(s, 4.69, 1.6, 3.95, 2.25, "−0.6–1.0 %", "Z_{0} (−0.41 / −0.26 Ω, 10–43 GHz), every line, both wafers")
stat(s, 8.88, 1.6, 3.95, 2.25, "+1.4–6 %", "α at 30 GHz (+0.06 / +0.26 dB/cm), every line; size differs by wafer", col=RED)
card(s, 0.5, 4.1, 6.05, 2.75, "Reading", ["ALD adds capacitance: n_{m} up, Z_{0} down (consistent signs).", "Loss: up at 30 GHz on both wafers; at 60 GHz the change",
     "is within ±0.07 dB/cm on 4CA0163.", "S_{21} (8 mm): −0.20 / −0.04 dB at 30 GHz."], size=12.5)
card(s, 6.78, 4.1, 6.05, 2.75, "Open points", ["Why the loss increase differs by wafer: same ALD run?", "same measurement session (probes, calibration)?",
     "Pad/probe ripple grows after ALD (0.6 → 2.3 Ω) on both wafers.", "Z_{0} at 60 GHz not resolvable from these structures."], hc=RED, size=12.5)

prs.save(P("ALD_RF_impact.pptx")); print("saved", len(prs.slides._sldIdLst), "slides")
