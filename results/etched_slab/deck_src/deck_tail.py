# ---- spacer slide ------------------------------------------------------------
s = SPACER_SLIDE
w0 = [(a, b) for a, b, c in NOM if 5.95 <= a <= 8.05]
sers = [("no spacer", w0, C_BLUE, 3, 1.5, False)]
for w, col in (("0.1", C_AQUA), ("0.3", C_ORANGE), ("0.6", C_YEL)):
    if SPC[w]:
        sers.append((f"{int(float(w)*1000)} nm", [(a, b) for a, b, c in SPC[w]], col, 3, 1.5, False))
sers.sort(key=lambda t: -len(t[1]))
xy_chart(s, 5.3, 1.75, 7.6, 5.4, sers, (6, 8), (0.02, 10), "slab_w (µm)", "IL (dB/cm)", log=True, xmaj=0.5, lsize=11)
pk = [("none", max(w0, key=lambda t: t[1]))] + [(f"{int(float(w)*1000)} nm", max(((a, b) for a, b, c in SPC[w]), key=lambda t: t[1]))
                                              for w in ("0.1", "0.3", "0.6", "1.0", "2.0") if SPC[w]]
rows = [["spacer w", "peak IL", "at slab_w"]] + [[lab, f"{y:.2f}", f"{x:.2f}"] for lab, (x, y) in pk]
table(s, rows, 0.55, 3.3, 4.5, [1.5, 1.5, 1.5], size=12, row_h=0.33)
text(s, 0.55, 3.3 + 0.33 * len(rows) + 0.15, 4.5, 1.4, [
    ("The ripple survives at every width", {"bold": True, "size": 14, "color": NAVY}),
    ("Gold over SiO₂ cannot carry the wave (n < n_rib): the spacer is just another mirror, it only shifts the peaks", {"size": 12.5})])
notes(s, "Under the gold the wave can only be absorbed or reflected: beta of the rib mode exceeds k0*n of every cladding, so nothing can radiate away. "
         "A SiO2 spacer replaces the hard metal wall with a soft (evanescent) mirror: the peaks move by ~0.25 um in slab_w, their height does not drop (100, 300, 600 nm simulated). "
         "Wider spacers were not simulated: the spacer was judged not viable for fabrication, and from 300 to 600 nm the curve no longer changes.")

# ---- comparison slide ----------------------------------------------------------
s = CMP_SLIDE
def rng(p): return f"{min(p):.2g} – {max(p):.2g}"
sp_all = [b for w in ("0.1", "0.3", "0.6") for a, b, c in SPC[w]]
rows = [["Design", "IL (dB/cm)", "Ripple", "Vπ·L (V·cm)", "Extra process"],
        ["Standard lifted, gap 4.2 µm", f"{std_rng[0]:.2f} – {std_rng[1]:.2f}", "vs x_lift, period 0.9 µm", f"{VPI_STD:.2f}", "—"],
        ["Etched, slab ends in gold", f"{gold_rng[0]:.2f} – {gold_rng[1]:.1f}", "vs slab edge, period 0.9 µm", "2.26", "LN etch + alignment"],
        ["Etched, slab past the edge", f"{std_rng[0]:.2f} – {std_rng[1]:.2f}", "= standard (vs x_lift)", f"{VPI_STD:.2f}", "LN etch"],
        ["Etched + SiO₂ spacer (100–600 nm)", f"{min(sp_all):.2f} – {max(sp_all):.1f}" if sp_all else "–", "shifted, not removed", "2.27", "not viable (fab)"],
        ["Etched, slab ends in gap, gap 4.2 / 3.2", "≤ 0.003 / 0.083", "none", "3.1 – 5.4 / 2.47", "LN etch + alignment"]]
for k, lab in (("DE0.400_x7.00", "Deeper rib etch, 150 nm slab, gap 4.2"), ("DE0.425_g3.2", "Deeper rib etch, 125 nm slab, gap 3.2"),
               ("PR125_3.6", "Partial 2nd etch, 125 nm, gap 4.2"), ("PG3.6_3.0_0.1", "Partial 2nd etch, 100 nm, gap 3.6")):
    if k in R2:
        rows.append([lab, f"{R2[k][0]:.3g}", "none", f"{R2[k][1]:.2f}",
                     "none (deeper etch)" if k.startswith("DE") else "2nd LN etch + alignment"])
rows.append(["Buffered 200 nm SiO₂, gap 3.2 µm", f"{IL_BUF:.3f}", "none (flat ±0.2 %)", f"{VPI_BUF:.2f}", "blanket oxide, no litho"])
table(s, rows, 0.45, 1.75, 12.45, [3.85, 1.75, 2.6, 1.6, 2.65], size=12, row_h=0.4, highlight=(len(rows) - 1,))
notes(s, "IL ranges: standard and slab-past-edge over x_lift 6.5-11 um; slab in gold over slab_w 4.2-14 um; spacer over slab_w 6-8 um for 100 and 300 nm. "
         "All at 1575 nm with Sellmeier SiO2 and Johnson & Christy gold. Buffered values from the buffered study (x_lift = 7 um).")

# ---- conclusion ---------------------------------------------------------------
s = CONC
stat(s, 0.6, 1.9, 3.9, 1.75, f"{IL_BUF:.3f} dB/cm", "IL, flat vs x_lift\n(standard: 0.18 – 0.89)", colr=C_BLUE)
stat(s, 4.75, 1.9, 3.9, 1.75, f"{VPI_BUF:.2f} V·cm", "Vπ·L at gap 3.2 µm\n(standard: 2.27 at 4.2 µm)", colr=C_BLUE)
stat(s, 8.9, 1.9, 3.9, 1.75, "38 nm", "cutoff thickness\n200 nm = 5× margin", colr=C_BLUE)
box(s, 0.6, 4.0, 12.2, 2.9, [
    ("Why no geometric trick can replace it", {"bold": True, "size": 16, "space": 8}),
    ("Under the gold the wave cannot radiate (β > k₀n of every cladding): any termination reflects it → a cavity", {"size": 14, "space": 6}),
    ("Ripples vanish only if the wave is never launched: no slab under the gold (Vπ·L +35 % … +140 %) or a buffer above cutoff", {"size": 14, "space": 6}),
    ("Thin LN under the gold (deeper or partial etch) also kills the wave, but at equal Vπ·L its IL is 2 – 3× higher", {"size": 14, "space": 6}),
    ("Buffer: same materials, keeps the lift, one blanket SiO₂ deposition before the gold, no extra lithography", {"size": 14, "space": 6}),
])
notes(s, "Recommendation: keep the 200 nm buffered lifted design. Etching the slab either keeps the cavity (slab in the gold, or past the edge) "
         "or kills it at a large Vpi*L cost (slab in the gap).")

out = "/tmp/deck4/Etched_slab_vs_buffer.pptx"
prs.save(out)
print("saved", out, len(prs.slides))
