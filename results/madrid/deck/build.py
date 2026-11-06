"""Madrid deck in the AFR template.  Run: python3 build.py"""
import sys, os, shutil
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
M = "/home/user/claude/results/madrid/"
RED = RGBColor(0xC0, 0x39, 0x2B); PINK = RGBColor(0xE0, 0x21, 0x8A)
first_new = len(prs.slides)
B = {"size": 12, "space": 4}

# 1 goal ---------------------------------------------------------------------
s = new("MADRID: a very-low-Vπ modulator for C + L band", "All simulations at λ = 1625 nm · femwell 2D FEM (optical mode + anisotropic DC)")
stat(s, 0.7, 1.9, 3.8, 1.3, "min Vπ·L", "target", NAVY)
stat(s, 4.75, 1.9, 3.8, 1.3, "IL < 0.5 dB/cm", "comfortably, at 1625 nm", RED)
stat(s, 8.8, 1.9, 3.8, 1.3, "gap ≥ 3.0 µm", "preferably ≥ 3.5 µm", NAVY)
box(s, 0.7, 3.55, 5.9, 2.6, [("Fixed by the request", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    ("LN film 550 nm, rib etch 275 nm (slab 275 nm), 60° walls", B),
    ("Rib top 1.4 µm", B), ("Flat (non-lifted) Cordoba-type electrodes, 30 µm wide", B),
    ("SiO₂ cap wide and short: (gap − 0.2) × 0.5 µm", B), ("SiO₂ buffer under the gold and across the gap", B)])
box(s, 6.9, 3.55, 5.7, 2.6, [("Swept", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    ("Gap 3.0 → 4.0 µm, 0.1 µm step", B), ("Buffer 0 → 200 nm (case a: above cut-off ± 40 nm; case b: pure trade-off)", B),
    ("ALD Al₂O₃ 0 / 20 / 40 / 60 nm, and a full no-ALD sweep", B), ("Gold thickness MTX 0.3 → 3 µm", B),
    ("≈ 185 FEM runs, mesh checked (IL ±1.2 %, Vπ·L ±0.02 %)", B)])
notes(s, "Madrid notebook: VPI_Madrid.ipynb (USE_ALD switch). Mesh: MESH_SCALE 1.4 vs 1.0 at gap 3.5/buffer 100/ALD 40: IL 0.2476 vs 0.2447, VpiL 1.8587 vs 1.8590.")

# 2 lessons ----------------------------------------------------------------------
s = new("Starting point: what our tapeouts taught us", "Simulated values at each design's own wavelength")
table(s, [["Tapeout / variant", "λ (nm)", "Film / slab", "Gap (µm)", "Vπ·L (V·cm)", "IL (dB/cm)"],
          ["Cordoba (flat electrodes)", "1575", "550 / 275", "4.2", "2.17", "0.43"],
          ["Cordoba + 40 nm ALD", "1575", "550 / 275", "4.2", "2.11", "0.93"],
          ["Istanbul + 200 nm buffer", "1575", "550 / 275", "3.65", "2.42", "0.013"],
          ["Lisbon lifted + 200 nm buffer, rib 1.4", "1575", "550 / 275", "3.4", "2.17", "0.027"],
          ["Lisbon buffered + 40 nm ALD", "1575", "550 / 275", "3.4", "2.06", "0.055"],
          ["Danube", "1310", "450 / 225", "4.15", "1.94", "0.03"],
          ["Jerez lifted + buffer, rib 1.4", "1360", "400 / 230", "3.4", "1.81", "0.015"]],
      0.6, 1.8, 8.0, [3.1, 0.8, 1.1, 0.9, 1.1, 1.0], size=11)
box(s, 8.95, 1.8, 3.8, 4.5, [("Levers", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    ("Gap sets Vπ·L; without buffer IL ∝ e^(−3.3·gap) plus Fabry–Perot ripples", B),
    ("SiO₂ buffer kills the ripple and lets the gap close", B),
    ("Buffered designs use only 5–10 % of a 0.5 dB/cm budget → room to trade", B),
    ("Wider rib / wider cap / ALD: −4 to −5 % Vπ·L each, for IL", B),
    ("Over-etch raises Vπ·L: avoid", B)])

# 3 buffer -------------------------------------------------------------------------
s = new("The buffer is mandatory: below ~60 nm the line is unusable", "ALD 40 nm, Au 2 µm · IL and Vπ·L vs gap for each buffer thickness")
image(s, M + "madrid_gap_buffer.png", 0.5, 1.75, w=8.6)
table(s, [["Buffer", "IL @ 3.5 µm", "IL @ 4.0 µm"], ["0 nm", "19.4", "4.4"], ["20 nm", "30.4", "6.9"], ["40 nm", "3.0", "0.68"],
          ["60 nm", "0.65", "0.15"], ["80 nm", "0.36", "0.08"], ["120 nm", "0.19", "0.04"], ["200 nm", "0.09", "0.02"]],
      9.4, 1.8, 3.4, [1.1, 1.15, 1.15], size=11, highlight=(6,))
text(s, 0.6, 5.5, 12.2, 1.4, [("Cut-off of the lateral wave under the gold at 1625 nm: t_c ≈ 33 nm (1D model). "
     "A 20 nm buffer is worse than none (resonant); 40 nm is too close to cut-off. "
     "Each +0.1 µm of gap: Vπ·L +0.052 V·cm, IL ÷1.35.", {"size": 13, "color": MUT})])

# 4 ALD and MTX --------------------------------------------------------------------
s = new("ALD and gold thickness", "Gap 3.5 µm, buffer 80 nm")
image(s, M + "madrid_ald_mtx.png", 0.5, 1.75, w=12.3)
box(s, 0.6, 5.55, 6.0, 1.4, [("ALD (εr ≈ 9.8) fills the gap and the 0.1 µm cap/gold slots", {"size": 12, "bold": True, "color": NAVY, "space": 4}),
    ("Pulls DC field into the LN: Γ 0.488 → 0.519; Vπ·L −6 % for 40 nm, but IL ×2.6", {"size": 12})])
box(s, 6.8, 5.55, 6.0, 1.4, [("Gold thickness saturates above ~1–1.5 µm", {"size": 12, "bold": True, "color": NAVY, "space": 4}),
    ("Vπ·L +1 % at 0.75 µm, +3.8 % at 0.3 µm (and IL rises). Keep MTX ≥ 1.5 µm", {"size": 12})])

# 5-6 ALD design ---------------------------------------------------------------------
s = new("Proposed design A: with ALD", "Gap 3.5 µm · buffer 120 ± 40 nm · cap 3.3 × 0.5 µm · ALD 40 nm · Au 2 µm · true 1:1 scale")
image(s, M + "madrid_cross_section.png", 1.6, 1.65, h=5.6)
s = new("Design A at 1625 nm: ±40 nm buffer tolerance", "Band = buffer 80–160 nm, line = nominal 120 nm")
image(s, M + "madrid_fom_tolerance.png", 1.4, 1.7, w=10.5)
stat(s, 0.9, 5.85, 3.7, 1.1, "1.89 V·cm", "Vπ·L  [1.83 … 1.95]  (−3.4 / +3.0 %)", NAVY)
stat(s, 4.85, 5.85, 3.7, 1.1, "0.19 dB/cm", "IL  [0.13 … 0.36]", RED)
stat(s, 8.8, 5.85, 3.7, 1.1, "3.5 µm", "gap, as preferred", NAVY)

# 7-8 no-ALD design --------------------------------------------------------------------
s = new("Proposed design B: no ALD", "Gap 3.2 µm · buffer 120 ± 40 nm · cap 3.0 × 0.5 µm · Au 2 µm · true 1:1 scale")
image(s, M + "madrid_cross_section_noALD.png", 1.6, 1.65, h=5.6)
s = new("Design B at 1625 nm: ±40 nm buffer tolerance", "Band = buffer 80–160 nm, line = nominal 120 nm")
image(s, M + "madrid_fom_tolerance_noALD.png", 1.4, 1.7, w=10.5)
stat(s, 0.9, 5.85, 3.7, 1.1, "1.85 V·cm", "Vπ·L  [1.78 … 1.91]  (−3.8 / +3.3 %)", NAVY)
stat(s, 4.85, 5.85, 3.7, 1.1, "0.21 dB/cm", "IL  [0.15 … 0.34]", RED)
stat(s, 8.8, 5.85, 3.7, 1.1, "3.2 µm", "gap (≥ 3.0 µm)", RED)

# 9 comparison -----------------------------------------------------------------------
s = new("ALD vs no ALD", "Same buffer (120 nm): no ALD gives a better Vπ·L–IL trade-off, but needs a narrower gap")
image(s, M + "madrid_ald_vs_noald.png", 0.5, 1.75, w=7.0)
table(s, [["Design", "Gap", "Vπ·L (V·cm)", "IL (dB/cm)"],
          ["A: ALD 40 nm", "3.5", "1.89 [1.83–1.95]", "0.19 [0.13–0.36]"],
          ["B: no ALD", "3.2", "1.85 [1.78–1.91]", "0.21 [0.15–0.34]"],
          ["B′: no ALD, gap held", "3.5", "1.98 [1.90–2.04]", "0.11 [0.07–0.22]"]],
      7.8, 1.9, 5.0, [1.6, 0.6, 1.4, 1.4], size=11, highlight=(2,))
box(s, 7.8, 3.6, 5.0, 2.7, [("Reading", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    ("At equal IL the no-ALD curve sits ~0.03–0.05 V·cm lower", B),
    ("ALD only wins when the gap is frozen at 3.5 µm", B),
    ("B′ uses buffer 100 ± 40 nm (60 nm worst case stays above cut-off)", B),
    ("Brackets: buffer ±40 nm", B)])

# 10 conclusions -------------------------------------------------------------------------
s = new("Conclusions and next steps")
box(s, 0.6, 1.7, 6.0, 3.0, [("Madrid at 1625 nm", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    ("Vπ·L 1.85–1.89 V·cm with IL ≈ 0.2 dB/cm (Cordoba ≈ 2.2 at 1575 nm)", B),
    ("SiO₂ buffer 120 ± 40 nm: robust to process (Vπ·L ±3–4 %, IL < 0.4)", B),
    ("No lift needed: flat electrodes with buffer are ripple-free", B),
    ("Without ALD: close the gap to 3.2 µm for the same result", B),
    ("Gold ≥ 1.5 µm", B)], fill=TINT)
box(s, 6.9, 1.7, 5.9, 3.0, [("Next", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    ("RF study (60 GHz): narrow gap + ALD lower Z0 and raise n_m", B),
    ("Check IL across 1525–1625 nm", B),
    ("Buffer thickness control on wafer (target ±20 nm)", B),
    ("Decide ALD (A) vs no ALD (B)", B)], fill=TINT)

sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = M + "Madrid_results_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
