"""Add the SiO2 cap-sweep slides to the Lisbon lifted deck, before the Conclusions.  usage: add_slides.py in.pptx out.pptx"""
import sys, os, shutil, csv
os.makedirs("/tmp/deck5", exist_ok=True); shutil.copy(sys.argv[1], "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
H = "/home/user/claude/results/lisbon_cap_sweep/"
R = list(csv.DictReader(open(H + "cap_sweep.csv")))
def v(wg, h, w, k): return [float(r[k]) for r in R if r["wg_top_um"] == wg and r["cap_h_um"] == h and r["cap_w_um"] == w][0]
def ser(wg, h, k): return sorted((float(r["cap_w_um"]), float(r[k])) for r in R if r["wg_top_um"] == wg and r["cap_h_um"] == h)
LBLUE = RGBColor(0x8F, 0xB8, 0xE8); LORANGE = RGBColor(0xF5, 0xB0, 0x8A)
B = lambda t, **k: (t, dict({"size": 13, "space": 6}, **k))
n0 = len(prs.slides)

s = new("SiO₂ cap sweep on the buffered design", "Lisbon lifted, 200 nm buffer, bottom gap 3.4 µm, 1575 nm, no slab etch; rib 1.0 and 1.4 µm")
box(s, 0.6, 1.8, 5.6, 4.6, [("Sweep", {"size": 16, "bold": True, "color": NAVY, "space": 8}),
    B("Cap height 0.5 → 1.4 µm (from the buffer top)"), B("Cap width 2.0 → 2.9 µm (0.25 µm from the electrodes at most)"),
    B("100 nm steps, two rib widths: 200 runs, no failures", space=12),
    ("Reference cap 2.0 × 1.4 µm", {"size": 16, "bold": True, "color": NAVY, "space": 8}),
    B(f"Rib 1.0 µm: Vπ·L {v('1.0','1.4','2.0','VpiL_Vcm'):.3f} V·cm, IL {v('1.0','1.4','2.0','IL_dB_per_cm'):.4f} dB/cm"),
    B(f"Rib 1.4 µm: Vπ·L {v('1.4','1.4','2.0','VpiL_Vcm'):.3f} V·cm, IL {v('1.4','1.4','2.0','IL_dB_per_cm'):.4f} dB/cm"),
    B("At gap 3.4 µm the 1.4 µm rib recovers the unbuffered Vπ·L (2.175 V·cm)", color=MUT)])
stat(s, 6.6, 1.9, 2.9, 1.3, "−5 %", "Vπ·L, cap width 2.0 → 2.9 µm", NAVY)
stat(s, 9.8, 1.9, 2.9, 1.3, "+22 %", "IL, cap width 2.0 → 2.9 µm", ORANGE)
stat(s, 6.6, 3.5, 2.9, 1.3, "−1 to −2.5 %", "Vπ·L, cap height 1.4 → 0.5 µm", NAVY)
stat(s, 9.8, 3.5, 2.9, 1.3, "< 0.4 %", "IL change with cap height", ORANGE)
text(s, 6.6, 5.1, 6.1, 1.3, [("Cap width sets both Vπ·L and IL; cap height only lowers Vπ·L, at no loss cost.", {"size": 14, "bold": True, "color": NAVY})])

s = new("Cap sweep: Vπ·L and IL maps", "Each cell is one simulation; rib 1.0 µm (top) and 1.4 µm (bottom)")
image(s, H + "cap_sweep_maps.png", 2.6, 1.6, h=5.75)

s = new("Cap width: trading loss for Vπ·L", "Cuts at the tallest (1.4 µm) and lowest (0.5 µm) cap")
xy_chart(s, 0.6, 1.75, 6.0, 4.0, [("rib 1.0, cap h 1.4", ser("1.0", "1.4", "VpiL_Vcm"), BLUE, 6, 2.0, False),
    ("rib 1.0, cap h 0.5", ser("1.0", "0.5", "VpiL_Vcm"), LBLUE, 6, 2.0, True),
    ("rib 1.4, cap h 1.4", ser("1.4", "1.4", "VpiL_Vcm"), ORANGE, 6, 2.0, False),
    ("rib 1.4, cap h 0.5", ser("1.4", "0.5", "VpiL_Vcm"), LORANGE, 6, 2.0, True)],
    (2.0, 2.9), (2.0, 2.3), "Cap width (µm)", "Vπ·L (V·cm)", legend=True, xmaj=0.1, ymaj=0.05, lsize=9)
xy_chart(s, 6.8, 1.75, 6.0, 4.0, [("rib 1.0, cap h 1.4", ser("1.0", "1.4", "IL_dB_per_cm"), BLUE, 6, 2.0, False),
    ("rib 1.4, cap h 1.4", ser("1.4", "1.4", "IL_dB_per_cm"), ORANGE, 6, 2.0, False)],
    (2.0, 2.9), (0.025, 0.035), "Cap width (µm)", "Insertion loss (dB/cm)", legend=True, xmaj=0.1, ymaj=0.002, lsize=9)
text(s, 0.6, 5.95, 12.2, 1.0, [("≈ 1 % of Vπ·L costs ≈ 4 % of IL; even the widest cap stays below 0.035 dB/cm, > 10× below unbuffered Cordoba. "
     "A lower cap gives up to 2.5 % extra Vπ·L for free.", {"size": 13, "bold": True, "color": NAVY})])

L = prs.slides._sldIdLst; ids = list(L); new_ids = ids[n0:]; concl = ids[n0 - 1]
for sid in new_ids: L.remove(sid)
pos = list(L).index(concl)
for k, sid in enumerate(new_ids): L.insert(pos + k, sid)
prs.save(sys.argv[2]); print("saved", sys.argv[2], len(prs.slides))
