# Notes for Claude

- Technical reports for this project follow `docs/reports/REPORT_STYLE.md` (the user's standing rules).
- Chat replies render as GitHub-flavoured Markdown: write math only with `$...$` (inline) and `$$...$$` (display). Never `\(...\)` or `\[...\]`: Markdown strips the backslashes and eats underscores, so the formulas arrive broken.
- CST field exports (3D Export in Volume, ASCII): the step size is ONE value common to x, y and z. Specify export
  settings as a box (x, y, z ranges) plus a single step; never give separate steps per direction.
  Standard gap export: x 0.001 (min = max), y 0.2925..0.3325 (line A) or -0.3325..-0.2925 (line B), z 0..8, step 0.005.
  Gap-voltage exports: one region per gap with y min = max at the gap centre (WS/2 + GAP/2 from the line centre) and
  x at electrode mid-height. A y range is snapped by CST to multiples of the step (Istanbul: points landed next to the
  signal edge). Before any analysis, check the exported x, y in the file against the intended gap centre.
- Presentations (user's standing rules): short (few slides, only the essential messages), not descriptive (results and
  conclusions, not narration of what was done), formal impersonal language (no "we"/"our"/"I"). Company template:
  `docs/CST_line_extraction.pptx` (see `docs/cst/xtalk/deck/build_istanbul.py`). All dB plots start at 0 dB at the top.
- Slide content (lessons from the Istanbul deck review, user's standing rules):
  - Write for the audience, not for yourself: every number on a slide says what it is (mean, median, maximum, over
    what range, relative to what) and where it comes from. No unexplained figures such as "150 ps" or "2.2 dB for 2.5 µm".
  - Prefer an illustration to text: geometry, sampling points, coupling paths, signal flow are drawn, not described.
  - Draw only what was simulated: read the model and the exports (coordinates, ports, materials) before drawing any
    geometry. Never add elements that are not in the simulation.
  - State every dependence and weakness up front: if a "field-based" result uses the touchstone, if sampling points
    are not where intended, if a parameter was chosen by judgement. Never bury it in a note or a passing phrase.
  - Justify every processing choice (fit windows, thresholds, averaging) with a sensitivity test, or remove it and
    use the simplest option.
  - Equations rendered (mathtext images), large enough to read; no "exp(...)" in text. Define every symbol.
  - Derivations as a chain: each step states why it follows from the previous one and its physical meaning.
  - Drop slides about methods that were abandoned; keep only what supports the conclusions.
  - Review workflow: send one slide image at a time for approval; build and send the full .pptx only at the end.
- Figures (user's standing rule): a legend must never overlap plot curves. Inside the axes is fine if it sits in empty space; otherwise put it outside. Check the rendered image.
- Spelling: British English in all answers, reports and slides (equaliser, polarisation, modelling, colour).
- Answer style (user's standing instructions, from their Claude Code settings): all answers brief and concise, short
  and direct to the point (the user hates long answers). Natural language with a logical flow. Use examples,
  similarities and metaphors. Discussions are mainly physics related to the user's work: always make the real
  physical meaning of equations, plots and results clear.
