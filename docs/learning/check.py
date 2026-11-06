"""Checker for docs/learning/toy_problems.md. Says right / wrong (and, for known mistakes, which step to look at)
without showing the answer. Hints and solutions on request.

    python3 check.py P3 -36.0
    python3 check.py P6 -41.7 60
    python3 check.py hint P3 2
    python3 check.py solution P3
"""
import base64, json, os, sys, zlib

K = json.loads(zlib.decompress(base64.b64decode(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.dat"), "rb").read())))


def ok(x, ref, tol):
    kind, t = tol
    return abs(x - ref) <= (t * abs(ref) if kind == "rel" else t)


def near(vals, pattern, tols):
    return all(p is None or ok(v, p, t) for v, p, t in zip(vals, pattern, tols))


def main(a):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    if a[0] == "hint":
        p, lvl = a[1].upper(), int(a[2]) if len(a) > 2 else 1
        h = K[p]["hints"]
        print(f"{p} hint {lvl}/{len(h)}: {h[min(lvl, len(h)) - 1]}"); return
    if a[0] == "solution":
        p = a[1].upper()
        if input(f"Show the full solution of {p}? Type yes: ").strip().lower() == "yes":
            print(K[p]["sol"])
        return
    p = a[0].upper()
    k = K[p]
    vals = [float(v) for v in a[1:]]
    if len(vals) != k["n"]:
        print(f"{p} expects {k['n']} number(s)."); return
    good = [ok(v, r, t) for v, r, t in zip(vals, k["ans"], k["tol"])]
    if all(good):
        print(f"{p}: correct."); return
    for pat, msg in k["wrong"]:
        if near(vals, pat, k["tol"]):
            print(f"{p}: not yet. {msg}"); return
    if k["n"] > 1:
        print(f"{p}: " + ", ".join(f"value {i + 1} {'right' if g else 'wrong'}" for i, g in enumerate(good)) + ".")
    else:
        print(f"{p}: wrong. Try 'hint {p} 1'.")


if __name__ == "__main__":
    main(sys.argv[1:])
