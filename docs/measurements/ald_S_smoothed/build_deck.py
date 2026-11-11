"""ALD |S11| / |S21| deck: chip averages and Savitzky-Golay smoothed averages for the four wafers.
Run s_smoothed_plots.py first. Output: ALD_S_parameters_smoothed.pptx (6 slides)."""
import os, sys, csv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ald_cordoba8mm", "deck"))
from deck_helpers import *
HERE = os.path.dirname(os.path.abspath(__file__))   # deck_helpers also defines HERE
WAF = [("CORDOBA", "4CA0162", 8, 15), ("CORDOBA", "4CA0163", 8, 14), ("JEREZ", "6JZ0011", 8, 15), ("HELSINKI", "5HK0005", 13, 8)]
def figp(s, path, x, y, w, h):
    rect(s, x, y, w, h, fill=WHITE, line=BOX)
    W, H = Image.open(path).size; sc = min((w - .1) / W, (h - .1) / H); ww, hh = W * sc, H * sc
    s.shapes.add_picture(path, Inches(x + (w - ww) / 2), Inches(y + (h - hh) / 2), Inches(ww), Inches(hh))
st = list(csv.DictReader(open(os.path.join(HERE, "smoothing_stats.csv"))))
rms = lambda q, b: [float(r["rms_raw_minus_smoothed_dB"]) for r in st if r["S"] == q and r["band_GHz"] == b]

s = prs.slides.add_slide(L_TITLE)
text(s, 0, 2.2, 13.33, 1.4, ["RF impact of the Al_{2}O_{3} (ALD) layer:", "S_{11} and S_{21} before and after ALD"], size=34, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0, 3.75, 13.33, 0.8, "CORDOBA 4CA0162, 4CA0163 · JEREZ 6JZ0011 · HELSINKI 5HK0005 · chip averages, raw and smoothed", size=18, color=MUTED, align=PP_ALIGN.CENTER)

s = prs.slides.add_slide(L_BLANK)
title(s, "Savitzky–Golay smoothing", "Applied to the chip-averaged |S| (dB); the raw average is always shown with it")
figp(s, os.path.join(HERE, "smoothing_example.png"), 0.4, 1.55, 7.1, 3.75)
card(s, 7.75, 1.55, 5.15, 3.75, "Procedure", [
    "1. Raw average: mean over chips of |S| in dB at each frequency point (1601 points, 37.5 MHz spacing).",
    "2. For each point, a polynomial of order 3 is fitted by least squares to the 21 points centred on it (±10 points, 0.79 GHz).",
    "3. The smoothed value is the polynomial at the centre point; the window then moves by one point.",
    "At the band edges the polynomial of the first and last window is used (scipy.signal.savgol_filter)."], size=12.5)
card(s, 0.4, 5.5, 12.5, 1.55, "Choice of window", [
    "The window is short compared with the S_{11} ripple period (≈ 8.4 GHz for 8 mm lines, ≈ 5.1 GHz for 13 mm): S_{11} null depths below 20 GHz change by ≤ 0.1 dB.",
    f"Difference raw − smoothed (rms): S_{{11}} {min(rms('S11','1-20')):.2f}–{max(rms('S11','1-20')):.2f} dB below 20 GHz, {min(rms('S11','40-60')):.2f}–{max(rms('S11','40-60')):.2f} dB at 40–60 GHz; "
    f"S_{{21}} ≤ {max(rms('S21','40-60')):.2f} dB everywhere. The largest values come from HELSINKI no ALD, the noisiest set."], size=12.5)

for d, w, L, n in WAF:
    s = prs.slides.add_slide(L_BLANK)
    title(s, f"{d} {w}: |S_{{11}}| and |S_{{21}}|", f"{L} mm line · {n} chips measured before and after ALD · thin: raw average, thick: smoothed")
    figp(s, os.path.join(HERE, f"S11_{w}.png"), 0.35, 1.55, 6.25, 5.25)
    figp(s, os.path.join(HERE, f"S21_{w}.png"), 6.73, 1.55, 6.25, 5.25)
prs.save(os.path.join(HERE, "ALD_S_parameters_smoothed.pptx")); print("saved", len(prs.slides._sldIdLst), "slides")
