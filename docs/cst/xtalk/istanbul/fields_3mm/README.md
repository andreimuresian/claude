# Istanbul 3 mm (w = 1 mm) -- E and H field planes, port 1, for the mode model

Source run: `TEST0_XTALK_SW__3p00mm.s4p` (same model, same mesh family as the 5 mm line).
One E file and one H file per frequency, CST "3D Export in Volume", Use Subvolume, ASCII:

| setting | value |
|---|---|
| monitors | `e-field (f=<f>) [1]` and `h-field (f=<f>) [1]` |
| frequencies (GHz) | 10, 20, 30, 45, 60, 80 |
| x min = x max | 0.001 |
| y | -0.40 to 0.40 |
| z | 0 to 3 |
| step | 0.005 |

161 x 601 points per file (about 14 MB). Any file names are fine: the frequency, the field (E/H)
and the port are read from the CST default name, e.g. `e-field (f=30.0000) [1].txt`.
The 5 mm counterparts (full planes) are not stored in the repository (24 MB each); their gap
columns are in `../fields_5mm`.

## Contents
* `e-field_3mm_port1_10-80GHz.zip`: `e-field (f=<f>) [1].txt`, f = 10, 20, 30, 45, 60, 80 GHz
* `h-field_3mm_port1_10-80GHz.zip`: `h-field (f=<f>) [1].txt`, same frequencies
Checked: 96761 rows each, x = 0.001, y -0.40..0.40 (161), z 0..3 (601).

## Gap columns for the field-based EO crosstalk
`e-field_f<f>_1_<A|B>.txt` (f = 10, 20, 30, 45, 60, 80 GHz): cut from the planes, same format as
`../fields_5mm` (x = 0.001, y = 0.305..0.320 / -0.320..-0.305, z 0..3). Use with
`TEST0_XTALK_SW__3p00mm.s4p`, length 3 mm, in the Crosstalk-from-s4p window. Other ports by
symmetry (verified on the 5 mm line of the same family; not on this one).
