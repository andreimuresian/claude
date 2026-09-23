"""Phase-0 gate: every dataset column must either reach the model or be
recorded here as an intentional exclusion, with a reason.

This exists because MTX and CAP_W were parsed into the geometry dict and then
used by nothing, and sat that way through three phases without anyone noticing.
MTX turned out to be the single strongest geometry predictor in the dataset
(t = -83 against nm_baseline).  Nothing in the pipeline checked that an input
actually reached the solver, so nothing caught it.

Run it as a test:  python phase0_column_coverage.py   (exit 1 on an undocumented
input column).  Add a column here the moment the dataset gains one.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = ["mesh_generator.py", "phase3_run.py", "bloch_solver.py",
       "floquet_greens.py", "layered_greens.py", "mom_solver.py",
       "common_mesh.py"]

# columns consumed as model INPUTS
INPUTS = ["WS", "GAP", "MTX", "CAP_W", "L1", "L2", "W1", "W2", "ETCH_DEPTH"]

# columns that are REFERENCE ONLY -- scoring targets, never inputs.  The
# standing order is that the dataset is a test fixture: no fit, no surrogate,
# no lookup, and none of these may ever be read at solve time.
REFERENCE = ["deltaL lumped", "deltaC lumped", "nm_baseline_val",
             "z0_baseline_val", "alpha_baseline_val", "nm_final_val",
             "z0_final_val", "alpha_delta_val", "alpha_final_val"]

# inputs deliberately NOT modelled, each with a reason
EXCLUDED = {
    "MTX": ("Electrode thickness.  The RWG formulation places current on a "
            "zero-thickness sheet, so MTX has no representation.  KNOWN GAP, "
            "not benign: it is the strongest single geometry predictor in the "
            "dataset and a 2D electrostatic probe reproduces CST's partial to "
            "4 % once thickness is included.  Closing it needs the 3D "
            "closed-surface build."),
    "CAP_W": ("Width of the SiO2 cap above the optical rib.  Confirmed by the "
              "project owner that this cap was never built in the CST model "
              "that generated the reference data, so there is nothing to "
              "reproduce.  Its apparent regression significance (t = 5.1) is "
              "confounding through GAP (r = 0.45)."),
}


def used_in_source(col):
    """True if the column's VALUE is actually read outside the parse function.

    The first version of this check looked for the bare word and reported MTX
    as used, because mom_solver's module docstring contains the phrase
    "MTX up to ~14 um".  A coverage gate that false-passes the one column that
    motivated it is worse than no gate, so the match now requires a real
    subscript or attribute access -- g["MTX"], row['MTX'], row.MTX -- and the
    body of geom_from_row (which only copies row -> dict) is skipped.
    """
    pat = re.compile(r"""\[\s*["']%s["']\s*\]|\.%s\b""" % (re.escape(col),
                                                             re.escape(col)))
    for f in SRC:
        p = HERE / f
        if not p.exists():
            continue
        lines = p.read_text().splitlines()
        skip = set()
        for i, line in enumerate(lines):          # skip the geom_from_row body
            if re.match(r"\s*def geom_from_row\b", line):
                j = i + 1
                while j < len(lines) and (not lines[j].strip()
                                          or lines[j].startswith((" ", "\t"))):
                    skip.add(j); j += 1
        for i, line in enumerate(lines):
            if i in skip or line.strip().startswith("#"):
                continue
            if pat.search(line):
                return True
    return False


def main():
    bad = []
    print("Phase-0 dataset column coverage")
    print("-" * 72)
    for c in INPUTS:
        if used_in_source(c):
            print("  %-12s reaches the model" % c)
        elif c in EXCLUDED:
            print("  %-12s EXCLUDED - %s" % (c, EXCLUDED[c][:60] + "..."))
        else:
            print("  %-12s *** UNDOCUMENTED GAP ***" % c)
            bad.append(c)
    print("  %d reference columns (scoring only, never read at solve time)"
          % len(REFERENCE))
    print("-" * 72)
    if bad:
        print("FAIL: %d input column(s) neither used nor documented: %s"
              % (len(bad), ", ".join(bad)))
        return 1
    print("PASS: every input column is used or documented as excluded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
