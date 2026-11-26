import sys, os, shutil, json
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
C = "/home/user/claude/results/ps_meas/"; F = json.load(open(C + "fit.json"))
first_new = len(prs.slides); B = {"size": 12, "space": 4}; H = lambda t: (t, {"size": 15, "bold": True, "color": NAVY, "space": 8})
# 1 boxplots
s = new("Phase-shifter resistance: measurements", "2-point DC probe, I = 10 mA · wafers 6LS0004 and 6LS0005 · 9 of 16 fields each · 71 values (0005 field 00 R4 missing)")
image(s, C + "boxplots.png", 0.5, 1.75, w=9.0)
box(s, 9.8, 1.75, 3.0, 3.5, [H("Boxplot"), ("Line: median", B), ("Box: Q1–Q3 (middle 50 %)", B), ("Whiskers: last point within 1.5 × IQR", B),
    H("Reading"), ("The two wafers agree: medians within 3 Ω", B), ("Same fields high on both wafers (06–10): across-wafer film variation, ≈ ±4 %", B)])
# 2 fit method
s = new("Fitting: physical model and least squares", "One straight line through all 71 points")
box(s, 0.6, 1.8, 6.0, 3.6, [H("Physical model"), ("R = R_s · (L / W): only the resistive section of length ΔL changes between R1…R4", B),
    ("Everything else (pads, gold leads, probe contacts) is the same for all four → constant R₀", B),
    ("⇒ R = R₀ + k · ΔL : a straight line, k = R_s / W_eff", B),
    H("Least squares"), ("Choose k, R₀ minimising Σ (R_i − k·ΔL_i − R₀)²", B),
    ("Fit on all 71 values, not on the 4 averages → standard errors", B),
    ("Extrapolation: ΔL = (R − R₀) / k", B)])
table(s, [["Quantity", "Value"], ["Slope k", f"{F['m']:.4f} ± {F['sm']:.4f} Ω/µm"], ["Intercept R₀", f"{F['b']:.1f} ± {F['sb']:.1f} Ω"],
          ["R² (71 points)", f"{F['R2']:.3f}"], ["Residuals of the 4 means", "+0.5, +0.1, −1.1, +0.6 Ω"], ["Slope if R₀ forced to 0", f"{F['m0']:.4f} Ω/µm"]],
      7.0, 1.8, 5.8, [2.6, 3.2], size=12)
text(s, 7.0, 4.1, 5.8, 2.2, [("Means lie on the line within 1.1 Ω: no curvature, linear model justified", B),
    ("R₀ consistent with 0: leads and contacts negligible", B),
    ("Scatter around the line (RMSE 8 Ω) is field-to-field, not noise", B)])
# 3 results
s = new("Extrapolated ΔL for target resistances", "Fit R = " + f"{F['m']:.4f}·ΔL {F['b']:+.2f} Ω · error bars: range of per-field fits")
image(s, C + "fit.png", 0.4, 1.7, w=7.4)
rows = [["R target", "ΔL (µm)", "Field range", "6LS0004", "6LS0005"]]
for r in F["rows"]: rows.append([f"{r['R']} Ω", f"{r['dL']:.1f}", f"{r['lo']:.0f} – {r['hi']:.0f}", f"{r['w4']:.1f}", f"{r['w5']:.1f}"])
table(s, rows, 8.0, 1.8, 4.9, [1.0, 0.95, 1.15, 0.9, 0.9], size=12, highlight=(2,))
box(s, 8.0, 3.4, 4.9, 2.0, [("190 Ω → ΔL ≈ 178 µm (not 185 µm: 185 µm gives ≈ 197 Ω on average)", B),
    ("Across-wafer spread ±5 µm (1σ) dominates; fit 95 % CI only ±3 µm", B),
    ("All targets lie below the shortest structure (197.1 µm): short extrapolation", B)])
sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = C + "PS_resistance_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
