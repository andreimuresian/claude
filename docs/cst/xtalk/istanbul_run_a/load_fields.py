"""Load the run (a) gap-field exports (zips as uploaded) into the dict used by mzm_interconnect.xtalk_fields.
Line A: txt, y -0.0075..0.0075; line B: CST CSV (';'), y -0.63..-0.615 (not the planned -0.6325..-0.6175).
Gap columns: A y = -0.0075 / +0.0075 (7.5 um from the line centre); B y = -0.63 / -0.62 (5 um from the centre,
0.15 um from the signal edge at 4.85 um). B y = -0.615 lies in the ground (zero at 1579 of 1751 z) and is dropped.
z: 0.3025..9.0525 step 0.005; the last point (9.0525, beyond the far port at 9.05) is zero everywhere and is dropped."""
import os, re, io, zipfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ZIPS = {"A": "e-field (f=1) [1]_lineA.zip", "B": "e-field (f=1) [1]_lineB.zip"}
GAPS = {"A": (0.0075, -0.0075), "B": (-0.62, -0.63)}          # (+y side gap, -y side gap) in mm


def _read(raw: bytes):
    t = raw.decode()
    if t.lstrip().startswith("#"):
        return np.loadtxt(io.StringIO(t), delimiter=";", skiprows=1)
    return np.loadtxt(io.StringIO(t), skiprows=2)


def load():
    data, z_ref = {}, None
    for line, zn in ZIPS.items():
        with zipfile.ZipFile(os.path.join(HERE, zn)) as zf:
            for name in zf.namelist():
                f = float(re.search(r"f=(\d+(?:\.\d+)?)", name).group(1))
                a = _read(zf.read(name))
                cols = []
                for y in GAPS[line]:
                    m = np.isclose(a[:, 1], y, atol=1e-7)
                    z = a[m, 2]; o = np.argsort(z)
                    cols.append(((a[m, 5] + 1j * a[m, 6])[o])[:-1]); zz = z[o][:-1]
                if z_ref is None:
                    z_ref = zz
                assert np.allclose(zz, z_ref)
                assert all(np.all(np.abs(c) > 0) for c in cols), (line, name)
                data.setdefault(f, {})[line] = tuple(cols)
    fs = np.array(sorted(data))
    return dict(f_GHz=fs, ports={f: {1: data[f]} for f in fs}, z=z_ref * 1e-3, path=HERE)
