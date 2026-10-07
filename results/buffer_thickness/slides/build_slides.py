"""Two slides (buffer-thickness robustness) in the style and master of the final deck.

Run: python3 build_slides.py  ->  ../buffer_thickness_slides.pptx
Uses the helpers of results/final_deck/src/head5.py (base deck /tmp/deck5/meeting.pptx), adds the two slides and
drops every other slide, so the output carries the same master/layout and pastes cleanly into the final deck.
"""
import sys, csv
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
import numpy as np
from head5 import *

HERE = "/home/user/claude/results/buffer_thickness/"
C_BLUE, C_ORANGE = RGBColor(0x2A, 0x78, 0xD6), RGBColor(0xEB, 0x68, 0x34)
GREYL, GREYW = RGBColor(0xB0, 0xB0, 0xB0), RGBColor(0xD5, 0xD5, 0xD5)
COL = {"L": C_ORANGE, "J": C_BLUE}
LBL = {"L": "Lisbon, C band 1575 nm", "J": "Jerez, O band 1360 nm"}

R = list(csv.DictReader(open(HERE + "buffer_thickness_sweep.csv")))
def series(d, w):
    rr = [r for r in R if r["design"] == d and float(r["wg_top"]) == w]
    b = np.array([int(r["buffer_nm"]) for r in rr if int(r["buffer_nm"]) > 0], float)
    v = np.array([float(r["VpiL_Vcm"]) for r in rr if int(r["buffer_nm"]) > 0])
    il = np.array([float(r["IL_dBcm"]) for r in rr if int(r["buffer_nm"]) > 0])
    ref = [float(r["VpiL_Vcm"]) for r in rr if int(r["buffer_nm"]) == 0][0]
    o = np.argsort(b)
    return b[o], v[o], il[o], ref

FV = {}; FI = {}
for d in "LJ":
    for w in (1.0, 1.4):
        b, v, il, ref = series(d, w)
        FV[d, w] = np.poly1d(np.polyfit(b, v, 2)); FI[d, w] = lambda x, p=np.polyfit(b, np.log(il), 2): float(np.exp(np.polyval(p, x)))

first_new = len(prs.slides)

# ------------------------------------------------------------------ slide 1: the sweep
s = new("Buffered design: robust to buffer-thickness error",
        "SiO₂ buffer 130 → 270 nm (10 nm step), gap 3.4 µm, CAP 2.0 × 1.4 µm; measured spread ±20 nm (±40 nm extreme)")

def win_lines(y0, y1):
    return [(f"_w{x}", [(x, y0), (x, y1)], GREYL, 0, 1.0 if x in (180, 220) else 0.75, x not in (180, 220))
            for x in (160, 180, 220, 240)] + [("_n200", [(200, y0), (200, y1)], NAVY, 0, 0.75, True)]

VR, IR, XR = (1.65, 2.45), (0.005, 0.1), (120, 280)
for j, w in enumerate((1.0, 1.4)):
    x0 = 0.35 + j * 6.35
    text(s, x0 + 0.1, 1.68, 6.1, 0.32, [(f"rib top WG_TOP = {w:.1f} µm", {"size": 13, "bold": True, "color": NAVY})])
    sv, si = [], []
    for d in "LJ":
        b, v, il, ref = series(d, w)
        sv.append((LBL[d], list(zip(b, v)), COL[d], 5, 1.75, False))
        si.append((LBL[d], list(zip(b, il)), COL[d], 5, 1.75, False))
    for d in "LJ":
        sv.append((f"_ref{d}", [(XR[0], series(d, w)[3]), (XR[1], series(d, w)[3])], COL[d], 0, 1.0, True))
    xy_chart(s, x0, 1.98, 6.25, 2.75, sv + win_lines(*VR), XR, VR, None, "Vπ·L (V·cm)",
             legend=False, xmaj=20, ymaj=0.2)
    xy_chart(s, x0, 4.72, 6.25, 2.45, si + win_lines(*IR), XR, IR, "SiO₂ buffer thickness (nm)", "IL (dB/cm)",
             log=True, legend=False, xmaj=20)
text(s, 0.45, 7.1, 12.4, 0.3, [[("━● ", {"color": C_ORANGE, "bold": True}), ("Lisbon, C band 1575 nm     ", {"color": INK}),
                                 ("━● ", {"color": C_BLUE, "bold": True}), ("Jerez, O band 1360 nm     ", {"color": INK}),
                                 ("dashed horizontal: unbuffered at gap 4.2 µm;  verticals: 200 nm nominal (navy), "
                                  "±20 nm (grey solid), ±40 nm (grey dashed)", {"italic": True})]],
     size=10.5, color=MUT)
notes(s, "Buffered lifted designs, gap 3.4 um, GAP_TOP 10 um, CAP_W 2.0 um, CAP_H 1.4 um from the buffer top "
         "(the cap moves with the buffer), 60 deg sidewalls. Lisbon: 550 nm film, 275 nm etch / 275 nm slab, 1575 nm. "
         "Jerez: 400 nm film, 170 nm etch / 230 nm slab, 1360 nm. Sellmeier LN (Zelmon) and SiO2 (Malitson), "
         "Johnson & Christy gold, converged mesh. Buffer 130-270 nm in 10 nm steps (60 runs) plus the unbuffered "
         "references at gap 4.2 um (dashed). Vpi*L is linear in the buffer thickness (deviation <= 6 mV*cm over the range): "
         "+1.3 mV*cm/nm (Lisbon) and +1.0 mV*cm/nm (Jerez), i.e. about +/-1.1 % at +/-20 nm and +/-2.3 % at +/-40 nm, "
         "the same for both rib widths. IL falls exponentially with the buffer (e-folding 150 nm Lisbon, 125 nm Jerez): "
         "about +/-15 % at +/-20 nm, but always below 0.036 dB/cm inside the +/-40 nm window. "
         "No ripple and no x_lift dependence appears anywhere in the range: the lateral wave under the gold stays cut off.")

# ------------------------------------------------------------------ slide 2: what the measured wafers give
WF = [("sil-A", 194.0, 18.3, 167, 231), ("sil-B", 213.5, 16.5, 189, 246), ("sil-C", 248.2, 15.6, 226, 279)]
s = new("Measured buffer spread → Vπ·L and IL spread",
        "Process data (32 chips per wafer) mapped onto the simulated sweep; rib top 1.0 µm")
rows = [["wafer", "buffer (nm)", "Lisbon Vπ·L (V·cm)", "Lisbon IL (dB/cm)", "Jerez Vπ·L (V·cm)", "Jerez IL (dB/cm)"]]
for nm, m, sd, lo, hi in WF:
    r = [nm, f"{m:.0f} ± {sd:.0f}  ({lo}–{hi})"]
    for d in "LJ":
        f, g = FV[d, 1.0], FI[d, 1.0]
        r += [f"{f(m):.3f} ± {(f(m + sd) - f(m - sd)) / 2:.3f}", f"{g(m):.3f}  ({g(hi):.3f}–{g(lo):.3f})"]
    rows.append(r)
refL, refJ = series("L", 1.0)[3], series("J", 1.0)[3]
rows.append(["no buffer, gap 4.2", "—", f"{refL:.3f}", "0.23 (on ripple)", f"{refJ:.3f}", "0.075 (on ripple)"])
table(s, rows, 0.55, 1.85, 12.2, [1.75, 2.05, 2.15, 2.15, 2.0, 2.1], size=12.5, row_h=0.4, highlight=(1,))
stat(s, 0.55, 4.05, 2.9, 1.6, "±1.1 %", "Vπ·L per ±20 nm\n(±2.3 % at ±40 nm)", colr=C_BLUE)
stat(s, 3.65, 4.05, 2.9, 1.6, "±0.025", "V·cm: Vπ·L chip-to-chip σ\n(sil-A, Lisbon)", colr=C_BLUE)
stat(s, 6.75, 4.05, 2.9, 1.6, "≤ 0.036", "dB/cm IL, any chip\n(buffer ≫ 38 nm cutoff)", colr=C_ORANGE)
stat(s, 9.85, 4.05, 2.9, 1.6, "235 nm", "Jerez: buffer up to which gap 3.4\nbeats the unbuffered gap 4.2", colr=C_BLUE)
box(s, 0.55, 5.9, 12.2, 1.05, [
    [("Robust: ", {"bold": True, "color": NAVY}), ("the process spread moves Vπ·L by about 1 % and keeps IL ≤ 0.036 dB/cm; the wave under the gold stays cut off on every chip.", {})],
    [("Margin: ", {"bold": True, "color": NAVY}), ("Jerez at gap 3.4 µm beats its unbuffered reference up to a 235 nm buffer; Lisbon matches it at 196 nm, "
      "so thicker wafers (sil-B/C) give Vπ·L 1–3 % above it: target the sil-A recipe, or narrow the gap by ≈ 0.1 µm (to be verified).", {})],
], size=13.5)
notes(s, "Measured 'thick slab post etch' (the 200 nm buffer after etch-back of the ~1.4 um deposition): sil-A 0.194 +/- 0.018, "
         "sil-B 0.2135 +/- 0.016, sil-C 0.248 +/- 0.016 um (min-max 167-231, 189-246, 226-279 nm). Each wafer's mean and sigma "
         "are mapped through a quadratic fit of the simulated Vpi*L(buffer) and log IL(buffer), rib top 1.0 um "
         "(1.4 um behaves the same: Lisbon 2.167 / 2.192 / 2.233, Jerez 1.800 / 1.819 / 1.851 V*cm). IL ranges are for the "
         "thinnest/thickest chip; sil-C's thickest chip (279 nm) is a 9 nm extrapolation. "
         "Vpi*L sensitivity: +1.34 (Lisbon) / +1.02 (Jerez) mV*cm per nm. Chip-to-chip sigma of Vpi*L on sil-A: 0.025 V*cm "
         "(Lisbon), 0.019 V*cm (Jerez). Against the unbuffered gap-4.2 design: Jerez crosses at 235 nm, Lisbon at 196 nm "
         "(WG 1.0) / 199 nm (WG 1.4). Narrowing the gap by 0.1 um should recover about 0.06 V*cm for Lisbon (slope ~0.6 V*cm/um from the earlier 150 nm runs at gap 3.2/3.4) - to be checked "
         "with a simulation if pursued. Caveat: the model keeps the cap height constant above the buffer; if the cap top is set "
         "by the deposition, Vpi*L shifts by about -0.4 %.")

# ------------------------------------------------------------------ keep only the two new slides
sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = HERE + "buffer_thickness_slides.pptx"
prs.save(out); print("saved", out, len(prs.slides))
