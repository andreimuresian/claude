# Notes for Claude

- Technical reports for this project follow `docs/reports/REPORT_STYLE.md` (the user's standing rules).
- Chat replies render as GitHub-flavoured Markdown: write math only with `$...$` (inline) and `$$...$$` (display). Never `\(...\)` or `\[...\]`: Markdown strips the backslashes and eats underscores, so the formulas arrive broken.
- CST field exports (3D Export in Volume, ASCII): the step size is ONE value common to x, y and z. Specify export
  settings as a box (x, y, z ranges) plus a single step; never give separate steps per direction.
  Standard gap export: x 0.001 (min = max), y 0.2925..0.3325 (line A) or -0.3325..-0.2925 (line B), z 0..8, step 0.005.
- Presentations (user's standing rules): short (few slides, only the essential messages), not descriptive (results and
  conclusions, not narration of what was done), formal impersonal language (no "we"/"our"/"I"). Company template:
  `docs/CST_line_extraction.pptx` (see `docs/cst/xtalk/deck/build_istanbul.py`). All dB plots start at 0 dB at the top.
