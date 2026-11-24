"""Madrid 1 (tri-galvanic) deck, built incrementally.  Run: python3 build.py"""
import sys, os, shutil
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
D = "/home/user/claude/results/madrid/m1/deck/"
RED = RGBColor(0xC0, 0x39, 0x2B)
first_new = len(prs.slides)
B = {"size": 12, "space": 4}
H = lambda t: (t, {"size": 15, "bold": True, "color": NAVY, "space": 8})

# 1 baseline -------------------------------------------------------------------
s = new("Madrid 1 (tri-galvanic): baseline", "Single arm as simulated · λ = 1625 nm · no ALD · femwell 2D FEM (optical mode + anisotropic DC)")
image(s, D + "F1_xs.png", 0.45, 1.55, w=8.3)
box(s, 8.95, 1.6, 3.9, 2.55, [H("Fixed"), ("LN 550 nm, etch 275 nm, 60°, rib top 1.4 µm", B),
    ("Continuous slab, BOX 4.7 µm", B), ("Signal 10 µm wide × 10 µm tall", B),
    ("Ground: 10 µm tongue (MTX_small) + 10 × 10 µm", B), ("SiO₂ buffer and cap, air above", B)])
stat(s, 8.95, 4.35, 1.85, 1.2, "1.827", "Vπ·L (V·cm)", NAVY)
stat(s, 11.0, 4.35, 1.85, 1.2, "0.261", "IL (dB/cm)", RED)
text(s, 8.95, 5.65, 3.9, 0.7, [("Baseline: gap 3.2, buffer 100 nm, cap 3.0 × 0.5, MTX_small 1.0 µm", {"size": 10, "color": MUT})])
notes(s, "Madrid B reference (flat 2 um gold both sides, buffer 120 nm): 1.854 V*cm / 0.209 dB/cm. Runner: results/madrid/m1/run_m1.py.")

# 2 parameters -------------------------------------------------------------------
s = new("Design space and goal", "Minimise Vπ·L with IL < 0.4 dB/cm at 1625 nm")
table(s, [["Parameter", "Min", "Max", "Expected trend for low Vπ·L"],
          ["GAP", "3.0 µm", "4.5 µm", "minimum (≈ +0.05 V·cm per 0.1 µm)"],
          ["BUFFER_H", "50 nm", "200 nm", "thin, limited by IL (50 nm = −50 nm error on 100)"],
          ["CAP_W", "2.8 µm", "= GAP", "fill the gap (no air pockets)"],
          ["CAP_H", "0.5 µm", "1.4 µm", "to be found: oxide in front of the tall signal wall"],
          ["MTX_small", "0.5 µm", "1.0 µm", "thick ground tongue"]],
      0.6, 1.8, 7.6, [1.5, 1.0, 1.0, 4.1], size=12)
box(s, 8.5, 1.8, 4.3, 4.4, [H("Plan"), ("32 corners + 80 Latin-hypercube points (112 FEM runs)", B),
    ("CAP_W sampled as a fraction of (GAP − 2.8 µm): no impossible geometries", B),
    ("Gaussian-process surrogate on log IL and Vπ·L, cross-validated", B),
    ("Optimum on the surrogate, then ≈ 8 FEM validation points", B),
    ("Robustness: buffer −40 nm at the optimum", B)])

# 3 standing wave -----------------------------------------------------------------
s = new("Standing wave under the 10 µm signal electrode", "Gap 3.2 µm, cap 3.0 × 0.5 µm, MTX_small 1.0 µm, λ = 1625 nm · signal width swept 9–11 µm in 0.1 µm steps")
image(s, D + "F2_standing_wave.png", 0.4, 1.6, w=8.4)
table(s, [["Buffer", "IL (dB/cm)", "Ripple", "Vπ·L"], ["none", "31–41", "±15 %", "1.514"],
          ["50 nm", "0.779", "0.07 %", "1.724"], ["100 nm", "0.261", "0.04 %", "1.827"]],
      9.0, 1.7, 3.8, [1.0, 1.1, 0.8, 0.9], size=11)
box(s, 9.0, 3.25, 3.8, 3.0, [H("Reading"), ("No buffer: the lateral wave under the gold reflects at the far signal edge (period ≈ 0.95 µm)", B),
    ("Cordoba hid it with 35–50 µm wide electrodes; a 10 µm signal does not", B),
    ("With ≥ 50 nm SiO₂ the wave is cut off: IL flat", B)])

# 4 wavelength / minimum buffer ------------------------------------------------------
s = new("Across C + L (1525–1625 nm) and minimum buffer", "1D slab model of the lateral wave under Au / SiO₂ / LN, 5 nm steps; 2D check at 1625 nm")
image(s, D + "F3_wavelength.png", 0.35, 1.55, w=12.6)
box(s, 0.6, 5.65, 6.0, 1.25, [("Without buffer the ripple period grows with λ (+12 % over the band): any 10 µm electrode crosses ≈ 1 peak in the band", {"size": 11.5, "space": 3}),
    ("Cut-off 32.8–33.1 nm, flat in λ; 1625 nm decays slowest (worst case)", {"size": 11.5})])
box(s, 6.85, 5.65, 5.95, 1.25, [("Minimum buffer: 90 nm nominal → 50 nm with −40 nm error", {"size": 12.5, "bold": True, "color": NAVY, "space": 3}),
    ("50 nm: round trip ≤ 10⁻¹⁴, 2D flat (0.07 %). Working minimum 100 nm (IL)", {"size": 11.5})])

sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = D + "Madrid1_results_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
