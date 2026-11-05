"""
Collect the CORDOBA 8 mm line measurements before (MTX) and after (ALD) the Al2O3 layer into one folder per wafer.

For each wafer W in WAFERS:
  S:\\Compott\\Testing\\RF TEST PROBE\\CORDOBA\\W\\MTX\\LINEA CHIP COR T2 NN\\3.s2p  ->  <DEST>\\W\\W_noALD_NN.s2p
  S:\\Compott\\Testing\\RF TEST PROBE\\CORDOBA\\W\\ALD\\LINEA CHIP COR T2 NN\\3.s2p  ->  <DEST>\\W\\W_ALD_NN.s2p
NN = 00..14, read from the folder name. Source files are only read (copied with their timestamps), never changed.

Run:   python collect_ald_files.py            (copies)
       python collect_ald_files.py --dry-run  (only lists what it would copy)
At the end it prints a table of what was found and copied, and writes it to <DEST>\\W\\collect_log.csv.
"""
import argparse
import csv
import os
import re
import shutil

SRC_ROOT = r"S:\Compott\Testing\RF TEST PROBE\CORDOBA"
DEST_ROOT = r"T:\Personal_Folders\Muresian\ALD RF impact lab results"
WAFERS = ["4CA0162", "4CA0163"]
STATES = {"MTX": "noALD", "ALD": "ALD"}      # source folder -> label in the file name
FILE_NAME = "3.s2p"
N_LINES = 15
FOLDER_RE = re.compile(r"^\s*LINEA\s+CHIP\s+COR\s+T2\s+(\d{2})\s*$", re.IGNORECASE)


def collect(dry_run: bool) -> None:
    for wafer in WAFERS:
        dest = os.path.join(DEST_ROOT, wafer)
        if not dry_run:
            os.makedirs(dest, exist_ok=True)
        log = []
        for src_state, label in STATES.items():
            state_dir = os.path.join(SRC_ROOT, wafer, src_state)
            if not os.path.isdir(state_dir):
                print(f"[MISSING FOLDER] {state_dir}")
                log.append((wafer, label, "", state_dir, "", "missing folder"))
                continue
            found = {}
            for name in sorted(os.listdir(state_dir)):
                m = FOLDER_RE.match(name)
                if m and os.path.isdir(os.path.join(state_dir, name)):
                    found[m.group(1)] = name
            for nn in [f"{i:02d}" for i in range(N_LINES)]:
                if nn not in found:
                    print(f"[MISSING LINE]   {wafer} {src_state} LINEA CHIP COR T2 {nn}")
                    log.append((wafer, label, nn, "", "", "missing line folder"))
                    continue
                src = os.path.join(state_dir, found[nn], FILE_NAME)
                dst = os.path.join(dest, f"{wafer}_{label}_{nn}.s2p")
                if not os.path.isfile(src):
                    print(f"[MISSING FILE]   {src}")
                    log.append((wafer, label, nn, src, dst, "missing 3.s2p"))
                    continue
                status = "would copy" if dry_run else ("overwritten" if os.path.exists(dst) else "copied")
                if not dry_run:
                    shutil.copy2(src, dst)
                print(f"[{status.upper():11s}] {src}  ->  {dst}")
                log.append((wafer, label, nn, src, dst, status))
            extra = sorted(set(found) - {f"{i:02d}" for i in range(N_LINES)})
            if extra:
                print(f"[NOTE] {wafer} {src_state}: extra line folders not copied: {extra}")
        n_ok = sum(1 for r in log if r[5] in ("copied", "overwritten", "would copy"))
        print(f"== {wafer}: {n_ok} of {2 * N_LINES} files {'found' if dry_run else 'copied'}\n")
        if not dry_run:
            with open(os.path.join(dest, "collect_log.csv"), "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["wafer", "state", "line", "source", "destination", "status"])
                w.writerows(log)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="list what would be copied, copy nothing")
    collect(ap.parse_args().dry_run)
