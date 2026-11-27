"""Robust wrapper: try mesh / solver variants until a clean rib mode is found.  Same args as run_m1.py."""
import os, subprocess, sys
VARIANTS = [dict(RIBPATCH="0", MS="1.4"), dict(RIBPATCH="1", MS="1.4"),
            dict(RIBPATCH="0", MS="1.4", NMODES="6", NGUESS=os.environ.get("NGUESS","1.885")), dict(RIBPATCH="1", MS="1.4", NMODES="6", NGUESS=os.environ.get("NGUESS","1.885")),
            dict(RIBPATCH="0", MS="1.3"), dict(RIBPATCH="0", MS="1.3", NMODES="6", NGUESS=os.environ.get("NGUESS","1.885")),
            dict(RIBPATCH="0", MS="1.2", NMODES="10", NGUESS=os.environ.get("NGUESS","1.89"))]
for v in VARIANTS:
    out = subprocess.run([sys.executable, "/home/user/claude/results/madrid/m1/run_m1.py", *sys.argv[1:]], env=dict(os.environ, **v),
                         capture_output=True, text=True).stdout
    line = [l for l in out.splitlines() if l.startswith("RESULT")]
    if line:
        tag = ", ".join(f'"{k.lower()}": "{x}"' for k, x in v.items())
        print(line[0][:-1] + ", " + tag + "}", flush=True); break
else:
    print("FAIL " + " ".join(sys.argv[1:]), flush=True)
