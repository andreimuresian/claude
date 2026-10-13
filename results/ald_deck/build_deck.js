// ALD Al2O3 protection layer: Cordoba vs buffered Lisbon lifted
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const sizeOf = (f) => { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };
const F = (n) => path.join(__dirname, "figs", n);

const P = { navy: "14213D", gold: "D4A017", blue: "1F5AA6", pink: "BE185D", ink: "1F2937", mut: "6B7280", card: "F3F4F6", white: "FFFFFF" };
const HF = "Cambria", BF = "Calibri";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "ALD alumina layer: Cordoba vs Lisbon lifted";

function img(s, file, x, y, wMax, hMax) {
  const { w, h } = sizeOf(file);
  let W = wMax, H = (wMax * h) / w;
  if (H > hMax) { H = hMax; W = (hMax * w) / h; }
  s.addImage({ path: file, x: x + (wMax - W) / 2, y: y + (hMax - H) / 2, w: W, h: H });
}
function title(s, t, sub) {
  s.addText(t, { x: 0.6, y: 0.35, w: 12.1, h: 0.7, fontFace: HF, fontSize: 30, bold: true, color: P.navy, margin: 0, isTextBox: true });
  if (sub) s.addText(sub, { x: 0.6, y: 1.05, w: 12.1, h: 0.45, fontFace: BF, fontSize: 16, color: P.mut, margin: 0, isTextBox: true });
}
function lines(s, items, x, y, w, h, fs = 17) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 12 } })),
    { x, y, w, h, fontFace: BF, fontSize: fs, color: P.ink, valign: "top", margin: 0.05, isTextBox: true });
}
function stat(s, big, small, x, y, w, col) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.25, fill: { color: P.card }, line: { color: P.card }, rectRadius: 0.1 });
  s.addText(big, { x, y: y + 0.12, w, h: 0.6, fontFace: HF, fontSize: 26, bold: true, color: col, align: "center", margin: 0, isTextBox: true });
  s.addText(small, { x: x + 0.15, y: y + 0.72, w: w - 0.3, h: 0.45, fontFace: BF, fontSize: 13, color: P.ink, align: "center", margin: 0, isTextBox: true });
}
const light = () => { const s = pres.addSlide(); s.background = { color: P.white }; return s; };

// 1 Title
let s = pres.addSlide(); s.background = { color: P.navy };
s.addText("ALD alumina protection layer", { x: 0.8, y: 2.1, w: 11.7, h: 1.0, fontFace: HF, fontSize: 42, bold: true, color: P.white, margin: 0, isTextBox: true });
s.addText("Effect on Vπ·L and insertion loss in the Cordoba and buffered Lisbon lifted designs", { x: 0.8, y: 3.2, w: 11.7, h: 0.6, fontFace: BF, fontSize: 22, color: "CADCFC", margin: 0, isTextBox: true });
s.addText("1575 nm  ·  550 nm LN film, 275 nm etch  ·  rib top width 1.4 µm  ·  full LN slab (no slab etch)", { x: 0.8, y: 4.5, w: 11.7, h: 0.4, fontFace: BF, fontSize: 15, color: P.gold, margin: 0, isTextBox: true });

// 2 What we studied
s = light(); title(s, "What we studied", "A thin alumina film covers every exposed surface after the electrodes are made");
const cards = [
  ["The layer", "ALD Al₂O₃, conformal on all surfaces.\nNominal thickness 40 nm, swept from 0 to 100 nm.\nOptical index 1.74, RF permittivity 9.8."],
  ["Cordoba", "Gold electrodes directly on the LN slab.\nElectrode gap 4.2 µm.\nReference: 0.43 dB/cm and 2.17 V·cm."],
  ["Lisbon lifted, buffered", "Gold on a 200 nm SiO₂ buffer.\nBottom gap 3.4 µm.\nVery low loss: 0.03 dB/cm."]];
cards.forEach(([h, t], i) => {
  const x = 0.6 + i * 4.15;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.9, w: 3.85, h: 3.2, fill: { color: P.card }, line: { color: P.card }, rectRadius: 0.12 });
  s.addText(h, { x: x + 0.3, y: 2.1, w: 3.3, h: 0.5, fontFace: HF, fontSize: 21, bold: true, color: [P.pink, "8A6A00", P.blue][i], margin: 0, isTextBox: true });
  s.addText(t, { x: x + 0.3, y: 2.75, w: 3.3, h: 2.2, fontFace: BF, fontSize: 16, color: P.ink, valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true });
});
s.addText("Questions: how much does the layer lower Vπ·L, how much loss does it add, and can it let us widen the Lisbon gap?",
  { x: 0.6, y: 5.6, w: 12.1, h: 0.8, fontFace: BF, fontSize: 17, italic: true, color: P.navy, margin: 0, isTextBox: true });

// 3 Cross sections
s = light(); title(s, "The two cross-sections with 40 nm of alumina", "Alumina shown in pink; the bottom panels zoom on the electrode corner");
img(s, F("xs_cordoba.png"), 0.4, 1.6, 6.2, 4.9);
img(s, F("xs_lisbon.png"), 6.75, 1.6, 6.2, 4.9);
s.addText("Cordoba", { x: 0.4, y: 6.55, w: 6.2, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: "8A6A00", align: "center", margin: 0, isTextBox: true });
s.addText("Lisbon lifted with 200 nm SiO₂ buffer", { x: 6.75, y: 6.55, w: 6.2, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: P.blue, align: "center", margin: 0, isTextBox: true });

// 4 Cordoba
s = light(); title(s, "Cordoba: alumina lowers Vπ·L but doubles the loss at 40 nm", "Gap 4.2 µm");
img(s, F("cordoba_sweep.png"), 0.5, 1.6, 12.3, 4.3);
stat(s, "−3 %", "Vπ·L at 40 nm (2.174 → 2.109 V·cm)", 1.5, 6.0, 4.6, "8A6A00");
stat(s, "×2.2", "loss at 40 nm (0.43 → 0.93 dB/cm)", 7.2, 6.0, 4.6, P.pink);
s.addNotes("Validated against COMSOL: the Vpi*L change matches point by point; the IL increase factor matches within about 3 %. Absolute IL differs by a constant ~25 % ratio, most likely gold permittivity or mesh at the metal in COMSOL.");

// 5 Lisbon
s = light(); title(s, "Lisbon buffered: a larger Vπ·L gain, loss stays very low", "Bottom gap 3.4 µm");
img(s, F("lisbon_sweep.png"), 0.5, 1.6, 12.3, 4.3);
stat(s, "−5.4 %", "Vπ·L at 40 nm (2.175 → 2.058 V·cm)", 1.5, 6.0, 4.6, P.blue);
stat(s, "0.055 dB/cm", "loss at 40 nm, still 8× below bare Cordoba", 7.2, 6.0, 4.6, P.pink);

// 6 Comparison
s = light(); title(s, "Side by side: same trend, different strength", "Changes are measured from each design without alumina");
img(s, F("comparison_relative.png"), 0.5, 1.6, 12.3, 4.4);
lines(s, ["Both designs start from the same Vπ·L (2.17 V·cm), but Lisbon gains almost twice as much",
  "Loss grows by a similar factor in both, yet Lisbon starts about 15 times lower"], 0.8, 6.15, 11.8, 1.0, 16);

// 7 Why
s = light(); title(s, "Why Lisbon gains more: what the alumina sits on", "Simplified drawing, not to scale");
img(s, F("mechanism.png"), 0.4, 1.55, 8.4, 3.5);
img(s, F("equal_gap_test.png"), 8.95, 1.55, 4.0, 3.5);
lines(s, ["In Cordoba, the electric field already prefers the LN, which is far more polarisable than alumina",
  "In Lisbon, alumina is the most polarisable material at the electrode level. It acts like a small extension of the electrode toward the waveguide",
  "Test: at the same 4.2 µm gap, Lisbon still gains twice as much (right). The buffer, not the narrower gap, causes the difference"],
  0.8, 5.25, 11.8, 2.0, 15);

// 8 Reliability
s = light(); title(s, "Is it the mesh? No", "Repeating the 40 nm case with a much finer mesh barely changes the results");
const H = (t) => ({ text: t, options: { bold: true, color: P.white, fill: { color: P.navy } } });
s.addTable([
  [H("Check (40 nm alumina)"), H("Mesh"), H("Vπ·L change"), H("Loss change")],
  ["Lisbon, gap 3.4 µm", "30 % finer everywhere", "+0.01 %", "−0.8 %"],
  ["Lisbon, gap 3.4 µm", "5 elements across the alumina (instead of 3)", "< 0.01 %", "−0.2 %"],
  ["Lisbon, gap 4.2 µm", "30 % finer everywhere", "+0.01 %", "−0.8 %"],
  ["Cordoba, gap 4.2 µm", "30 % finer everywhere", "+0.02 %", "−0.6 %"],
  ["Cordoba, gap 4.2 µm", "5 elements across the alumina (instead of 3)", "0.00 %", "+0.03 %"]],
  { x: 1.0, y: 1.9, w: 11.3, colW: [3.1, 4.6, 1.8, 1.8], fontFace: BF, fontSize: 15, color: P.ink, border: { type: "solid", pt: 0.5, color: "D1D5DB" }, rowH: 0.55 });
stat(s, "0.05 V·cm", "the Lisbon–Cordoba difference at 40 nm: 100× larger than any mesh effect", 3.6, 5.6, 6.1, P.blue);

// 9 Gap relaxation
s = light(); title(s, "Gap relaxation: from 3.4 µm to 3.6 µm", "Target: the Vπ·L of Lisbon without alumina at 3.4 µm (2.175 V·cm, same as Cordoba)");
img(s, F("P2_gap_relaxation.png"), 0.4, 1.6, 12.5, 4.4);
stat(s, "3.60 µm", "relaxed bottom gap with 40 nm alumina", 0.9, 6.05, 3.6, P.blue);
stat(s, "0.029 dB/cm", "loss at 3.60 µm: 15× below Cordoba", 4.85, 6.05, 3.6, P.pink);
stat(s, "+0.58 V·cm / µm", "Vπ·L cost of widening the gap", 8.8, 6.05, 3.6, P.navy);
s.addNotes("Vpi*L grows steeply with the gap, so the 0.12 V*cm gained from the alumina buys only about 0.2 um. Loss is never the limit: it falls with the gap and stays below 0.001 dB/cm at 4.8 um.");

// 10 Robustness
s = light(); title(s, "Robustness: alumina thickness ±10 nm", "The gap is fixed at 3.60 µm, designed for 40 nm");
img(s, F("P3_ald_tolerance.png"), 0.5, 1.6, 12.3, 4.5);
lines(s, ["A ±10 nm error moves Vπ·L by only ±1.1 % (2.200 to 2.152 V·cm)",
  "That equals a gap error of about 40 nm: the gap lithography matters more than the alumina control",
  "Loss stays between 0.025 and 0.033 dB/cm in all cases"], 0.8, 6.15, 11.8, 1.2, 15);

// 11 Conclusions
s = pres.addSlide(); s.background = { color: P.navy };
s.addText("Conclusions", { x: 0.8, y: 0.55, w: 11.7, h: 0.8, fontFace: HF, fontSize: 34, bold: true, color: P.white, margin: 0, isTextBox: true });
[["Alumina lowers Vπ·L in both designs", "by 3 % in Cordoba and 5.4 % in Lisbon at 40 nm"],
 ["The difference is physical", "the buffer makes the alumina more effective; the mesh is not the cause"],
 ["Loss is not a concern for Lisbon", "below 0.06 dB/cm at the original gap, below 0.03 dB/cm at 3.6 µm"],
 ["Gap gain is modest: 3.4 → 3.6 µm", "a wider gap is possible only by accepting a higher Vπ·L"],
 ["Process tolerance is comfortable", "±10 nm of alumina changes Vπ·L by about ±1 %"]].forEach(([h, t], i) => {
  const y = 1.65 + i * 1.08;
  s.addShape(pres.shapes.OVAL, { x: 0.85, y: y + 0.12, w: 0.5, h: 0.5, fill: { color: P.gold }, line: { color: P.gold } });
  s.addText(String(i + 1), { x: 0.85, y: y + 0.12, w: 0.5, h: 0.5, fontFace: HF, fontSize: 17, bold: true, color: P.navy, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText([{ text: h, options: { bold: true, color: P.gold, breakLine: true } }, { text: t, options: { color: P.white } }],
    { x: 1.65, y, w: 11.0, h: 0.9, fontFace: BF, fontSize: 18, valign: "middle", margin: 0, isTextBox: true });
});

pres.writeFile({ fileName: path.join(__dirname, "ALD_alumina_Cordoba_vs_Lisbon.pptx") }).then(f => console.log("wrote", f));
