"""ALD RF impact: comparison of CORDOBA (4CA0162, 4CA0163), JEREZ (6JZ0011) and HELSINKI (5HK0005).
Inputs: out_<wafer>/summary_FOM.csv of each study (set "all"; 4CA0163 line 04 excluded there).
Outputs: change_comparison.png, ALD_RF_impact_comparison.pptx (4 slides)."""
import os, sys, csv
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); M = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(M, "ald_cordoba8mm", "deck"))
from deck_helpers import *
HERE = os.path.dirname(os.path.abspath(__file__))   # deck_helpers also defines HERE
WAF = [("CORDOBA", "4CA0162", "ald_cordoba8mm", 8, "#0E2268"), ("CORDOBA", "4CA0163", "ald_cordoba8mm", 8, "#5A7BD8"),
       ("JEREZ", "6JZ0011", "jerez", 8, "#1BAA7D"), ("HELSINKI", "5HK0005", "helsinki", 13, "#EB6834")]
KEYS = ["n_m", "Re Z0", "alpha (dB/cm) @ 30", "alpha (dB/cm) @ 60", "|S21| (dB) @ 30", "|S21| (dB) @ 60"]
R = {}
for d, w, fo, L, c in WAF:
    for r in csv.DictReader(open(os.path.join(M, fo, f"out_{w}", "summary_FOM.csv"))):
        if r["set"] != "all": continue
        k = next(k for k in KEYS if r["FOM"].startswith(k)); R[(w, k)] = r
g = lambda w, k, f: float(R[(w, k)][f])

# figure: median per-chip change with IQR
PAN = [("n_m", "Δn_m at 60 GHz", 1), ("Re Z0", "ΔRe Z0, band average (Ω)", 1), ("alpha (dB/cm) @ 30", "Δα at 30 GHz (dB/cm)", 1), ("alpha (dB/cm) @ 60", "Δα at 60 GHz (dB/cm)", 1)]
fig, ax = plt.subplots(1, 4, figsize=(15, 3.9))
for a, (k, lab, _) in zip(ax, PAN):
    for i, (d, w, fo, L, c) in enumerate(WAF):
        m, lo, hi = g(w, k, "median_change"), g(w, k, "IQR_change_lo"), g(w, k, "IQR_change_hi")
        a.errorbar(i, m, yerr=[[m - lo], [hi - m]], fmt="o", color=c, ms=8, capsize=4, lw=1.6)
    a.axhline(0, color="#5A606E", lw=0.9, ls="--"); a.set_xticks(range(len(WAF)))
    a.set_xticklabels([f"{d}\n{w}" for d, w, *_ in WAF], fontsize=9); a.set_title(lab, fontsize=11); a.grid(alpha=0.3, axis="y")
    a.set_xlim(-0.6, len(WAF) - 0.4)
fig.suptitle("Median per-chip change ALD − no ALD (bars: interquartile range)", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "change_comparison.png"), dpi=200); plt.close(fig)

new = lambda: prs.slides.add_slide(L_BLANK)
def figp(s, path, x, y, w, h):
    rect(s, x, y, w, h, fill=WHITE, line=BOX)
    W, H = Image.open(path).size; sc = min((w - .1) / W, (h - .1) / H); ww, hh = W * sc, H * sc
    s.shapes.add_picture(path, Inches(x + (w - ww) / 2), Inches(y + (h - hh) / 2), Inches(ww), Inches(hh))
N = {w: R[(w, "n_m")]["n"] for _, w, *_ in WAF}

# 1 title
s = prs.slides.add_slide(L_TITLE)
text(s, 0, 2.2, 13.33, 1.4, ["RF impact of the Al_{2}O_{3} (ALD) layer:", "CORDOBA, JEREZ and HELSINKI comparison"], size=34, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0, 3.75, 13.33, 0.8, "4 wafers · 52 chips measured before and after ALD · median per-chip change of n_{m}, Z_{0}, α, S_{21}", size=18, color=MUTED, align=PP_ALIGN.CENTER)

# 2 samples and reference values
s = new(); title(s, "Samples and values before ALD", "Same extraction and figures of merit for all wafers; medians over chips, no ALD")
rows = [["Design", "Wafer", "Line", "Chips", "n_{m} @ 60 GHz", "Z_{0} (Ω)", "α @ 30 GHz (dB/cm)", "α @ 60 GHz (dB/cm)"]]
for d, w, fo, L, c in WAF:
    rows.append([d, w, f"{L} mm", N[w], f"{g(w, 'n_m', 'median_noALD'):.3f}", f"{g(w, 'Re Z0', 'median_noALD'):.2f}",
                 f"{g(w, 'alpha (dB/cm) @ 30', 'median_noALD'):.2f}", f"{g(w, 'alpha (dB/cm) @ 60', 'median_noALD'):.2f}"])
table(s, 0.5, 1.6, 12.35, rows, [1.5, 1.4, 1.0, 0.9, 1.7, 1.4, 2.2, 2.2], size=13, row_h=0.6)
card(s, 0.5, 4.9, 12.35, 1.3, "Notes", ["Z_{0}: Re Z_{c} averaged over whole pad-ripple periods (10–42.8 GHz for 8 mm, 10–41.5 GHz for 13 mm).",
     "4CA0163 chip 04 excluded (bad ALD measurement). ALD thickness and process of JEREZ and HELSINKI not documented here."], size=13)

# 3 changes
s = new(); title(s, "Change after ALD", "Median per-chip change; chips up = chips with a higher value after ALD")
figp(s, os.path.join(HERE, "change_comparison.png"), 0.5, 1.5, 12.35, 3.35)
rows = [["Wafer", "Δn_{m} @ 60 GHz", "ΔZ_{0} (Ω)", "Δα @ 30 GHz", "Δα @ 60 GHz", "Δ|S_{21}| @ 30 GHz"]]
for d, w, fo, L, c in WAF:
    cell = lambda k, nd, u="": f"{g(w, k, 'median_change'):+.{nd}f}{u} ({R[(w, k)]['lines_up']}/{N[w]})"
    rows.append([f"{d} {w}", f"{cell('n_m', 3)}", cell("Re Z0", 2), cell("alpha (dB/cm) @ 30", 3), cell("alpha (dB/cm) @ 60", 3), cell("|S21| (dB) @ 30", 3, f" dB")])
table(s, 0.5, 5.0, 12.35, rows, [2.2, 1.9, 1.7, 1.9, 1.9, 2.4], size=11.5, row_h=0.38)

# 4 conclusions
s = new(); title(s, "Conclusions", "")
stat(s, 0.5, 1.45, 3.95, 2.2, "n_{m} ↑", "+0.4 to +1.7 % at 60 GHz, every chip of every wafer")
stat(s, 4.69, 1.45, 3.95, 2.2, "Z_{0} ↓", "−0.2 to −1.0 % (median), every wafer")
stat(s, 8.88, 1.45, 3.97, 2.2, "α: open", "Direction differs between designs and between fit and measured S_{21}", col=RED)
card(s, 0.5, 3.9, 6.05, 2.5, "Established", ["ALD adds capacitance: n_{m} increases and Z_{0} decreases on all four wafers.",
     "Size of the n_{m} increase depends on the design: CORDOBA +0.035 / +0.038, JEREZ +0.018, HELSINKI +0.010."], size=14)
card(s, 6.78, 3.9, 6.07, 2.5, "Open: attenuation", ["Fitted α at 60 GHz is sensitive to fit and data noise; the change is of the order of its uncertainty.",
     "Band-averaged measured S_{21} does not confirm the fitted direction on every wafer (JEREZ)."], hc=RED, size=14)
prs.save(os.path.join(HERE, "ALD_RF_impact_comparison.pptx")); print("saved", len(prs.slides._sldIdLst), "slides")
