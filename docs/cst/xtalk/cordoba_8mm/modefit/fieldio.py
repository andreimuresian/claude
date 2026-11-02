"""Read a CST field export (3D Export in Volume) whether it is the ASCII table (.txt: two header lines,
whitespace columns) or the CSV variant (.csv: comma-separated, header line(s) with quoted names).
Returns the numeric table: x, y, z, ExRe, ExIm, EyRe, EyIm, EzRe, EzIm (one row per point)."""
import numpy as np

def load_field_table(path):
    rows = []
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            parts = line.replace(";", ",").replace(",", " ").split()
            try:
                vals = [float(p) for p in parts]
            except ValueError:
                continue                      # header, separator or unit line
            if len(vals) >= 9:
                rows.append(vals[:9])
    if not rows:
        raise ValueError(f"{path}: no numeric rows with 9 columns")
    return np.array(rows)
