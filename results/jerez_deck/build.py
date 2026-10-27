"""Jerez lifted (O band) deck in the AFR template.  Run: python3 build.py"""
import sys, os, shutil, json, csv
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
H = "/home/user/claude/results/"; D = H + "jerez_deck/"
RED = RGBColor(0xC0, 0x39, 0x2B); LRED = RGBColor(0xF0, 0xA0, 0x8F); GREEN2 = RGBColor(0x1B, 0x9E, 0x77); LGREEN = RGBColor(0x8F, 0xD3, 0xBE)
B = lambda t, **k: (t, dict({"size": 13, "space": 6}, **k))
L = list(csv.DictReader(open(H + "oband/lift_sweep_oband.csv")))
def ser(design, wl, col="IL_dB_per_cm"):
    return sorted((float(r["x_lift_um"]), float(r[col])) for r in L if r["design"] == design and r["wavelength_nm"] == str(wl))
SUM = {r["wavelength_nm"]: r for r in csv.DictReader(open(H + "oband/summary_O_vs_C.csv"))}
GS = list(csv.DictReader(open(H + "jerez_gap/jerez_gap_sweep.csv")))
GJ = json.load(open(H + "jerez_gap/summary.json"))
n0 = len(prs.slides)

# 1 title
s = prs.slides.add_slide(L_TITLE)
text(s, 1.4, 2.4, 10.5, 2.4, [("Jerez lifted (O band)", {"size": 34, "bold": True}),
     ("Standing wave under the lifted electrodes and the SiO₂ buffer", {"size": 24, "bold": True}),
     ("400 nm LN film, 1310 and 1360 nm: x_lift sweeps, Fabry-Perot fits, buffer cutoff and gap relaxation", {"size": 18, "color": MUT})],
     align=PP_ALIGN.CENTER)

# 2 design
s = new("Jerez lifted: the two designs", "Lisbon-lifted electrodes on a 400 nm LN film (170 nm etch, 230 nm slab), rib top 1.0 µm")
image(s, D + "xs_jerez_lifted.png", 0.6, 1.75, w=12.1)
box(s, 0.6, 5.3, 6.0, 1.6, [("The question", {"size": 14, "bold": True, "color": NAVY, "space": 4}),
    B("Does the standing wave seen in Lisbon lifted (C band) also appear in the O band, and does the 200 nm buffer remove it?", size=12)])
box(s, 6.8, 5.3, 6.0, 1.6, [("x_lift", {"size": 14, "bold": True, "color": NAVY, "space": 4}),
    B("Where the gold leaves the slab and climbs onto the SiO₂ lift: the far mirror of the cavity. Swept 6.5 → 11 µm (0.1 µm step).", size=12)])

# 3 x_lift sweep
s = new("x_lift sweep: ripple without buffer, flat with buffer", "Bottom gap 4.2 µm (no buffer) / 3.2 µm (200 nm buffer); 184 runs, no failures")
xy_chart(s, 0.6, 1.75, 8.4, 4.6, [("No buffer, 1360 nm", ser("no_buffer", 1360), RED, 4, 1.75, False),
    ("No buffer, 1310 nm", ser("no_buffer", 1310), LRED, 4, 1.75, False),
    ("Buffer, 1360 nm", ser("buffer", 1360), GREEN2, 4, 2.0, False),
    ("Buffer, 1310 nm", ser("buffer", 1310), LGREEN, 4, 2.0, False)],
    (6.5, 11), (0, 0.3), "x_lift (µm)", "Insertion loss (dB/cm)", legend=True, xmaj=0.5, ymaj=0.05)
table(s, [["", "1310 nm", "1360 nm"],
          ["No buffer: IL range", f"{float(SUM['1310']['N_IL_min']):.3f}–{float(SUM['1310']['N_IL_max']):.3f}", f"{float(SUM['1360']['N_IL_min']):.3f}–{float(SUM['1360']['N_IL_max']):.3f}"],
          ["Ripple period", f"{float(SUM['1310']['N_period']):.3f} µm", f"{float(SUM['1360']['N_period']):.3f} µm"],
          ["Buffer: IL (flat)", f"{float(SUM['1310']['B_IL']):.4f}", f"{float(SUM['1360']['B_IL']):.4f}"],
          ["Buffer: spread", "< 0.01 %", "0.35 %"]], 9.3, 1.85, 3.5, [1.5, 1.0, 1.0], size=10, row_h=0.36)
text(s, 9.3, 4.0, 3.5, 2.2, [("IL in dB/cm", {"size": 10, "color": MUT, "space": 8}),
     ("The ripple is present in the O band too: up to ×3.7 between trough and peak. With the buffer IL is flat and 2–10× lower.", {"size": 13, "bold": True, "color": NAVY})])

# 4 Vpi*L and O vs C band
s = new("Vπ·L, and the O band against the C band", "Same lifted design; O band on 400 nm film, C band on 550 nm film")
rows = [["λ (nm)", "film (nm)", "no buffer IL range", "IL∞ (Fabry-Perot)", "period (µm)", "Vπ·L no buffer", "buffer IL", "Vπ·L buffer"]]
for wl in ("1310", "1360", "1525", "1550", "1575"):
    r = SUM[wl]
    rows.append([wl, r["film_nm"], f"{float(r['N_IL_min']):.3f}–{float(r['N_IL_max']):.3f}", f"{float(r['N_IL_inf']):.3f}",
                 f"{float(r['N_period']):.3f}", f"{float(r['N_VpiL']):.3f}", f"{float(r['B_IL']):.4f}", f"{float(r['B_VpiL']):.3f}"])
table(s, rows, 0.6, 1.85, 12.2, [1.0, 1.1, 1.9, 1.7, 1.3, 1.8, 1.6, 1.8], size=12, row_h=0.42, highlight=(1, 2))
box(s, 0.6, 4.6, 6.0, 2.0, [("Vπ·L", {"size": 14, "bold": True, "color": NAVY, "space": 4}),
    B("Independent of x_lift (< 0.1 %)", size=12, space=3), B("Buffer at gap 3.2 µm: −7 % vs no buffer at 4.2 µm (1.81 → 1.68 V·cm at 1310 nm)", size=12)])
box(s, 6.8, 4.6, 6.0, 2.0, [("O band vs C band", {"size": 14, "bold": True, "color": NAVY, "space": 4}),
    B("Shorter period (0.63–0.67 vs 0.85–0.90 µm) and lower loss level", size=12, space=3),
    B("IL in dB/cm; same physics: the buffer removes the ripple in both bands", size=12)])

# 5 why the buffer works
s = new("Why the buffer removes the ripple", "The slab wave under the gold, and the buffer thickness that cuts it off")
box(s, 0.6, 1.8, 6.0, 4.6, [("Cavity", {"size": 15, "bold": True, "color": NAVY, "space": 6}),
    B("The rib mode leaks into the slab wave guided under the gold (index above the rib mode)"),
    B("That wave is reflected where the gold climbs onto the lift (x_lift) → Fabry-Perot cavity", space=10),
    ("Fabry-Perot fit (no buffer)", {"size": 15, "bold": True, "color": NAVY, "space": 6}),
    B("1310 nm: mirror ρ₀ 0.93, round-trip decay 0.23 µm⁻¹, rms 0.0004 dB/cm"),
    B("1360 nm: mirror ρ₀ 0.94, round-trip decay 0.22 µm⁻¹, rms 0.0010 dB/cm")])
box(s, 6.8, 1.8, 6.0, 4.6, [("Cutoff of the slab wave", {"size": 15, "bold": True, "color": NAVY, "space": 6}),
    B("Buffer between gold and slab lowers the slab-wave index; above a critical thickness it can no longer be guided"),
    B("1D cutoff: 45.7 nm (1310) and 46.5 nm (1360); C band ≈ 38 nm", space=10),
    ("2D check of the 1D model", {"size": 15, "bold": True, "color": NAVY, "space": 6}),
    B("Ripple period at 0 and 25 nm: within 0.5–2.2 %"),
    B("200 nm is ≈ 4× the cutoff: the ripple is suppressed with a large margin")])

# 6 gap relaxation
s = new("Buffered Jerez lifted: how far can the gap be relaxed?", "1360 nm, 200 nm buffer, bottom gap 3.2 → 4.0 µm; target = unbuffered Vπ·L at gap 4.2 µm")
def gser(cap, wg, col):
    return sorted((float(r["gap_bot_um"]), float(r[col])) for r in GS if r["design"] == "buffer_200nm" and r["cap_h_um"] == cap and r["wg_top_um"] == wg)
xy_chart(s, 0.6, 1.75, 6.2, 3.6, [("cap 1.4, rib 1.0", gser("1.4", "1.0", "VpiL_Vcm"), NAVY, 5, 2.0, False),
    ("cap 1.4, rib 1.4", gser("1.4", "1.4", "VpiL_Vcm"), BLUE, 5, 2.0, False),
    ("target (cap 1.4, rib 1.0)", [(3.2, 1.9153), (4.0, 1.9153)], RED, 0, 1.5, True)],
    (3.2, 4.0), (1.6, 2.3), "Bottom gap (µm)", "Vπ·L (V·cm)", legend=True, xmaj=0.1, ymaj=0.1)
xy_chart(s, 6.9, 1.75, 5.9, 3.6, [("cap 1.4, rib 1.0", gser("1.4", "1.0", "IL_dB_per_cm"), NAVY, 5, 2.0, False),
    ("cap 1.4, rib 1.4", gser("1.4", "1.4", "IL_dB_per_cm"), BLUE, 5, 2.0, False)],
    (3.2, 4.0), (0, 0.035), "Bottom gap (µm)", "IL (dB/cm)", legend=True, xmaj=0.1, ymaj=0.005)
rows = [["Cap / rib (µm)", "unbuffered Vπ·L at 4.2", "matching buffered gap", "buffered IL there", "unbuffered IL (x_lift 6)"]]
for k, v in GJ.items():
    rows.append([k.replace("CAP_H ", "").replace(" / WG_TOP ", " / "), f"{v['ref_noBuffer_VpiL']:.3f} V·cm", f"{v['matching_gap_um']:.2f} µm",
                 f"{v['buffered_IL_at_matching_gap']:.4f} dB/cm", f"{v['ref_noBuffer_IL_at_xlift6']:.3f} dB/cm"])
table(s, rows, 0.6, 5.45, 12.2, [2.2, 2.6, 2.4, 2.5, 2.5], size=11, row_h=0.3, highlight=(1,))

# 7 cap and buffer
s = new("Cap height and buffer: how they interact", "Rib 1.0 µm, 1360 nm; Vπ·L (V·cm) at gaps 3.4 and 4.2 µm")
C = {(r["cap_h_um"], r["buffer_um"], r["gap_bot_um"]): float(r["VpiL_Vcm"]) for r in csv.DictReader(open(H + "jerez_gap/cap_buffer_decomposition.csv"))}
rows = [["", "gap 4.2, no buffer", "gap 3.4, no buffer", "gap 4.2, buffer", "gap 3.4, buffer"]]
for cap in ("1.4", "0.5"):
    rows.append([f"Cap {cap} µm"] + [f"{C[(cap, b, g)]:.3f}" for b, g in (("0.0", "4.2"), ("0.0", "3.4"), ("0.2", "4.2"), ("0.2", "3.4"))])
rows.append(["Cap 1.4 → 0.5"] + [f"{(C[('0.5', b, g)] / C[('1.4', b, g)] - 1) * 100:+.1f} %" for b, g in (("0.0", "4.2"), ("0.0", "3.4"), ("0.2", "4.2"), ("0.2", "3.4"))])
table(s, rows, 0.6, 1.9, 12.2, [2.6, 2.4, 2.4, 2.4, 2.4], size=13, row_h=0.45, highlight=(3,))
box(s, 0.6, 4.1, 6.0, 2.5, [("Cap acts electrostatically", {"size": 14, "bold": True, "color": NAVY, "space": 6}),
    B("n_eff changes by only 4·10⁻⁴; a lower SiO₂ cap leaves more air next to the rib, so more of the gap voltage drops across it (DC field in the rib +3–5 %)", size=12)])
box(s, 6.8, 4.1, 6.0, 2.5, [("Smaller with the buffer", {"size": 14, "bold": True, "color": NAVY, "space": 6}),
    B("The buffer fills the gap at rib level whatever the cap height, so the cap only changes the dielectric above it", size=12, space=4),
    B("Buffer penalty at fixed gap: +19–21 % (4.2 µm), +26 % (3.4 µm), the same for both caps", size=12)])

# 8 conclusions
s = new("Conclusions")
items = [("1", "The standing wave exists in Jerez lifted in the O band: IL varies up to ×3.7 with x_lift (period 0.63–0.67 µm)"),
         ("2", "The 200 nm SiO₂ buffer removes it: IL flat (0.018 / 0.028 dB/cm at 1310 / 1360 nm), ≈ 4× above the 46 nm cutoff"),
         ("3", "With the buffer the bottom gap can be relaxed to ≈ 3.4–3.5 µm at equal Vπ·L, with IL ≈ 0.012–0.016 dB/cm"),
         ("4", "Cap height acts only electrostatically: a lower cap lowers Vπ·L by 3–4 %, less with the buffer"),
         ("5", "Same physics as Lisbon lifted in the C band, with a shorter ripple period and lower loss")]
for i, (n, t) in enumerate(items):
    y = 1.8 + i * 0.95
    shp = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.8), Inches(y), Inches(0.5), Inches(0.5))
    shp.fill.solid(); shp.fill.fore_color.rgb = NAVY; shp.line.fill.background()
    text(s, 0.8, y, 0.5, 0.5, [(n, {"size": 15, "bold": True, "color": RGBColor(255, 255, 255)})], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.55, y - 0.05, 11.2, 0.65, [(t, {"size": 15})], anchor=MSO_ANCHOR.MIDDLE)

sl = prs.slides._sldIdLst
for sid in list(sl)[:n0]: prs.part.drop_rel(sid.rId); sl.remove(sid)
out = D + "Jerez_lifted_Oband_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
