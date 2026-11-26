import sys, os, shutil, json
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
C = "/home/user/claude/results/madrid/chinese/"; RED = RGBColor(0xC0, 0x39, 0x2B)
first_new = len(prs.slides); B = {"size": 12, "space": 4}; H = lambda t: (t, {"size": 15, "bold": True, "color": NAVY, "space": 8})
# 1 design
s = new("MTX tall – Chinese version: design", "Etched slab (SLAB_W), gold directly on LN/BOX (no buffer, no ALD) · femwell 2D FEM, C+L band 1525–1625 nm")
image(s, C + "deck/xs_user.png", 0.4, 1.9, w=8.0)
table(s, [["Parameter", "Value"], ["LN film / etch", "550 / 275 nm, 60°"], ["WG_W (rib top)", "1.5 µm"], ["GAP", "4.0 µm"], ["SLAB_W (swept)", "4.0 – 6.0 µm"],
          ["CAP_W × CAP_H", "2.5 × 1.4 µm (SiO₂)"], ["MTX_signal / MTX_ground", "10 / 0.5 µm"], ["Gold over slab", "conformal; wraps slab end"]],
      8.6, 1.7, 4.3, [2.2, 2.1], size=11)
text(s, 8.6, 4.85, 4.3, 1.2, [("SLAB_W = 4.0: slab ends at the gold edge; larger SLAB_W puts slab under the gold → lateral standing wave between rib and the gold-wrapped slab end", {"size": 10.5, "color": MUT})])
# 2 mesh
R = [json.loads(l[7:]) for l in open(C + "mesh.txt") if l.startswith("RESULT")]
rows = [["SLAB_W", "Mesh", "Triangles", "IL (dB/cm)", "Vπ·L (V·cm)"]]
for r in sorted(R, key=lambda r: (r["slab_w"], -r["ms"])): rows.append([f"{r['slab_w']:.1f}", f"{r['ms']}", f"{r['tri']//1000} k", f"{r['IL_dBcm']:.4f}", f"{r['VpiL_Vcm']:.4f}"])
s = new("Mesh convergence (λ = 1625 nm)", "MESH_SCALE 1.4 / 1.1 / 0.85")
table(s, rows, 0.6, 1.8, 7.6, [1.2, 1.0, 1.5, 1.9, 2.0], size=11)
box(s, 8.5, 1.8, 4.3, 3.6, [H("Choice: MESH_SCALE 1.4"), ("Vπ·L converged (≤ 0.07 %)", B), ("IL 0.2–9 % high vs 0.85 (largest on the resonance flank)", B),
    ("Peak positions and trends reliable; absolute IL slightly pessimistic", B)])
# 3 sweep
s = new("Standing wave across the C+L band", "SLAB_W 4.0–9.0 µm (0.1 µm step to 6, 0.2 µm beyond) × λ 1525–1625 nm (25 nm step) · 180 FEM runs")
image(s, C + "chinese_sweep.png", 1.55, 1.55, w=10.2)
box(s, 0.6, 5.5, 4.0, 1.3, [("Resonances every ≈ 1.9 µm: 4.8–4.9, 6.6–7.0, 8.4–9.0 µm; they shift to larger SLAB_W with λ", {"size": 11})])
box(s, 4.75, 5.5, 4.0, 1.3, [("Widest low-IL window: 5.5–6.2 µm, worst-case IL ≤ 0.29 dB/cm over C+L. Next one (7.6–8.0 µm) is narrower and lossier", {"size": 11})])
box(s, 8.9, 5.5, 3.9, 1.3, [("Vπ·L flat for SLAB_W ≥ 4.6 µm: 1.94 (1525) → 2.12 V·cm (1625)", {"size": 11})])
# 4 conclusions
s = new("Conclusions", "MTX tall – Chinese version")
table(s, [["SLAB_W (1625 nm)", "Vπ·L (V·cm)", "IL (dB/cm)", "Note"], ["4.6 µm (drawn)", "2.11", "0.57", "on resonance flank"],
          ["5.9 µm", "2.12", "0.19", "recommended, ±0.3 µm"]],
      0.6, 1.8, 8.2, [2.6, 1.6, 1.6, 2.4], size=13, highlight=(2,))
box(s, 0.6, 3.0, 8.2, 1.05, [("No buffer → slab end under gold acts as a mirror → standing-wave resonance", B),
    ("Nominal SLAB_W 5.9 µm: tolerates ±0.3 µm with IL ≤ 0.25 dB/cm across C+L", B)])
box(s, 9.1, 1.8, 3.7, 1.3, [H("Notes"), ("Mesh 1.4: IL ≤ 9 % high", B), ("Peak heights under-sampled (0.2 µm step above 6 µm)", B)])
sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = C + "deck/MTX_tall_Chinese_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
