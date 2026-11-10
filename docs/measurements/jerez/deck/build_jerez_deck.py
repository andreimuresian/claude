"""ALD RF impact on JEREZ 8 mm lines (wafer 6JZ0011): short deck in the company template (python-pptx).
Helpers and template from ../../ald_cordoba8mm/deck/deck_helpers.py. Inputs: ../out_6JZ0011/*, ../v2_box_wafer_medians.png
(wafer_analysis.py, figs_v2.py, box_both_medians.py in ../../ald_cordoba8mm). Output: ../ALD_RF_impact_JEREZ.pptx"""
import os, sys, csv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ald_cordoba8mm", "deck"))
from deck_helpers import *
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); P = lambda *a: os.path.join(D, *a)
new = lambda: prs.slides.add_slide(L_BLANK)
def figp(s, path, x, y, w, h):
    rect(s, x, y, w, h, fill=WHITE, line=BOX)
    W, H = Image.open(path).size; sc = min((w - .1) / W, (h - .1) / H); ww, hh = W * sc, H * sc
    s.shapes.add_picture(path, Inches(x + (w - ww) / 2), Inches(y + (h - hh) / 2), Inches(ww), Inches(hh))
W = "6JZ0011"
S = {r["FOM"]: r for r in csv.DictReader(open(P(f"out_{W}", "summary_FOM.csv"))) if r["set"] == "all"}
FOMS = ["n_m @ 60 GHz", "Re Z0 (ohm), 10-43 GHz avg", "alpha (dB/cm) @ 30 GHz", "alpha (dB/cm) @ 60 GHz", "|S21| (dB) @ 30 GHz", "|S21| (dB) @ 60 GHz"]
LBL = ["n_{m} @ 60 GHz", "Z_{0} (Ω), 10–43 GHz avg", "α (dB/cm) @ 30 GHz", "α (dB/cm) @ 60 GHz", "|S_{21}| (dB) @ 30 GHz", "|S_{21}| (dB) @ 60 GHz"]
def row(l, q, nd):
    r = S[q]; a, b, d = float(r["median_noALD"]), float(r["median_ALD"]), float(r["median_change"])
    return [l, f"{a:.{nd}f}", f"{b:.{nd}f}", f"{d:+.{nd}f}", f"{r['lines_up']}/{r['n']}"]

# 1 title
s = prs.slides.add_slide(L_TITLE)
text(s, 0, 2.2, 13.33, 1.4, ["RF impact of the Al_{2}O_{3} (ALD) layer", "on JEREZ 8 mm lines"], size=36, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0, 3.75, 13.33, 0.8, "Wafer 6JZ0011 · 15 chips measured before and after ALD · n_{m}, Z_{0}, α, S_{21}", size=18, color=MUTED, align=PP_ALIGN.CENTER)

# 2 samples and method
s = new(); title(s, "Samples and method", "Same extraction and figures of merit as the CORDOBA ALD study")
card(s, 0.5, 1.55, 4.0, 2.4, "Samples", ["Wafer 6JZ0011, 15 chips, one 8 mm line each.", "Same chip measured before and after ALD: paired comparison."], size=13)
card(s, 0.5, 4.1, 4.0, 2.75, "Measurement", ["2-port VNA, 40 MHz–60 GHz, 1601 points, 50 Ω.",
     "All 30 files pass the checks: reciprocity 0.8–1.1 % (median), passivity ≤ 0.92. No chip excluded."], size=13)
table(s, 4.75, 1.55, 8.1, [["FOM", "Value per chip"], ["n_{m}", "saturating dispersion fit, at 60 GHz"],
      ["Z_{0}", "Re Z_{c}, mean over 10.0–42.8 GHz (4 pad-ripple periods)"], ["α", "fit a√f + b f + c (a, b ≥ 0), at 30 and 60 GHz"],
      ["S_{21}", "fitted line between 50 Ω ends, at 30 and 60 GHz"]], [1.2, 6.9], size=12.5, row_h=0.5)
card(s, 4.75, 4.25, 8.1, 2.6, "Extraction", ["ABCD de-embedding of each 2-port as one uniform line, L = 8 mm (pads included, same bias before and after ALD).",
     "Reported change: median of the per-chip difference ALD − no ALD."], size=13)

# 3 curves and per-chip values
s = new(); title(s, f"Wafer {W}: results", "Chip means with fits (left) · per-chip values, before (o) and after (s) (right)")
figp(s, P(f"out_{W}", "mean_fit_panel.png"), 0.4, 1.5, 5.6, 5.35)
figp(s, P(f"out_{W}", "boxplots_FOM.png"), 6.15, 1.5, 6.8, 5.35)

# 4 summary table + n_m, Z0 boxplots
s = new(); title(s, "Median change after ALD", "15 chips; Up = chips with a higher value after ALD")
table(s, 0.5, 1.55, 6.2, [["FOM", "No ALD", "ALD", "Change", "Up"]] + [row(l, q, 2 if "Z0" in q else 3) for l, q in zip(LBL, FOMS)],
      [2.2, 1.0, 1.0, 1.1, 0.9], size=12, row_h=0.55, hl=(1, 3))
text(s, 0.5, 5.6, 6.2, 1.2, "Z_{0} changes below about 0.5 Ω are not resolved (pad ripple); α at 60 GHz carries about ±0.07 dB/cm (CORDOBA fit check).", size=12, color=MUTED)
figp(s, P("v2_box_wafer_medians.png"), 6.95, 1.55, 5.9, 3.2)
figp(s, P(f"out_{W}", "v2_S21.png"), 6.95, 4.9, 5.9, 2.0)

# 5 conclusions
s = new(); title(s, "Conclusions", "")
stat(s, 0.5, 1.45, 3.95, 2.2, "n_{m} ↑", "+0.8 % at 60 GHz (+0.018), every chip")
stat(s, 4.69, 1.45, 3.95, 2.2, "Z_{0} ↓", "Median per-chip decrease after ALD")
stat(s, 8.88, 1.45, 3.97, 2.2, "α: open", "Change of the order of the fit uncertainty", col=RED)
card(s, 0.5, 3.9, 6.05, 2.5, "Established", ["ALD adds capacitance: n_{m} increases and Z_{0} decreases."], size=14)
card(s, 6.78, 3.9, 6.07, 2.5, "Open: attenuation", ["Fitted α depends on the fit and on the data noise.",
     "To be checked against the band-averaged measured S_{21} (no fit)."], hc=RED, size=14)
prs.save(P("ALD_RF_impact_JEREZ.pptx")); print("saved", len(prs.slides._sldIdLst), "slides")
