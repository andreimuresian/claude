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
         (5, 13), (0, 1.1), "Slab width (µm)", "Insertion loss (dB/cm)", legend=True, xmaj=1, ymaj=0.2)
stat(s, 9.2, 1.85, 3.6, 1.15, "1.8 µm", "ripple period in slab width\n(0.9 µm cavity per side)", NAVY)
stat(s, 9.2, 3.2, 3.6, 1.15, "0.05 → 0.6", "dB/cm within ±0.4 µm\nof the nominal slab width", RED)
stat(s, 9.2, 4.55, 3.6, 1.15, "±0.04 %", "Vπ·L variation over the sweep\n(2.421 V·cm)", NAVY)
text(s, 0.6, 6.35, 12.2, 0.8, [("Peaks 1.03 / 0.73 / 0.60 dB/cm, troughs 0.02–0.06 dB/cm: the nominal sits on the rising edge of a peak. "
     "Slab-edge offsets of a few hundred nm can explain the scattered loop IL measurements.", {"size": 13, "bold": True, "color": NAVY})])

sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = H + "Istanbul_results_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
