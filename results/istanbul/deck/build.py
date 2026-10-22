"""Istanbul 2-slide deck in the AFR template.  Run: python3 build.py"""
import sys, json, shutil, os
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
H = "/home/user/claude/results/istanbul/"
RED = RGBColor(0xC0, 0x39, 0x2B)
R = sorted((json.loads(l[7:]) for l in open(H + "results.txt") if l.startswith("RESULT")), key=lambda r: r["slab_w"])
first_new = len(prs.slides)

# 1 --------------------------------------------------------------------------
s = new("Istanbul: cross-section and nominal result", "C-band tapeout, simulated at 1575 nm, gap 4.45 µm, slab 10.15 µm")
image(s, H + "deck/xs_top.png", 0.6, 1.85, w=7.6)
box(s, 8.6, 1.85, 4.2, 2.5, [("Geometry", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    ("LN rib 1.0 µm top, 275 nm etch, 275 nm slab", {"size": 12, "space": 4}),
    ("SiO₂ cap 2.0 × 1.4 µm", {"size": 12, "space": 4}),
    ("Gold 2.0 µm, conformal: drops 275 nm past the slab end", {"size": 12, "space": 4}),
    ("Slab ends 2.85 µm inside the gold", {"size": 12})])
stat(s, 0.9, 4.75, 3.4, 1.2, "0.092 dB/cm", "insertion loss at nominal", RED)
stat(s, 4.6, 4.75, 3.4, 1.2, "2.42 V·cm", "Vπ·L at nominal", NAVY)
table(s, [["Same cavity (2.85 µm)", "Gap", "IL (dB/cm)"], ["Cordoba etched, flat gold", "4.20 µm", "0.209"],
          ["Cordoba etched, flat gold", "4.45 µm", "0.092"], ["Istanbul, stepped gold", "4.45 µm", "0.092"]],
      8.6, 4.6, 4.2, [2.2, 0.9, 1.1], size=11, highlight=(3,))
text(s, 0.9, 6.2, 11.9, 0.8, [("Low loss comes from the wider gap (field at the gold ≈ halved per +0.125 µm per side); "
     "the 275 nm gold step has no effect. Vπ·L pays +7 % vs Cordoba (2.27 V·cm).", {"size": 13, "color": MUT})])

# 2 --------------------------------------------------------------------------
s = new("Slab-width sweep: strong IL ripples, flat Vπ·L", "Slab width from gap + 1 to gap + 8 µm, 100 nm step (71 points)")
xy_chart(s, 0.6, 1.8, 8.2, 4.4, [("IL", [(r["slab_w"], r["IL_dBcm"]) for r in R], RED, 5, 2.0, False),
                                 ("Nominal 10.15 µm", [(10.15, 0), (10.15, 1.1)], NAVY, 0, 1.5, True)],
         (5, 13), (0, 1.1), "Slab width (µm)", "Insertion loss (dB/cm)", legend=True, xmaj=1, ymaj=0.1)
stat(s, 9.2, 1.85, 3.6, 1.15, "1.8 µm", "ripple period in slab width\n(0.9 µm cavity per side)", NAVY)
stat(s, 9.2, 3.2, 3.6, 1.15, "0.05 → 0.6", "dB/cm within ±0.4 µm\nof the nominal slab width", RED)
stat(s, 9.2, 4.55, 3.6, 1.15, "±0.04 %", "Vπ·L variation over the sweep\n(2.421 V·cm)", NAVY)
text(s, 0.6, 6.35, 12.2, 0.8, [("Peaks 1.03 / 0.73 / 0.60 dB/cm, troughs 0.02–0.06 dB/cm: the nominal sits on the rising edge of a peak. "
     "Slab-edge offsets of a few hundred nm can explain the scattered loop IL measurements.", {"size": 13, "bold": True, "color": NAVY})])

# 3 wavelength sweep -----------------------------------------------------------
WR = [json.loads(l[7:]) for l in open(H + "wl_results.txt") if l.startswith("RESULT")]
def ser(wl):
    return sorted([(r["slab_w"], r["IL_dBcm"]) for r in WR if abs(r["wl"] - wl) < 1e-9])
GREEN2 = RGBColor(0x1B, 0x9E, 0x77)
s = new("Wavelength: the ripple pattern shifts across the C band", "No buffer, gap 4.45 µm; same slab-width sweep at 1525, 1575 and 1625 nm")
xy_chart(s, 0.6, 1.8, 8.2, 4.4, [("1575 nm", [(r["slab_w"], r["IL_dBcm"]) for r in R], RED, 4, 1.75, False),
                                 ("1525 nm", ser(1.525), BLUE, 4, 1.75, False),
                                 ("1625 nm", ser(1.625), GREEN2, 4, 1.75, False),
                                 ("Nominal 10.15 µm", [(10.15, 0), (10.15, 2.0)], NAVY, 0, 1.5, True)],
         (5, 13), (0, 2.0), "Slab width (µm)", "Insertion loss (dB/cm)", legend=True, xmaj=1, ymaj=0.2)
table(s, [["λ", "IL @ 10.15 µm", "Position"], ["1525 nm", "0.262 dB/cm", "on a peak"],
          ["1575 nm", "0.092 dB/cm", "rising edge"], ["1625 nm", "0.080 dB/cm", "in a trough"]],
      9.1, 1.9, 3.7, [0.9, 1.35, 1.45], size=11)
box(s, 9.1, 3.65, 3.7, 2.5, [("What changes with λ", {"size": 14, "bold": True, "color": NAVY, "space": 6}),
    ("Peaks move to wider slabs: ≈ +0.35 µm per +50 nm", {"size": 12, "space": 4}),
    ("Period 1.70 / 1.77 / 1.90 µm", {"size": 12, "space": 4}),
    ("Peaks grow with λ (≈ 0.5 → 1.3 dB/cm at 9 µm)", {"size": 12, "space": 4}),
    ("Vπ·L: 2.32 / 2.42 / 2.53 V·cm, flat vs slab", {"size": 12})])
text(s, 0.6, 6.35, 12.2, 0.8, [("At the nominal slab, IL falls 3× from 1525 to 1625 nm, opposite to the normal gold-loss trend: "
     "a clear signature to look for in the measured C-band data.", {"size": 13, "bold": True, "color": NAVY})])

# 4 slab-end etch angle -----------------------------------------------------------
SL = sorted([json.loads(l[7:]) for l in open(H + "../istanbul_slanted/results.txt") if l.startswith("RESULT") and '"alpha_slab": 60' in l], key=lambda r: r["slab_w"])
s = new("Real 60° slab etch: ripples survive, shifted by 0.1 µm", "No buffer, gap 4.45 µm, 1575 nm; slab width = top width for both")
xy_chart(s, 0.6, 1.8, 8.2, 4.4, [("Vertical slab end (90°)", [(r["slab_w"], r["IL_dBcm"]) for r in R], RED, 4, 1.75, False),
                                 ("60° slab end (process)", [(r["slab_w"], r["IL_dBcm"]) for r in SL], NAVY, 4, 1.75, False),
                                 ("Nominal 10.15 µm", [(10.15, 0), (10.15, 1.1)], GREY, 0, 1.5, True)],
         (5, 13), (0, 1.1), "Slab top width (µm)", "Insertion loss (dB/cm)", legend=True, xmaj=1, ymaj=0.1)
image(s, H + "deck/xs_slant_zoom.png", 9.15, 1.75, w=3.65)
table(s, [["", "90°", "60°"], ["Period", "1.80 µm", "1.80 µm"], ["Peaks, dB/cm", "0.49–1.03", "0.50–0.96"],
          ["Troughs, dB/cm", "0.017–0.059", "0.016–0.059"], ["IL @ 10.15, dB/cm", "0.092", "0.138"]],
      9.15, 4.1, 3.65, [1.35, 1.15, 1.15], size=10, highlight=(4,))
text(s, 0.6, 6.35, 12.2, 0.8, [("The 275 nm, 60° slope still reflects the slab mode: same period and depth, pattern shifted by −0.10 µm "
     "(acts like a vertical end 0.10 µm wider). Vπ·L unchanged (2.421 V·cm).", {"size": 13, "bold": True, "color": NAVY})])

# 5 buffered: cross-section + gap -----------------------------------------------
B = H + "../istanbul_buffer/"
BA = [json.loads(l[7:]) for l in open(B + "all.txt") if l.startswith("RESULT")]
BG = sorted([r for r in BA if abs(r["slab_w"] - 10.15) < 1e-9], key=lambda r: r["gap"])
BS = sorted([r for r in BA if abs(r["gap"] - 3.65) < 1e-9], key=lambda r: r["slab_w"])
s = new("Istanbul + 200 nm buffer: gap recovers Vπ·L", "Conformal buffer under all the gold; slab 10.15 µm, 1575 nm")
image(s, H + "deck/xs_buf_top.png", 0.6, 1.8, w=6.4)
xy_chart(s, 7.3, 1.75, 5.5, 3.3, [("Vπ·L", [(r["gap"], r["VpiL_Vcm"]) for r in BG], NAVY, 6, 2.0, False),
                                  ("No buffer, 4.45 µm", [(3.5, 2.4215), (4.5, 2.4215)], RED, 0, 1.5, True)],
         (3.5, 4.5), (2.3, 3.0), "Gap on the buffer (µm)", "Vπ·L (V·cm)", legend=True, xmaj=0.2, ymaj=0.1)
stat(s, 0.6, 5.15, 2.85, 1.15, "+20 %", "Vπ·L with buffer at 4.45 µm\n(2.42 → 2.90 V·cm)", RED)
stat(s, 3.7, 5.15, 2.85, 1.15, "3.65 µm", "gap that restores 2.42 V·cm", NAVY)
stat(s, 6.8, 5.15, 2.85, 1.15, "0.013", "dB/cm at 3.65 µm", GREEN2)
stat(s, 9.9, 5.15, 2.85, 1.15, "7×", "lower IL than unbuffered", GREEN2)
text(s, 0.6, 6.5, 12.2, 0.6, [("Slope ≈ 0.6 V·cm per µm of gap; IL rises from 0.001 to 0.013 dB/cm as the gap closes.", {"size": 12, "color": MUT})])

# 5 buffered slab sweep -----------------------------------------------------------
s = new("With the buffer the ripples disappear", "Slab-width sweep at 1575 nm, both designs at the same nominal Vπ·L")
xy_chart(s, 0.6, 1.8, 8.2, 4.4, [("No buffer, gap 4.45 µm", [(r["slab_w"], r["IL_dBcm"]) for r in R], RED, 4, 1.75, False),
                                 ("200 nm buffer, gap 3.65 µm", [(r["slab_w"], r["IL_dBcm"]) for r in BS], GREEN2, 4, 2.0, False)],
         (5, 13), (0, 1.1), "Slab width (µm)", "Insertion loss (dB/cm)", legend=True, xmaj=1, ymaj=0.1)
stat(s, 9.2, 1.85, 3.6, 1.15, "0.0126 dB/cm", "buffered IL, ±0.4 % over\n5.45–12.45 µm", GREEN2)
stat(s, 9.2, 3.2, 3.6, 1.15, "0.017 → 1.03", "unbuffered IL range (dB/cm)", RED)
stat(s, 9.2, 4.55, 3.6, 1.15, "2.424 V·cm", "buffered Vπ·L, flat above 7 µm", NAVY)
text(s, 0.6, 6.35, 12.2, 0.8, [("The buffer removes the gold contact at the slab end: no cavity, no ripples, "
     "IL independent of slab-width errors, at equal Vπ·L.", {"size": 13, "bold": True, "color": NAVY})])

# 7-8 buffered + over-etched ------------------------------------------------------
OEd = H + "../istanbul_buffer_oe/"
OR = [json.loads(l[7:]) for l in open(OEd + "sweep.txt") if l.startswith("RESULT")]
A = sorted({round(r["oe"] * 1e3): r for r in OR if abs(r["L"] - 0.2) < 1e-9}.items())
Bl = sorted({round(r["L"] * 1e3): r for r in OR if abs(r["oe"] - 0.7) < 1e-9}.items())
s = new("Buffered Istanbul with the 700 nm BOX over-etch", "Gap 3.65 µm, slab 10.15 µm, 60° slab ends, 200 nm buffer, 1575 nm")
image(s, H + "../istanbul_buffer_oe/preview_nominal.png", 0.6, 1.7, w=12.1)
image(s, H + "deck/xs_buf_oe_zooms.png", 0.6, 4.85, h=2.0)
box(s, 9.3, 5.0, 3.5, 1.65, [("Two sweeps", {"size": 14, "bold": True, "color": NAVY, "space": 4}),
    ("Over-etch 0 → 900 nm", {"size": 12, "space": 2}), ("Lateral (side-wall) buffer 0 → 400 nm", {"size": 12, "space": 2}),
    ("Top and floor buffer fixed at 200 nm", {"size": 11, "color": MUT})])
s = new("Over-etch and lateral buffer: no effect on IL", "Same buffered design; IL axis 0–0.03 dB/cm")
xy_chart(s, 0.6, 1.75, 6.0, 3.3, [("IL", [(k, r["IL_dBcm"]) for k, r in A], GREEN2, 6, 2.0, False)],
         (0, 900), (0, 0.03), "Over-etch (nm)   [lateral buffer 200 nm]", "IL (dB/cm)", legend=False, xmaj=100, ymaj=0.005)
xy_chart(s, 6.8, 1.75, 6.0, 3.3, [("IL", [(k, r["IL_dBcm"]) for k, r in Bl], GREEN2, 6, 2.0, False)],
         (0, 400), (0, 0.03), "Lateral buffer (nm)   [over-etch 700 nm]", "IL (dB/cm)", legend=False, xmaj=50, ymaj=0.005)
stat(s, 0.6, 5.25, 3.9, 1.15, "0.0126 dB/cm", "IL at every point (within 1.4 %)", GREEN2)
stat(s, 4.75, 5.25, 3.9, 1.15, "−0.24 %", "Vπ·L from 0 to 900 nm over-etch\n(2.424 → 2.418 V·cm)", NAVY)
stat(s, 8.9, 5.25, 3.9, 1.15, "0 nm OK", "even gold on the LN slope\ngives the same IL", NAVY)
text(s, 0.6, 6.55, 12.2, 0.6, [("The top buffer removes the guided slab wave under the gold: no power reaches the slab end, "
     "so what surrounds it (recess, side buffer, gold) no longer matters.", {"size": 13, "bold": True, "color": NAVY})])

sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = H + "Istanbul_results_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
