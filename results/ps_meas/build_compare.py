import sys, os, shutil, json
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
C = "/home/user/claude/results/ps_meas/"; J = json.load(open(C + "compare.json"))
first_new = len(prs.slides); B = {"size": 11.5, "space": 4}
s = new("Manual vs automatic prober", "Wafers 6LS0004 and 6LS0005 (Lisbona tape-out) · our R2 = colleague PS-3, our R4 = colleague PS-1")
image(s, C + "compare_both.png", 0.4, 1.7, w=8.6)
rows = [["Median (Ω)", "Manual", "Auto", "Δ"]]
for k in ["R2_6LS0004", "R2_6LS0005", "R4_6LS0004", "R4_6LS0005"]:
    r, w = k.split("_"); rows.append([f"{r} · {w[-4:]}", f"{J[k]['ours']:.1f}", f"{J[k]['col']:.1f}", f"{J[k]['d']:+.1f}"])
table(s, rows, 9.2, 1.8, 3.7, [1.3, 0.8, 0.8, 0.8], size=11)
box(s, 9.2, 3.65, 3.7, 2.0, [("Automatic reads 1–6 Ω higher (≤ 2.6 %)", B),
    ("Automatic spread wider (IQR 16–24 vs 12–17 Ω)", B),
    ("6LS0005 automatic: 2 outliers (180.9, 473.9 Ω), likely probe contact", B)])
sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = C + "PS_manual_vs_auto.pptx"; prs.save(out); print("saved", out, len(prs.slides))
