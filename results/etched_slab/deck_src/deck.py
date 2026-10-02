import sys, re, csv, json
sys.path.insert(0, "/tmp/deck4")
import numpy as np
from head4 import *

SP = "/tmp/claude-0/-home-user-claude/fd41e088-2b12-5532-ab62-ef0605547492/scratchpad/"
RES = "/home/user/claude/results/etched_slab/"
K = 20 * np.log10(np.e) * 2 * np.pi / 1.575e-6 / 100
C_BLUE, C_ORANGE, C_AQUA, C_YEL = (RGBColor(0x2A, 0x78, 0xD6), RGBColor(0xEB, 0x68, 0x34),
                                   RGBColor(0x1B, 0xAF, 0x7A), RGBColor(0xED, 0xA1, 0x00))
GREYL = RGBColor(0xB0, 0xB0, 0xB0)


def runs(*files):
    d = {}
    for f in files:
        try:
            for l in open(SP + f):
                m = re.match(r"(\S+)\s+tri=\s*(\d+).*neff=(\S+) Im=(\S+) IL=(\S+) VpiL=(\S+)", l)
                if m: d[m[1]] = (K * abs(float(m[4])), float(m[6]))
        except FileNotFoundError:
            pass
    return d


R = runs("r3_out.txt", "r3b_out.txt", "l11_out.txt", "r4_out.txt")
# ---- nominal slab_w sweep (x_lift = 7) + gap fill
base = {float(r["slab_w_um"]): (float(r["IL_dB_per_cm"]), float(r["VpiL_Vcm"]))
        for r in csv.DictReader(open(RES + "slab_w_sweep.csv"))}
for k, v in R.items():
    if k.startswith("S_"): base[float(k[2:])] = v
SW = sorted(base)
NOM = [(s, *base[s]) for s in SW if s <= 20.0001]
L11 = sorted((float(k[4:]), *v) for k, v in R.items() if k.startswith("L11_"))
L11_CHECK = [(x, i, base[x][0]) for x, i, v in L11 if x < 12.0 and x in base]
L11 = [r for r in L11 if r[0] >= 12.0]
SPC = {w: sorted((float(k.split("_")[1]), *v) for k, v in R.items() if k.startswith(f"SP{w}_")) for w in ("0.1", "0.3", "0.6", "1.0", "2.0")}
WS = sorted((float(k.split("_")[1]), *v) for k, v in R.items() if k.startswith("W675_"))
G = {k: v for k, v in R.items() if k.startswith("G")}
XL = [(float(r["x_lift_um"]), float(r["IL_dB_per_cm"])) for r in csv.DictReader(open(RES + "xlift_sweep_slab_past_interface.csv"))]
OLD = sorted((float(r["x_lift_um"]), float(r["IL_dB_per_cm"])) for r in csv.DictReader(open("/home/user/claude/results/lift_sweep.csv")))
IL_STD_7, VPI_STD = 0.2295, 2.2668
IL_BUF, VPI_BUF = 0.0492, 2.1504
std_rng = (min(i for x, i in XL), max(i for x, i in XL))
gold = [r for r in NOM if 4.2 < r[0] < 14.0]
gold_rng = (min(r[1] for r in gold), max(r[1] for r in gold))
print("points: nominal", len(NOM), "L11", len(L11), "spacer", {k: len(v) for k, v in SPC.items()}, "W", len(WS), "G", G)


def vline(x, y0, y1, colr=GREYL):
    return (f"_v{x}", [(x, y0), (x, y1)], colr, 0, 1.0, True)


def label(slide, x, y, w, t, size=12, colr=INK, bold=False, align=PP_ALIGN.LEFT):
    text(slide, x, y, w, 0.35, [(t, {"size": size, "color": colr, "bold": bold})], align=align)


def hide_legend_entries(ch, idx):
    """Hide legend entries for helper series (vertical guide lines)."""
    leg = ch.legend._element
    for i in idx:
        le = etree.SubElement(leg, qn("c:legendEntry"))
        e = etree.SubElement(le, qn("c:idx")); e.set("val", str(i))
        d = etree.SubElement(le, qn("c:delete")); d.set("val", "1")
        leg.remove(le); leg.insert(1, le)


# =====================================================================
# 1. title
s = prs.slides.add_slide(L_TITLE)
text(s, 1.2, 2.3, 11.0, 2.6, [
    ("Etching the LN slab vs a SiO₂ buffer", {"size": 34, "bold": True}),
    ("Can we remove the lateral standing wave of the lifted electrodes?", {"size": 24}),
    ("λ = 1575 nm · 550 nm film, 275 nm etch · gap 4.2 µm · x_lift 7 µm · 2D FEM (femwell)", {"size": 17, "color": MUT}),
], align=PP_ALIGN.CENTER)
notes(s, "Follow-up of the lifted-electrode study: does a full etch of the LN slab remove the standing wave, "
         "how does it compare with the standard lifted and the buffered designs, and why the ripple behaves the way it does.")

# =====================================================================
# 2. geometries
s = new("Geometries compared", "Same rib, cap and lifted electrodes; only what sits under the gold changes")
image(s, FIG + "geoms6.png", 0.9, 1.75, h=4.75)
for x, t, c in [(0.6, "reference", MUT), (4.75, "candidate", MUT), (8.9, "etched slab: 3 regimes", MUT)]:
    pass
text(s, 0.9, 6.6, 12.0, 0.5, [[("LN ", {"bold": True, "color": RGBColor(0x6B, 0x75, 0x82)}), ("slab   ", {}),
                                   ("SiO₂ ", {"bold": True, "color": RGBColor(0x4C, 0x8F, 0xD0)}), ("buffer / lift / BOX   ", {}),
                                   ("Au ", {"bold": True, "color": RGBColor(0xC9, 0x93, 0x10)}), ("electrodes", {})]],
     size=13, color=MUT)
notes(s, "Etched slab: the slab is removed outside slab_w; gold fills the etched zone under the lower blocks, SiO2 under the pads, air in the gap. "
         "The spacer variant puts a SiO2 block between the slab end and the gold.")

# =====================================================================
# 3. IL and VpiL vs slab_w
s = new("Etched slab: IL and Vπ·L vs slab width", "λ = 1575 nm, gap 4.2 µm. slab_w = gap + 2d (d: slab edge beyond the gold inner edge)")
nom_il = [(a, b) for a, b, c in NOM]
sers = [("x_lift = 7 µm (nominal)", nom_il, C_BLUE, 4, 1.5, False)]
if L11:
    sers.append(("wider gold, x_lift = 11 µm", [(a, b) for a, b, c in L11], C_ORANGE, 4, 1.5, False))
sers += [("standard lifted (no etch)", [(2.0, IL_STD_7), (20.0, IL_STD_7)], GREY, 0, 1.25, True),
         vline(4.2, 1e-5, 10), vline(14.0, 1e-5, 10)]
ch = xy_chart(s, 0.45, 1.75, 8.6, 3.65, sers, (2, 20), (1e-5, 10), "", "IL (dB/cm)", log=True, xmaj=2, lsize=11)
hide_legend_entries(ch, [len(sers) - 2, len(sers) - 1])
ch.category_axis.tick_labels.font.size = Pt(10)
vp = [("x_lift = 7 µm", [(a, c) for a, b, c in NOM], C_BLUE, 3, 1.5, False)]
if L11:
    vp.append(("x_lift = 11 µm", [(a, c) for a, b, c in L11], C_ORANGE, 3, 1.5, False))
vp += [vline(4.2, 2.0, 6.0), vline(14.0, 2.0, 6.0)]
ch2 = xy_chart(s, 0.45, 5.35, 8.6, 1.95, vp, (2, 20), (2.0, 6.0), "slab_w (µm)", "Vπ·L (V·cm)", legend=False, xmaj=2, ymaj=1)
for x, t in [(2.15, "slab ends\nin the gap"), (5.5, "slab ends inside the gold"), (14.25, "slab past the\ngold/SiO₂ edge")]:
    pass
y0 = 2.2
stat(s, 9.35, 1.85, 3.55, 1.55, "≤ 0.003 dB/cm", "slab ends in the gap\nbut Vπ·L 3.1 – 5.4 V·cm", colr=C_AQUA)
stat(s, 9.35, 3.55, 3.55, 1.55, f"{gold_rng[0]:.2f} – {gold_rng[1]:.1f}", "dB/cm, slab ends in the gold\nripple period 1.79 µm in slab_w", colr=C_ORANGE)
stat(s, 9.35, 5.25, 3.55, 1.55, "= standard", "slab past the gold/SiO₂ edge\nIL 0.228 dB/cm at x_lift 7", colr=C_BLUE)
notes(s, "Three regimes. (1) slab_w < gap: no slab under the gold, no leak, IL ~0, but Vpi*L rises because the DC field crosses the air pocket. "
         "(2) slab ends in the gold: the gold-wrapped slab end is a mirror, ripples up to 7 dB/cm, first resonance at slab_w 4.95 um. "
         "(3) slab past the gold/SiO2 edge: identical to the standard lifted design; the cavity is clamped by x_lift. "
         "The orange curve uses a longer gold lower block (x_lift = 11 um) so the slab still ends in the gold up to slab_w 20: the ripple keeps decaying toward IL_inf. "
         + "Check: at slab_w 8.6 / 10.4 / 12.2 the x_lift = 11 model gives the same IL as the nominal one within 0.2 %.")
LBL3 = s

# =====================================================================
# 4. field cuts
s = new("Where the light goes", "|E|² along the slab mid-height; shaded = gold on the slab region, dotted = slab end")
image(s, FIG + "fieldcuts.png", 0.9, 1.75, h=5.5)
notes(s, "Slab in the gap: the field never reaches the gold. Slab in the gold: a standing wave between the gold inner edge and the slab end. "
         "Slab past the edge: the standing wave stops at x_lift; beyond it the slab is under SiO2 and the field decays evanescently, so the slab end is invisible.")

# =====================================================================
# 5. Q1 period vs cavity length
s = new("Why the ripple period does not depend on the cavity length",
        "We sweep the mirror position at fixed λ, not λ at fixed mirror position")
image(s, FIG + "q1_cavity.png", 0.45, 1.8, w=8.6)
box(s, 9.35, 1.85, 3.55, 5.2, [
    ("λ and β are fixed", {"bold": True, "size": 14}),
    ("→ the lateral wavelength λx = 1.79 µm is fixed by the source, not by the cavity", {"size": 13, "space": 12}),
    ("Resonance: 2kx·L + φ = 2πm", {"bold": True, "size": 14}),
    ("→ a new resonance every ΔL = λx/2 = 0.895 µm, whatever L is (like scanning a Fabry–Pérot mirror)", {"size": 13, "space": 12}),
    ("Off resonance", {"bold": True, "size": 14}),
    ("the rib keeps feeding the cavity; the echo returns out of phase → weaker field → dip, not zero", {"size": 13}),
])
notes(s, "A cavity scanned in frequency has resonances spaced by the free spectral range c/2nL, which depends on L. "
         "Here the frequency and the propagation constant beta of the rib mode are fixed, so the lateral wavenumber kx is fixed. "
         "Changing L by lambda_x/2 adds one half-wavelength and brings the same resonance back: the ripple period in L is lambda_x/2, independent of L. "
         "Off resonance the wave still exists because the cavity is continuously driven by the rib mode; the reflected wave returns with the wrong phase "
         "and partially cancels the incoming one, so the field under the gold is weaker and the absorption (IL) is lower.")

# =====================================================================
# 6. Q2 what sets the period
s = new("What sets the period: the wave under the gold", "The stack Au / LN slab / BOX and the rib mode, not the mirror")
image(s, FIG + "q2_phase_matching.png", 0.45, 1.8, w=8.7)
box(s, 9.45, 1.85, 3.45, 5.2, [
    ("Period", {"bold": True, "size": 14}),
    ("1D stack: n_sw = 2.08, rib: 1.884", {"size": 13}),
    ("→ λx/2 = 0.89 – 0.93 µm", {"size": 13}),
    ("2D fit: 0.895 µm for both mirrors", {"size": 13, "space": 12}),
    ("Both mirrors end the same guide", {"bold": True, "size": 14}),
    ("slab end: the slab stops", {"size": 13}),
    ("gold/SiO₂ edge: the gold cover stops", {"size": 13}),
    ("both at the top of the slab, where the field peaks", {"size": 13, "space": 12}),
    ("Buffer ≥ 38 nm: n_sw < n_rib", {"bold": True, "size": 14}),
    ("→ kx imaginary: no wave, no cavity", {"size": 13}),
])
notes(s, "The light under the gold is a gold-bound TM wave of the Au/LN/BOX stack with n_sw ~ 2.07-2.08. Its lateral wavenumber is kx = k0*sqrt(n_sw^2 - n_rib^2). "
         "The mirror material does not appear: it only terminates this guide. The guide exists only where gold covers LN, so it ends either where the slab ends "
         "or where the gold leaves the slab. The wave is strongest exactly at the gold/LN interface, at the top of the slab, so the gold edge is not 'away' from the field. "
         "With a SiO2 buffer above the cutoff the same stack gives n_sw below n_rib: kx becomes imaginary and no lateral wave can exist.")

# =====================================================================
# 7. Q4 same cavity two mirrors
s = new("Same cavity, two mirrors", "IL vs cavity length L = mirror position − gold inner edge")
FAC = sorted(((r[0] - 4.2) / 2, r[1]) for r in NOM if 4.2 < r[0] < 14.0)
sers = [("previous unetched x_lift sweep", [(x - 2.1, i) for x, i in OLD if x - 2.1 <= 9.0], GREYL, 0, 1.25, False),
        ("mirror: slab end in gold", FAC, C_ORANGE, 3, 1.25, False),
        ("mirror: gold/SiO₂ edge", [(x - 2.1, i) for x, i in XL if x - 2.1 <= 9.0], C_BLUE, 3, 1.25, False)]
xy_chart(s, 0.45, 1.75, 7.6, 5.4, sers, (0, 9), (0.02, 10), "cavity length L (µm)", "IL (dB/cm)", log=True, xmaj=1, lsize=11)
fj = json.load(open(RES + "ripple_comparison_facet_vs_interface.json"))
a, b = fj["slab_facet_in_gold"], fj["gold_SiO2_interface"]
table(s, [["fit", "slab end", "gold/SiO₂ edge"],
          ["period (µm)", f"{a['period_um']:.3f}", f"{b['period_um']:.3f}"],
          ["IL∞ (dB/cm)", f"{a['IL_inf']:.3f}", f"{b['IL_inf']:.3f}"],
          ["decay 2α (1/µm)", f"{a['two_alpha_per_um']:.3f}", f"{b['two_alpha_per_um']:.3f}"],
          ["mirror ρ₀", f"{a['rho0']:.3f}", f"{b['rho0']:.3f}"]],
      8.35, 2.0, 4.6, [1.9, 1.35, 1.35], size=13, row_h=0.4)
box(s, 8.35, 4.3, 4.6, 2.75, [
    ("Same period, IL∞ and decay", {"bold": True, "size": 14}),
    ("→ they belong to the cavity (the wave under the gold)", {"size": 13, "space": 10}),
    ("Different ρ₀ and phase", {"bold": True, "size": 14}),
    ("→ they belong to the mirror: curves shifted by 0.34 µm (next slide)", {"size": 13}),
])
notes(s, "Period, asymptote and decay coincide: they belong to the cavity medium. The mirrors differ in strength and in reflection phase. "
         "At the gold-wrapped slab end the field must vanish at the metal wall: a node sits at the wall. At the gold/SiO2 edge the guide ends into a slab "
         "where the wave is evanescent: the field has an antinode at the edge and leaks ~0.3 um into the SiO2-covered slab. "
         "This moves the effective mirror plane by ~0.30 um (field cuts) and shifts the curves by 0.34 um (fits).")

# =====================================================================
# 7b. offset
s = new("Why the two curves are offset", "The two mirrors reflect with a different phase")
image(s, FIG + "q4_mirrors.png", 1.2, 1.75, h=3.75)
text(s, 1.2, 5.7, 11.5, 1.4, [
    [("Hard mirror: ", {"bold": True}), ("the field must vanish at the gold wall → node at the mirror", {})],
    [("Soft mirror: ", {"bold": True}), ("the wave turns evanescent past the edge → antinode at the edge, tail into the SiO₂-covered slab", {})],
    [("→ effective mirror planes 0.30 µm apart (field) ≈ 0.34 µm shift of the IL curves (fit)", {"bold": True, "color": NAVY})],
], size=15)
notes(s, "Field cuts aligned on the mirror position. Left: slab_w 12 um, the slab end wrapped in gold; the last node coincides with the wall. "
         "Right: slab past the edge, x_lift 7; the field has a local maximum at the edge and decays evanescently beyond it; the last node is 0.30 um inside. "
         "A shift of the effective mirror plane shifts every resonance by the same length, which is the offset seen between the two IL curves.")

# =====================================================================
# 8. Q5 spacer
s = new("Countermeasure 1: SiO₂ spacer at the slab end", "Slab ending in the gold, SiO₂ spacer of width w between slab end and gold (fabrication: not viable)")
image(s, FIG + "geom_spacer.png", 0.55, 1.8, w=4.6)
SPACER_SLIDE = s

# =====================================================================
# 8b. thin LN under the gold
R2 = runs("r5_out.txt", "r6_out.txt", "r7_out.txt")
s = new("Countermeasure 2: no wave under the gold", "A slab thinner than ~180 nm under the gold cannot carry the wave (1D model, 1575 nm)")
image(s, FIG + "nsw_vs_thickness.png", 0.55, 1.8, h=5.0)
image(s, FIG + "geom_deep.png", 8.55, 2.15, w=4.3)
label(s, 8.55, 1.8, 4.3, "A. deeper rib etch (one etch, 150 nm slab)", size=13, bold=True)
image(s, FIG + "geom_partial.png", 8.55, 4.35, w=4.3)
label(s, 8.55, 4.0, 4.3, "B. partial 2nd etch outside slab_w (125 nm)", size=13, bold=True)
text(s, 8.55, 5.6, 4.4, 1.3, [("Same materials, lift kept, no buffer", {"size": 13, "color": MUT})])
notes(s, "The gold-bound wave under the electrodes needs enough LN: below ~180 nm its index drops under the rib-mode index and the lateral wave is cut off, "
         "exactly like the SiO2 buffer does. Two ways to get there without new materials: etch the rib deeper (one etch step, thin slab everywhere), "
         "or a second partial etch that thins the slab only outside slab_w, keeping the nominal 275 nm slab around the rib.")

# =====================================================================
# 8c. option A: deeper etch
s = new("Option A: deeper rib etch", "550 nm film, slab left after the rib etch: 275 nm (today) → 175 / 150 / 125 nm")
DEx = {wg: sorted((float(k.split("_x")[1]), *v) for k, v in R2.items() if k.startswith(f"DE{wg}_x")) for wg in ("0.375", "0.400")}
sers = [("slab 175 nm", [(a, b) for a, b, c in DEx["0.375"]], C_ORANGE, 4, 1.5, False),
        ("slab 150 nm", [(a, b) for a, b, c in DEx["0.400"]], C_BLUE, 4, 1.5, False),
        ("slab 275 nm (today)", [(x, i) for x, i in XL if x <= 8.0001], GREYL, 3, 1.25, False)]
sers.sort(key=lambda t: -len(t[1]))
xy_chart(s, 0.45, 1.75, 6.4, 5.4, sers, (6.5, 8.0), (0.001, 2), "x_lift (µm)", "IL (dB/cm)", log=True, xmaj=0.5, lsize=11)
rows = [["slab", "gap (µm)", "IL (dB/cm)", "Vπ·L (V·cm)"], ["275 nm (today)", "4.2", f"{std_rng[0]:.2f} – {std_rng[1]:.2f}", f"{VPI_STD:.2f}"]]
for wg, sl in (("0.350", "200 nm"), ("0.375", "175 nm"), ("0.400", "150 nm"), ("0.425", "125 nm")):
    k = f"DE{wg}_x7.00"
    if k in R2: rows.append([sl, "4.2", f"{R2[k][0]:.3g}", f"{R2[k][1]:.2f}"])
    for g in ("3.6", "3.2"):
        k = f"DE{wg}_g{g}"
        if k in R2: rows.append([sl, g, f"{R2[k][0]:.3g}", f"{R2[k][1]:.2f}"])
rows.append(["buffered 200 nm", "3.2", f"{IL_BUF:.3f}", f"{VPI_BUF:.2f}"])
table(s, rows, 7.15, 1.85, 5.75, [1.75, 1.0, 1.5, 1.5], size=12, row_h=0.36, highlight=(len(rows) - 1,))
text(s, 7.15, 1.85 + 0.36 * len(rows) + 0.2, 5.75, 1.2, [
    ("Ripple gone at ≤ 150 nm, but the thin slab weakens the EO overlap: Vπ·L +30 … +50 %", {"size": 13}),
    ("Narrowing the gap brings the gold onto the rib mode: IL rises", {"size": 13})])
notes(s, "Deeper rib etch: one process step, no new material. The ripple disappears (flat IL vs x_lift at 150 nm, nearly flat at 175 nm, close to the cutoff). "
         "But Vpi*L rises because less LN carries the DC field and the mode, and recovering it with a smaller gap puts the metal close to the mode.")

# =====================================================================
# 8d. option B: partial second etch
s = new("Option B: partial second etch outside slab_w", "Rib and 275 nm slab untouched; 125 nm LN left from slab_w outward; gap 4.2 µm")
image(s, FIG + "geom_partial.png", 0.55, 1.85, w=5.6)
PRs = sorted((float(k.split("_")[1]), *v) for k, v in R2.items() if k.startswith("PR125_"))
xy_chart(s, 0.45, 3.45, 6.0, 3.75, [("125 nm left", [(a, b) for a, b, c in PRs], C_BLUE, 5, 1.5, False),
                                    vline(4.2, 0.001, 10)],
         (2, 7), (0.001, 10), "slab_w (µm)   [step under the gold for slab_w > 4.2]", "IL (dB/cm)", log=True, xmaj=1, legend=False)
label(s, 1.55, 3.85, 3.0, "step in the gap", size=11.5, colr=MUT)
label(s, 4.4, 3.85, 2.2, "step under the gold", size=11.5, colr=C_ORANGE)
PRx = [v for k, v in R2.items() if k.startswith("PR125x_")] + ([R2["PR125_3.6"]] if "PR125_3.6" in R2 else [])
rows = [["case", "IL (dB/cm)", "Vπ·L (V·cm)"]]
for k, lab in (("PR125_3.2", "slab_w 3.2 (step 0.5 µm before gold)"), ("PR125_3.6", "slab_w 3.6 (step 0.3 µm before gold)"),
               ("PR125_4.0", "slab_w 4.0 (step 0.1 µm before gold)"), ("PR150_3.6", "150 nm left, slab_w 3.6")):
    if k in R2: rows.append([lab, f"{R2[k][0]:.3g}", f"{R2[k][1]:.2f}"])
for k, v in sorted(R2.items()):
    if k.startswith("PG"):
        g, sw, tr = k[2:].split("_")
        rows.append([f"gap {g}, slab_w {sw}, {int(float(tr)*1000)} nm left", f"{v[0]:.3g}", f"{v[1]:.2f}"])
rows.append(["buffered 200 nm, gap 3.2", f"{IL_BUF:.3f}", f"{VPI_BUF:.2f}"])
table(s, rows, 6.85, 1.85, 6.05, [3.55, 1.25, 1.25], size=11.5, row_h=0.34, highlight=(len(rows) - 1,))
if PRx:
    text(s, 6.85, 1.85 + 0.34 * len(rows) + 0.15, 6.05, 1.2, [
        (f"Flat vs x_lift 6.5 – 7.5 µm: IL {min(v[0] for v in PRx):.4f} – {max(v[0] for v in PRx):.4f} dB/cm", {"size": 13, "bold": True, "color": NAVY}),
        ("Step must stay in the gap: under the gold it forms a short cavity (2.4 dB/cm at slab_w 4.4)", {"size": 13})])
notes(s, "Partial second etch: the slab is thinned to 125 nm from slab_w outward, so the gold sits on LN that cannot carry the lateral wave. "
         "IL is flat in x_lift. The DC field still crosses LN instead of air, so the Vpi*L penalty of the full etch is much smaller. "
         "Requirement: the thickness step must lie in the gap with margin for the litho overlay; if it falls under the gold, a short cavity forms.")
PARTIAL_SLIDE = s

# =====================================================================
# 8e. trade-off chart
BUFSCAN = [(float(r["VpiL_Vcm"]), float(r["IL_dB_per_cm"])) for r in csv.DictReader(open("/home/user/claude/results/buffer/gap_scan_buffer200nm.csv"))]
part = [(v[1], v[0]) for k, v in R2.items() if k.startswith("PG") or k in ("PR125_3.2", "PR125_3.6", "PR125_4.0", "PR150_3.6", "PR150_3.2")]
deep = [(v[1], v[0]) for k, v in R2.items() if k.startswith("DE") and (k.endswith("_x7.00") or "_g" in k) and not k.startswith("DE0.350") and not k.startswith("DE0.375")]
full = [(v[1], v[0]) for k, v in list(G.items()) + [(f"S{x}", base[x]) for x in (3.2, 3.6, 4.0) if x in base]]
s = new("All solutions: insertion loss vs Vπ·L", "Each point is a ripple-free design (gap and thickness varied); lower-left is better")
sers = [("buffered 200 nm (gap 2.4 – 3.6 µm)", sorted(BUFSCAN), C_BLUE, 6, 2.0, False),
        ("partial 2nd etch (100 – 150 nm left)", sorted(part), C_ORANGE, 8, 0, False),
        ("deeper rib etch (125 – 150 nm slab)", sorted(deep), C_AQUA, 8, 0, False),
        ("full etch, slab ends in the gap", sorted(full), C_YEL, 8, 0, False),
        ("standard lifted: ripple range", [(VPI_STD, std_rng[0]), (VPI_STD, std_rng[1])], GREY, 6, 2.0, False)]
sers.sort(key=lambda t: -len(t[1]))
xy_chart(s, 0.45, 1.75, 8.4, 5.45, sers, (1.6, 3.6), (0.0005, 2), "Vπ·L (V·cm)", "IL (dB/cm)", log=True, xmaj=0.2, lsize=11)
def il_at(v, pts):
    pts = sorted(pts); return float(np.exp(np.interp(v, [p[0] for p in pts], [np.log(p[1]) for p in pts])))
cmp_rows = [["at Vπ·L", "buffered", "best alternative"]]
for v in (1.95, 2.05, 2.27):
    alts = [p for p in part + deep + full if abs(p[0] - v) < 0.06]
    if alts:
        b = min(alts, key=lambda p: p[1])
        cmp_rows.append([f"≈ {v:.2f} V·cm", f"{il_at(b[0], BUFSCAN):.3f} dB/cm", f"{b[1]:.3f} dB/cm"])
table(s, cmp_rows, 9.1, 1.9, 3.8, [1.3, 1.25, 1.25], size=12, row_h=0.38)
box(s, 9.1, 1.9 + 0.38 * len(cmp_rows) + 0.25, 3.8, 2.4, [
    ("The buffer wins", {"bold": True, "size": 15, "color": NAVY, "space": 8}),
    ("At the same Vπ·L it has 2 – 3× lower IL than any thin-LN or etched variant", {"size": 13, "space": 8}),
    ("It needs no alignment-critical step", {"size": 13})])
notes(s, "Trade-off between loss and drive voltage. The buffered curve is its gap scan (2.4 to 3.6 um, 200 nm SiO2; computed with the previous SiO2 constant, ~2 % lower IL). "
         "Every alternative point lies above the buffered curve: for the same Vpi*L the alternatives absorb more, because thin LN under the gold still brings "
         "the metal closer to the mode, or the rib mode is less confined. The standard lifted design is a vertical bar: its IL depends on x_lift.")

# =====================================================================
# 9. comparison
s = new("Countermeasures compared", "λ = 1575 nm; IL range over the swept dimension (x_lift or slab_w)")
CMP_SLIDE = s

# =====================================================================
# 10. conclusion
s = new("Recommendation: keep the 200 nm SiO₂ buffer", "Best IL – Vπ·L trade-off, flat IL, no alignment-critical step")
CONC = s

if __name__ == "__main__":
    exec(open("/tmp/deck4/deck_tail.py").read())
