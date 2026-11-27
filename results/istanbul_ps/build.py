import sys, os, shutil, json
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
C = "/home/user/claude/results/istanbul_ps/"; J = json.load(open(C + "fit.json")); fd = J["fitd"]
first_new = len(prs.slides); B = {"size": 12, "space": 4}; H = lambda t: (t, {"size": 15, "bold": True, "color": NAVY, "space": 8})
s = new("Istanbul phase shifters: measurements", "2-point DC · wafers 6IS0001, 6IS0002 · 13 fields each (0, 4 not measured) · 4 resistive-line widths")
image(s, C + "boxplots.png", 0.4, 1.7, w=9.2)
box(s, 9.8, 1.75, 3.0, 3.0, [H("Boxplot"), ("Line: median; box Q1–Q3; whiskers 1.5 × IQR", B),
    H("Reading"), ("Wafers agree: medians within 1–4 Ω", B), ("3 points excluded (red ×): > 5 % off their own field (e.g. 206 Ω)", B)])
s = new("Impact of field position", "Field offset = median of R / (wafer median per width), 4 widths · fields 0, 4 not measured")
image(s, C + "field_map.png", 0.4, 1.65, w=8.6)
box(s, 9.3, 1.75, 3.6, 3.9, [H("Median"), ("Field-to-field spread 3.1 % (1σ), range −7.0 … +3.8 %", B),
    ("Right column (1, 2, 3) low: −3 to −7 %", B), ("Centre field 7 and left column (11–13) high: +2 to +4 %", B),
    ("→ radial + lateral gradient, consistent on both wafers", B),
    H("Variability"), ("Wafer-to-wafer: 1.1 % rms per field (3× smaller)", B), ("Same pattern on both wafers → deposition (TiN thickness) map, not noise", B)])
s = new("Least-squares fit R(w)", f"{fd['n']} points (3 excluded) · resistive-line widths 11.8–13.3 µm")
image(s, C + "fit.png", 0.4, 1.7, w=7.8)
box(s, 8.5, 1.75, 4.4, 2.9, [H("Final equation"), (f"R(w) = {fd['A']:.0f} / (w − {fd['d']:.2f})  Ω, w in µm", {"size": 14, "bold": True, "space": 6}),
    (f"A = {fd['A']:.0f} ± {fd['sA']:.0f} Ω·µm, δ = {fd['d']:.2f} ± {fd['sd']:.2f} µm", B),
    ("Form R = R_sh·L / (w − δ): effective width loss δ", B),
    (f"Equivalent in range: R = {J['lin'][0]:.2f}·w + {J['lin'][1]:.1f} Ω", B),
    ("Field correction: multiply by (1 + field offset)", B),
    ("δ ≈ 5.5 µm: R falls 19 % for +13 % width; not plain 1/w. Valid 11.8–13.3 µm only", B)])
sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = C + "Istanbul_PS_resistance_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
