"""Robust wrapper: try mesh variants until a clean rib mode is found.  Same args as run_m1.py."""
import os, subprocess, sys
VARIANTS = [("0", "1.4"), ("1", "1.4"), ("0", "1.3"), ("1", "1.3")]
for rp, ms in VARIANTS:
    env = dict(os.environ, RIBPATCH=rp, MS=ms)
    out = subprocess.run([sys.executable, "/home/user/claude/results/madrid/m1/run_m1.py", *sys.argv[1:]], env=env,
                         capture_output=True, text=True).stdout
    line = [l for l in out.splitlines() if l.startswith("RESULT")]
    if line:
        print(line[0][:-1] + f', "ribpatch": {rp}, "ms": {ms}}}', flush=True); break
else:
    print("FAIL " + " ".join(sys.argv[1:]), flush=True)
