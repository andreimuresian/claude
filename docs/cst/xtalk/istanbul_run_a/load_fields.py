"""Load the run (a) gap-field exports (zips as uploaded) into the dict used by mzm_interconnect.xtalk_fields.
Line A: txt, y -0.0075..0.0075 (first export) and y -0.005..0.005 (re-export, gaps at +-5 um, used); line B: CST CSV (';'), y -0.63..-0.615 (not the planned -0.6325..-0.6175).
Gap columns: A y = -0.0075 / +0.0075 (7.5 um from the line centre); B y = -0.63 / -0.62 (5 um from the centre,
0.15 um from the signal edge at 4.85 um). B y = -0.615 lies in the ground (zero at 1579 of 1751 z) and is dropped.
z: 0.3025..9.0525 step 0.005; the last point (9.0525, beyond the far port at 9.05) is zero everywhere and is dropped."""
import os, re, io, zipfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
# Default: line A re-exported at y -0.005..0.005 (gaps at +-5 um), the same position in the gap as line B.
# variant="A7.5": the first line A export (gaps at +-7.5 um), kept for the bias check.
VARIANTS = {"A5": ("e-field (f=1) [1]_lineA_5um.zip", (0.005, -0.005)),
            "A7.5": ("e-field (f=1) [1]_lineA.zip", (0.0075, -0.0075))}
B_ZIP, B_GAPS = "e-field (f=1) [1]_lineB.zip", (-0.62, -0.63)  # (+y side gap, -y side gap) in mm


def _read(raw: bytes):
    t = raw.decode()
    if t.lstrip().startswith("#"):
        return np.loadtxt(io.StringIO(t), delimiter=";", skiprows=1)
    return np.loadtxt(io.StringIO(t), skiprows=2)


def load(variant="A5", base=HERE, a_zip=None, drop="last", skip_f=()):
    """base: folder with the zips (run a by default; run b: ../istanbul_run_b with a_zip its line A zip, same grid).
    drop: z point to discard, "last" (runs a, b: 9.0525 beyond the far port, zero) or "first" (run c: grid 0.300..9.050,
    line A is zero at z = 0.300, the line/pad boundary).
    skip_f: frequencies (GHz) to leave out (run c: corrupted line B exports at 2 and 15 GHz)."""
    ZIPS = {"A": a_zip or VARIANTS[variant][0], "B": B_ZIP}
    GAPS = {"A": VARIANTS[variant][1], "B": B_GAPS}
    data, z_ref = {}, None
    for line, zn in ZIPS.items():
        with zipfile.ZipFile(os.path.join(base, zn)) as zf:
            for name in zf.namelist():
                f = float(re.search(r"f=(\d+(?:\.\d+)?)", name).group(1))
                if f in skip_f:
                    continue
                a = _read(zf.read(name))
                cols = []
                for y in GAPS[line]:
                    m = np.isclose(a[:, 1], y, atol=1e-7)
                    z = a[m, 2]; o = np.argsort(z)
                    sl = slice(None, -1) if drop == "last" else slice(1, None)
                    cols.append(((a[m, 5] + 1j * a[m, 6])[o])[sl]); zz = z[o][sl]
                if z_ref is None:
                    z_ref = zz
                assert np.allclose(zz, z_ref)
                assert all(np.all(np.abs(c) > 0) for c in cols), (line, name)
                data.setdefault(f, {})[line] = tuple(cols)
    fs = np.array(sorted(data))
    return dict(f_GHz=fs, ports={f: {1: data[f]} for f in fs}, z=z_ref * 1e-3, path=base)
