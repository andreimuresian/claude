"""Add the Jerez V0 (1310 nm) ALD results to the user's ALD deck (AFR template).
usage: add_jerez.py in.pptx out.pptx"""
import sys, os, shutil, json
os.makedirs("/tmp/deck5", exist_ok=True); shutil.copy(sys.argv[1], "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
H = "/home/user/claude/results/"
J = sorted({round(json.loads(l[7:])["T_nm"]): json.loads(l[7:]) for l in open(H + "jerez_v0_alumina/sweep.txt") if l.startswith("RESULT")}.items())
C = [l.split(",") for l in open(H + "cordoba_alumina/alumina_sweep.csv").read().split("\n")[1:] if l]
cor = [(float(c[0]), float(c[5]), float(c[4])) for c in C]
jer = [(float(k), r["VpiL_Vcm"], r["IL_dBcm"]) for k, r in J]
GREEN2 = RGBColor(0x1B, 0x9E, 0x77); PINK = RGBColor(0xBE, 0x18, 0x5D)
n0 = len(prs.slides)
# A: Jerez V0 set-up --------------------------------------------------------------
s = new("Jerez V0 in the O band: same alumina, new design", "Non-lifted Cordoba-type electrodes, unetched slab, λ = 1310 nm")
image(s, H + "ald_deck/figs/xs_jerezv0_clean.png", 0.6, 1.8, w=8.4)
box(s, 9.3, 1.8, 3.5, 3.4, [("Jerez V0", {"size": 16, "bold": True, "color": GREEN2, "space": 8}),
    ("LN film 400 nm, rib etch 170 nm", {"size": 13, "space": 6}), ("Rib top 1.0 µm (single mode)", {"size": 13, "space": 6}),
    ("Gap 4.15 µm, gold 2 µm on the slab", {"size": 13, "space": 6}), ("No buffer, no slab etch, no over-etch", {"size": 13, "space": 6}),
    ("SiO₂ cap 2.0 × 1.4 µm", {"size": 13, "space": 12}),
    ("Alumina placed as for Cordoba", {"size": 13, "bold": True, "color": PINK, "space": 4}),
    ("n 1.74, RF permittivity 9.8, swept 0 → 100 nm", {"size": 12, "color": MUT})])
text(s, 0.6, 5.5, 12.2, 0.6, [("Mesh converged at 1310 nm: IL within 0.6 %, Vπ·L within 0.01 %", {"size": 13, "color": MUT})])
# B: sweep ------------------------------------------------------------------------
s = new("Jerez V0: lower Vπ·L, almost 3× the loss at 40 nm", "Gap 4.15 µm, 1310 nm")
xy_chart(s, 0.6, 1.85, 6.0, 3.9, [("Vπ·L", [(t, v) for t, v, _ in jer], GREEN2, 7, 2.25, False)], (0, 100), (1.65, 1.80),
         "Al₂O₃ thickness (nm)", "Vπ·L (V·cm)", legend=False, xmaj=20, ymaj=0.05)
xy_chart(s, 6.8, 1.85, 6.0, 3.9, [("IL", [(t, i) for t, _, i in jer], GREEN2, 7, 2.25, False)], (0, 100), (0, 0.8),
         "Al₂O₃ thickness (nm)", "Insertion loss (dB/cm)", legend=False, xmaj=20, ymaj=0.2)
stat(s, 1.6, 5.95, 4.2, 1.15, "−2.9 %", "Vπ·L at 40 nm: 1.788 → 1.736 V·cm", GREEN2)
stat(s, 7.6, 5.95, 4.2, 1.15, "×2.7", "loss at 40 nm: 0.10 → 0.27 dB/cm", PINK)
# C: Jerez vs Cordoba -------------------------------------------------------------------
s = new("Jerez V0 vs Cordoba", "Each curve is measured from its own design without alumina")
xy_chart(s, 0.6, 1.85, 6.0, 3.9, [("Jerez V0, 1310 nm", [(t, v - jer[0][1]) for t, v, _ in jer], GREEN2, 6, 2.25, False),
                                  ("Cordoba, 1575 nm", [(t, v - cor[0][1]) for t, v, _ in cor], ORANGE, 6, 2.25, False)],
         (0, 100), (-0.15, 0), "Al₂O₃ thickness (nm)", "Vπ·L change (V·cm)", legend=True, xmaj=20, ymaj=0.05)
xy_chart(s, 6.8, 1.85, 6.0, 3.9, [("Jerez V0, 1310 nm", [(t, i / jer[0][2]) for t, _, i in jer], GREEN2, 6, 2.25, False),
                                  ("Cordoba, 1575 nm", [(t, i / cor[0][2]) for t, _, i in cor], ORANGE, 6, 2.25, False)],
         (0, 100), (0, 8), "Al₂O₃ thickness (nm)", "Loss / loss without alumina", legend=True, xmaj=20, ymaj=1)
table(s, [["At 40 nm", "Jerez V0", "Cordoba"], ["Loss without alumina", "0.10 dB/cm", "0.43 dB/cm"],
          ["Loss with 40 nm", "0.27 dB/cm", "0.93 dB/cm"], ["Vπ·L change", "−2.9 %", "−3.0 %"]],
      2.6, 5.85, 8.1, [2.7, 2.7, 2.7], size=12, row_h=0.3)
# move the new slides before the conclusions (last original slide)
L = prs.slides._sldIdLst; ids = list(L); new_ids = ids[n0:]; concl = ids[n0 - 1]
for sid in new_ids: L.remove(sid)
pos = list(L).index(concl)
for k, sid in enumerate(new_ids): L.insert(pos + k, sid)
prs.save(sys.argv[2]); print("saved", sys.argv[2], len(prs.slides))
