// Field components explained: theory vs simulation (Lisbon lifted, etched slab)
const pptxgen = require("pptxgenjs");
const path = require("path");
const sizeOf = (f) => { const b = require("fs").readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };
const F = (n) => path.join(__dirname, "..", "figs", n);

const P = { navy: "14213D", gold: "D4A017", ink: "1F2937", mut: "6B7280", card: "F3F4F6", ey: "C2410C", ex: "1F5AA6", ez: "0F766E", white: "FFFFFF" };
const HF = "Cambria", BF = "Calibri";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "Field components explained";

function img(s, file, x, y, wMax, hMax) {
  const { w, h } = sizeOf(file);
  let W = wMax, H = (wMax * h) / w;
  if (H > hMax) { H = hMax; W = (hMax * w) / h; }
  s.addImage({ path: file, x: x + (wMax - W) / 2, y: y + (hMax - H) / 2, w: W, h: H });
}
function title(s, t, sub) {
  s.addText(t, { x: 0.5, y: 0.3, w: 12.3, h: 0.65, fontFace: HF, fontSize: 28, bold: true, color: P.navy, margin: 0, isTextBox: true });
  if (sub) s.addText(sub, { x: 0.5, y: 0.95, w: 12.3, h: 0.4, fontFace: BF, fontSize: 15, italic: true, color: P.mut, margin: 0, isTextBox: true });
}
function src(s, t) {
  s.addText(t, { x: 0.5, y: 7.0, w: 12.3, h: 0.3, fontFace: BF, fontSize: 10, color: P.mut, margin: 0, isTextBox: true });
}
function bullets(s, items, x, y, w, h, fs = 15) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } })),
    { x, y, w, h, fontFace: BF, fontSize: fs, color: P.ink, valign: "top", margin: 0.05, isTextBox: true });
}
function callout(s, big, small, x, y, w, col) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.15, fill: { color: P.card }, line: { color: P.card }, rectRadius: 0.1 });
  s.addText(big, { x, y: y + 0.08, w, h: 0.6, fontFace: HF, fontSize: 24, bold: true, color: col, align: "center", margin: 0, isTextBox: true });
  s.addText(small, { x: x + 0.1, y: y + 0.66, w: w - 0.2, h: 0.45, fontFace: BF, fontSize: 11, color: P.ink, align: "center", margin: 0, isTextBox: true });
}
const light = () => { const s = pres.addSlide(); s.background = { color: P.white }; return s; };

// 1 ── Title
let s = pres.addSlide(); s.background = { color: P.navy };
s.addText("Why each field component looks the way it does", { x: 0.7, y: 2.0, w: 11.9, h: 1.0, fontFace: HF, fontSize: 38, bold: true, color: P.white, margin: 0, isTextBox: true });
s.addText("Analytical and physical justification of the Eₓ, Eᵧ, Eₓ maps, with the lateral gold cavity in focus".replace("Eₓ, Eᵧ, Eₓ", "Ex, Ey, Ez"),
  { x: 0.7, y: 3.05, w: 11.9, h: 0.6, fontFace: BF, fontSize: 20, color: "CADCFC", margin: 0, isTextBox: true });
s.addText("Lisbon lifted electrodes, etched LN slab  |  1575 nm  |  550 nm film, 275 nm etch  |  gap 4.2 µm  |  slab_w 8.2 µm  |  parameters unchanged",
  { x: 0.7, y: 4.2, w: 11.9, h: 0.4, fontFace: BF, fontSize: 14, color: P.gold, margin: 0, isTextBox: true });
s.addText("Sources: Okamoto (2006), Maier (2007), Peng & Oliner (1981, I & II), Webster et al. (2007), Liu et al. (2021)",
  { x: 0.7, y: 6.5, w: 11.9, h: 0.4, fontFace: BF, fontSize: 12, color: "9CA3AF", margin: 0, isTextBox: true });

// 2 ── The picture to explain
s = light(); title(s, "What we have to explain", "Same mode, three components, 100 dB range (common reference max|Ex|²)");
img(s, F("components_dB_full.png"), 0.4, 1.4, 7.6, 5.5);
const q = [["Rib", "Ex one lobe; Ez two lobes, null on axis, 90° out of phase; Ey four weak lobes"],
  ["Free slab (0.7–2.1 µm)", "every component falls as a straight line in dB"],
  ["Under the gold (2.1–4.1 µm)", "Ex collapses, Ey/Ez dominate, standing wave with ~0.9 µm nulls; Ex nulls shifted by ¼ period"],
  ["Device level", "IL ripples with slab end / gold position; a buffer kills the ripple"]];
q.forEach(([h, t], i) => {
  const y = 1.5 + i * 1.33;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.3, y, w: 4.6, h: 1.18, fill: { color: P.card }, line: { color: P.card }, rectRadius: 0.08 });
  s.addText([{ text: h, options: { bold: true, color: P.navy, breakLine: true } }, { text: t, options: { color: P.ink } }],
    { x: 8.45, y: y + 0.05, w: 4.35, h: 1.08, fontFace: BF, fontSize: 13, valign: "middle", margin: 0, isTextBox: true });
});
s.addNotes("Four observations to justify, in order of position in the cross-section: rib, free slab, gold-clad slab (the cavity), and the device-level consequence (IL). Every following slide puts a simulation result next to an analytical prediction from the literature.");

// 3 ── Literature map
s = light(); title(s, "Five sources, one job each", "Each observation is tied to a specific equation or figure");
const lit = [
  ["Okamoto, Fundamentals of Optical Waveguides, Ch. 1–2", "Boundary conditions (1.32–1.33); Marcatili E^x_pq fields (2.41): Ez ∝ ∂Hy/∂x, Ey ∝ ∂²Hy/∂x∂y", P.ex],
  ["Maier, Plasmonics, Ch. 2", "SPP at metal/dielectric (2.10–2.14); no TE surface wave (2.17); decay into metal (2.13)", P.gold],
  ["Peng & Oliner, IEEE MTT 29 (1981) Part I & II", "TE–TM conversion at a lateral step; a TE-like mode leaks a TM wave; exit angle cos θ = n_eff / n_TM (3); resonance condition (2)", P.ey],
  ["Webster et al., IEEE PTL 19 (2007)", "Phase-matching picture (Fig. 2); measured periodic loss vs width with sharp minima (Fig. 4)", P.ez],
  ["Liu et al., Chin. Opt. Lett. 19 (2021)", "SiO₂ buffer suppresses the LN/metal leaky mode; > 100× lower loss (Fig. 1c)", P.navy]];
lit.forEach(([a, b, c], i) => {
  const y = 1.55 + i * 1.07;
  s.addShape(pres.shapes.OVAL, { x: 0.6, y: y + 0.22, w: 0.5, h: 0.5, fill: { color: c }, line: { color: c } });
  s.addText(String(i + 1), { x: 0.6, y: y + 0.22, w: 0.5, h: 0.5, fontFace: HF, fontSize: 16, bold: true, color: P.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText([{ text: a, options: { bold: true, color: P.navy, breakLine: true } }, { text: b, options: { color: P.ink } }],
    { x: 1.35, y, w: 11.4, h: 0.95, fontFace: BF, fontSize: 14, valign: "middle", margin: 0, isTextBox: true });
});

// 4 ── Regions and indices
s = light(); title(s, "The cross-section is three 1D slab waveguides side by side", "Oliner's criterion: a lateral region leaks only if one of its slab waves is faster than the mode (n_wave > n_eff)");
img(s, F("F1_regions_indices.png"), 0.4, 1.5, 12.5, 4.1);
callout(s, "1.884", "n_eff of the guided TE-like mode", 0.8, 5.75, 3.6, P.ink);
callout(s, "2.078", "TM wave of the gold-clad slab: the only one above n_eff", 4.85, 5.75, 3.6, P.ey);
callout(s, "1.700", "TE wave of the free slab: below n_eff → evanescent", 8.9, 5.75, 3.6, P.ex);
src(s, "1D transfer-matrix solver, same Sellmeier/J&C materials as the notebook. Oliner Part II §III-D; Webster Fig. 1.");
s.addNotes("Gold raises the TM index of the slab above n_eff because the TM wave is a hybrid with the gold surface plasmon: the single-interface SPP Au/LN has n = 2.256 (Maier eq. 2.14), and the thin LN slab on SiO2 brings it down to 2.078 — still above 1.884. The TE wave under the gold is pushed DOWN (1.49) because gold forces tangential Ex to zero. So under the gold the mode can only feed a TM (Ey-dominant) wave. This is exactly Oliner's 'new class of leaky modes': the leaking wave has the opposite polarisation to the bound mode.");

// 5 ── Phase matching
s = light(); title(s, "Why the light goes sideways under the gold", "Along z the phase is locked to the mode; the leftover wavevector points laterally");
img(s, F("F2_phase_matching.png"), 0.4, 1.4, 6.2, 5.5);
bullets(s, [
  "kz is conserved: every wave has kz = β = k₀·1.884",
  "Under gold the TM wave has |k| = k₀·2.078 > β, so kx is real: kx = k₀√(2.078² − 1.884²) = 0.877 k₀",
  "It leaves the rib at θ = arccos(1.884/2.078) = 25° (Oliner eq. 3)",
  "In the free slab |k| < β for both polarisations → kx imaginary → pure decay",
  "Same picture as Webster Fig. 2 for SOI TM ridges, with gold playing the role of the thick slab",
  "Result: the lateral wave period is fixed by two indices only, π/kx = 0.897 µm"], 6.9, 1.6, 6.0, 5.2, 15);
src(s, "Webster et al. 2007, Fig. 2; Oliner et al. 1981 Part II, eq. (3) and Fig. 8.");

// 6 ── Rib Ez
s = light(); title(s, "Rib: Ez is the x-derivative of Ex, shifted by 90°", "Gauss's law ∇·D = 0 with e^(−jβz): Ez = −j (ε_x/ε_z) ∂Ex/∂x / β   (Okamoto eq. 2.41, E^x_pq mode)");
img(s, F("F3_rib_Ez_from_Ex.png"), 0.3, 1.45, 8.9, 5.5);
callout(s, "90.000°", "median |phase(Ez/Ex)| over all LN points: Ez is purely imaginary", 9.5, 1.6, 3.4, P.ez);
callout(s, "null at x = 0", "Ex even → ∂Ex/∂x odd → Ez antisymmetric, two lobes", 9.5, 2.95, 3.4, P.ez);
callout(s, "≈ −14 dB", "|Ez|²/|Ex|² peak ≈ (1/βw)²: wide guide → small Ez", 9.5, 4.3, 3.4, P.ez);
s.addText("Lobes sit where Ex is steepest (the rib sidewalls). The '−j' is why we plot Im(Ez): it is not a typo but the physics of a forward wave.",
  { x: 9.5, y: 5.6, w: 3.4, h: 1.3, fontFace: BF, fontSize: 12, color: P.ink, margin: 0, isTextBox: true });
src(s, "Theory computed from the FEM Ex alone (no fit). Ripple in the theory curve = numerical derivative of a piecewise N1 field.");

// 7 ── Rib Ey
s = light(); title(s, "Rib: Ey is the weak quadrupole that makes the mode 'hybrid'", "Marcatili: Ey ≈ ∂²Ex/∂x∂y / (k₀²n²) — odd in x, changes sign across the field centre (Okamoto eq. 2.41)");
img(s, F("F4_rib_Ey_quadrupole.png"), 0.3, 1.5, 12.7, 3.3);
bullets(s, [
  "Ex (right) is one even lobe; its mixed derivative gives four lobes of alternating sign: same sign pattern as the FEM Ey (left)",
  "Ey peaks at the slanted sidewalls and corners, where Ex bends fastest in both x and y; the 60° walls add a direct polarisation tilt",
  "Ey is ~25 dB below Ex: the mode is TE-like but never pure — Oliner: 'all these waveguides support hybrid modes with all six components'",
  "This small Ey is the seed of everything that follows: at the gold edge it is the TM part that can phase-match"], 0.6, 5.0, 12.2, 1.9, 14);
src(s, "Theory from FEM Ex (LN only). Speckle in the FEM Ey = N1 elements (normal component discontinuous between triangles), not physics.");

// 8 ── Free slab
s = light(); title(s, "Free slab: a single evanescent tail, no fitting", "Outside the rib the mode is a TE slab wave below cut-off: e^(−γx), γ = k₀√(n_eff² − n_TE,slab²) = 3.24 µm⁻¹");
img(s, F("F5_gap_decay.png"), 0.3, 1.45, 12.7, 3.9);
callout(s, "−28.1 / −28.2", "Ex slope dB/µm: FEM / theory", 0.8, 5.6, 3.6, P.ex);
callout(s, "−7.5 / −7.9 dB", "Ez below Ex: FEM / theory (γ/β)", 4.85, 5.6, 3.6, P.ez);
callout(s, "straight line", "in dB = bound field (Peng–Oliner EDC picture)", 8.9, 5.6, 3.6, P.ink);
s.addNotes("Ez follows Ex with the same exponent because Ez ∝ ∂Ex/∂x = −γ Ex, so the ratio is a constant γ/β (times ne²/no²). At x = 2.1 µm the straight line hits the gold: there the curves change character abruptly — that is the start of the cavity.");

// 9 ── Under the gold: vertical physics
s = light(); title(s, "Under the gold the field becomes a plasmon-photonic TM wave", "Gold kills tangential E (Ex, Ez → 0 at the surface) and keeps normal E (Ey) — Okamoto (1.32), Maier (2.10–2.12)");
img(s, F("F7_cavity_vertical_profile.png"), 0.3, 1.45, 12.7, 4.1);
bullets(s, [
  "1D TM mode of Au / LN 275 nm / SiO₂ reproduces the FEM vertical profile of both Ey and Ez with one common scale",
  "Normal D continuous: Ey jumps ×2.3 into SiO₂ and drops ×(|ε_Au|/ε_LN) ≈ 25 into gold; Ez/Ey = −9.8 dB FEM vs −10.0 dB theory",
  "Maier (2.17): metal supports no TE surface wave → the Ex-polarised mode cannot follow under the gold; it can only feed TM"], 0.6, 5.65, 12.2, 1.3, 14);
src(s, "Jump at the LN/SiO₂ face −5.9 vs −7.4 dB: lowest-order N1 elements only approximate the normal-component jump.");

// 10 ── Cavity cuts
s = light(); title(s, "The cavity: one standing wave explains all three components", "Gold wall at the slab end = mirror. Tangential Ey, Ez → node (sin); normal Ex → antinode (cos)");
img(s, F("F6_cavity_standing_wave.png"), 0.25, 1.45, 12.8, 3.6);
callout(s, "0.897 µm", "predicted half-period π/kx; FEM nulls 3.234 and 2.33 µm", 0.6, 5.3, 3.0, P.ey);
callout(s, "¼ period", "Ex nulls (2.79, 3.71) sit halfway between Ey/Ez nulls", 3.75, 5.3, 3.0, P.ex);
callout(s, "kx/β = 0.47", "sets Ex amplitude from Ez: no free parameter", 6.9, 5.3, 3.0, P.ex);
callout(s, "31 nm", "effective mirror behind the wall ≈ skin depth (22 nm)", 10.05, 5.3, 2.75, P.gold);
s.addNotes("Model: TM-to-y wave with potential f(y)·sin(kx(xw−x))·e^{−jβz}. Derivation: Ey ∝ β_lat² f sin, Ez ∝ −jβ f' sin, Ex ∝ −kx f' cos. So Ey and Ez share nodes; Ex has nodes where they peak — the quarter-period shift. The only adjusted quantity is the mirror plane xw, fixed by one FEM null: 4.131 µm, i.e. 31 nm inside the gold, consistent with the field penetrating ~ one skin depth. The left end (x≈2.1-2.3) deviates because there the evanescent bound tail and the corner fields add to the cavity wave — that is the coupling region (Oliner's TE→TM conversion at the step).");

// 11 ── Cavity maps
s = light(); title(s, "Same story in 2D: nodal lines are vertical and land where predicted", "White dashed lines = nodes from kx; Ex lines offset by a quarter period");
img(s, F("F10_cavity_maps_nodes.png"), 0.4, 1.4, 8.2, 5.5);
bullets(s, [
  "Nodes are straight vertical lines: the slab wave has one vertical profile and only the lateral factor sin/cos changes",
  "Ey and Ez fill the LN slab and leak downward into SiO₂ (TM tail), never upward into gold",
  "Ex survives only as the small in-plane projection (kx/β) of the TM wave → ~ −60 dB",
  "Tiled triangles in the BOX are N1 discretisation of a −70 dB field, not physics",
  "The left edge (x = 2.1 µm) is the launcher: the evanescent tail hits the gold step and converts TE → TM (Peng–Oliner mode matching)"], 8.9, 1.6, 4.1, 5.3, 13);

// 12 ── IL vs L
s = light(); title(s, "Device consequence: IL is a Fabry–Pérot of the lateral wave", "Oliner/Webster: loss vs width shows sharp periodic features set by the transverse wavenumber of the converted wave");
img(s, F("F8_IL_vs_cavity_length.png"), 0.3, 1.45, 12.7, 3.95);
callout(s, "0.897 vs 0.895 µm", "period: theory π/kx vs FEM fit (+0.2 %)", 0.6, 5.6, 3.9, P.ey);
callout(s, "0.182 vs 0.180 µm⁻¹", "round-trip decay 2|Im kx|: theory vs fit", 4.7, 5.6, 3.9, P.ey);
callout(s, "×70 swing", "between 0.04 and 2.9 dB/cm for 0.5 µm change of L", 8.8, 5.6, 4.0, P.ink);
s.addNotes("Webster's condition (1)/Oliner's (2): k_x W = 2mπ for cancellation inside a ridge. Here the bouncing wave lives OUTSIDE the rib, between the gold step and the gold wall, so the condition becomes 2 kx L + φ = 2mπ — an Airy/FP law. The same two-index kx predicts both the period and the decay. The present design (L = 2.0 µm) sits on the rising flank of a peak: a ±50 nm slab-etch error changes IL by ~±40 %. Honesty note: the literature analogue (Webster, Oliner) is for dielectric ridges; no published measurement of this exact metal-clad lateral cavity was found.");

// 13 ── Loss location
s = light(); title(s, "Where the power is lost: the first 20 nm of gold", "Loss = Ey,Ez of the lateral wave penetrating the metal by one skin depth (Maier eq. 2.13)");
img(s, F("F11_loss_skin.png"), 0.3, 1.5, 12.7, 4.0);
bullets(s, [
  "δ = 1/Re√(β_lat² − ε_Au k₀²) = 22.4 nm; FEM decay inside gold follows it",
  "90 % of absorption in the 70 nm shell under the slab, 10 % at the gold/LN corners (field singularities), bulk negligible",
  "So IL scales with how much lateral wave is stored in the cavity → the Fabry–Pérot law of the previous slide"], 0.6, 5.7, 12.2, 1.2, 14);

// 14 ── Buffer
s = light(); title(s, "Why a SiO₂ buffer removes the cavity", "Liu et al. 2021: the silica layer 'suppresses the leaky modes at the LN/metal interface' (>100× loss reduction)");
img(s, F("F9_buffer_cutoff.png"), 0.3, 1.45, 12.7, 3.95);
bullets(s, [
  "Lifting gold by t lowers the TM index; below n_eff the lateral wave becomes evanescent: cut-off t_c ≈ 40 nm (1D)",
  "All measured wafers (194–248 nm) are far beyond t_c → no lateral wave, no standing wave, IL smooth and exponential in t",
  "This is the same physics read backwards: no phase-matched TM wave ⇒ no cavity"], 0.6, 5.6, 12.2, 1.35, 14);

// 15 ── Physics vs numerics
s = light(); title(s, "What is physics and what is the mesh", "Answering the 'are these artefacts?' question up front");
img(s, F("components_dB_zoom_slab.png"), 0.4, 1.4, 6.4, 5.5);
const rows = [
  [{ text: "Feature", options: { bold: true, color: P.white, fill: { color: P.navy } } }, { text: "Verdict", options: { bold: true, color: P.white, fill: { color: P.navy } } }],
  ["Standing-wave nulls, period 0.9 µm", "Physics: predicted to 0.2 %"],
  ["Ex nulls shifted by ¼ period", "Physics: sin/cos of TM wave"],
  ["Ey/Ez ≫ Ex under the gold", "Physics: metal boundary condition"],
  ["Ex discontinuous at slab end", "Physics: normal E jumps (ε ratio)"],
  ["Straight-line decay in gap", "Physics: γ to 0.2 %"],
  ["Triangles in the BOX at −70 dB", "Numerics: N1 normal comp."],
  ["Speckle in rib Ey", "Numerics: same, field 25 dB down"]];
s.addTable(rows, { x: 7.1, y: 1.6, w: 5.8, colW: [3.0, 2.8], fontFace: BF, fontSize: 12, color: P.ink, border: { type: "solid", pt: 0.5, color: "D1D5DB" }, rowH: 0.5 });

// 16 ── Correspondence table
s = light(); title(s, "One-to-one map: simulation ↔ theory ↔ literature");
const T = [["Observation", "Mechanism", "Check (FEM / theory)", "Source"]].map(r => r.map(t => ({ text: t, options: { bold: true, color: P.white, fill: { color: P.navy } } })));
[["Ez two lobes, null on axis, Im", "Gauss law, Ez ∝ −j∂Ex/∂x", "phase 90.000°", "Okamoto 2.41"],
 ["Ey four lobes, weak", "hybrid mode, ∂²Ex/∂x∂y", "same sign pattern", "Okamoto 2.41; Oliner II"],
 ["Linear dB decay in gap", "TE slab below cut-off", "−28.1 / −28.2 dB/µm", "Peng–Oliner EDC"],
 ["Ez/Ex constant in gap", "Ez = (γ/β)Ex", "−7.5 / −7.9 dB", "Okamoto 2.41"],
 ["Wave appears under gold", "TM index 2.078 > 1.884", "θ = 25°", "Oliner II eq. 3; Webster Fig. 2"],
 ["Ex dies under gold", "tangential E → 0; no TE SPP", "Ez/Ey −9.8 / −10.0 dB", "Maier 2.10–2.17"],
 ["Nulls every 0.9 µm", "standing wave, π/kx", "0.895 / 0.897 µm", "Oliner II eq. 2; Webster eq. 1"],
 ["Ex nulls ¼-period shifted", "sin (tangential) vs cos (normal)", "3.71 vs 3.68 µm", "Okamoto 1.32"],
 ["IL periodic in slab end", "lateral Fabry–Pérot", "2α 0.180 / 0.182 µm⁻¹", "Webster Fig. 4"],
 ["Loss in 20 nm of gold", "skin depth", "δ = 22.4 nm", "Maier 2.13"],
 ["Buffer kills ripple", "TM wave cut-off", "t_c ≈ 40 nm", "Liu 2021 Fig. 1c"]].forEach(r => T.push(r));
s.addTable(T, { x: 0.5, y: 1.15, w: 12.3, colW: [3.0, 3.4, 2.9, 3.0], fontFace: BF, fontSize: 12, color: P.ink, border: { type: "solid", pt: 0.5, color: "D1D5DB" }, rowH: 0.47 });

// 17 ── Conclusions
s = pres.addSlide(); s.background = { color: P.navy };
s.addText("Take-aways", { x: 0.7, y: 0.5, w: 11.9, h: 0.8, fontFace: HF, fontSize: 34, bold: true, color: P.white, margin: 0, isTextBox: true });
const tk = [
  ["Every feature is predicted", "with textbook formulas and two indices (1.884, 2.078); no free fit except the mirror plane"],
  ["The cavity is a TM wave", "born at the gold step by TE→TM conversion, bouncing between gold step and gold-wrapped slab end"],
  ["It is physical and robust in kind", "it needs only n_TM > n_eff, true for any unbuffered gold on this LN slab; tilt/roughness are expected to change ρ, not its existence"],
  ["Fabrication sensitivity is real", "IL period 0.9 µm in L: control slab-end position to ≲ 50 nm, or add ≥ 40 nm SiO₂ buffer to remove the cavity"]];
tk.forEach(([h, t], i) => {
  const y = 1.6 + i * 1.3;
  s.addShape(pres.shapes.OVAL, { x: 0.8, y: y + 0.15, w: 0.55, h: 0.55, fill: { color: P.gold }, line: { color: P.gold } });
  s.addText(String(i + 1), { x: 0.8, y: y + 0.15, w: 0.55, h: 0.55, fontFace: HF, fontSize: 18, bold: true, color: P.navy, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText([{ text: h, options: { bold: true, color: P.gold, breakLine: true } }, { text: t, options: { color: P.white } }],
    { x: 1.65, y, w: 11.0, h: 1.0, fontFace: BF, fontSize: 17, valign: "middle", margin: 0, isTextBox: true });
});

pres.writeFile({ fileName: path.join(__dirname, "Field_components_theory.pptx") }).then(f => console.log("wrote", f));
