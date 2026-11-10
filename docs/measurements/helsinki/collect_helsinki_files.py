"""
Collect the HELSINKI line measurements before (MTX) and after (ALD_SPUTTER) the Al2O3 layer, wafer 5HK0005.

  S:\\Compott\\Testing\\RF TEST PROBE\\HELSINKI\\5HK0005\\MTX\\LINEA NN\\1.s2p
      ->  T:\\Personal_Folders\\Muresian\\ALD RF impact lab results\\Helsinki\\5HK0005\\no ALD\\NN_no_ALD.s2p
  S:\\Compott\\Testing\\RF TEST PROBE\\HELSINKI\\5HK0005\\ALD_SPUTTER\\LINEA NN\\1.s2p
      ->  T:\\Personal_Folders\\Muresian\\ALD RF impact lab results\\Helsinki\\5HK0005\\ALD\\NN_ALD.s2p
NN = 00..07, read from the folder name. Source files are only read (copied with their timestamps), never changed.

Run:   python collect_helsinki_files.py            (copies)
       python collect_helsinki_files.py --dry-run  (only lists what it would copy)
At the end it prints a table of what was found and copied, and writes it to <DEST>\\collect_log.csv.
"""
import argparse
import csv
import os
import re
import shutil

SRC_ROOT = r"S:\Compott\Testing\RF TEST PROBE\HELSINKI\5HK0005"
DEST_ROOT = r"T:\Personal_Folders\Muresian\ALD RF impact lab results\Helsinki\5HK0005"
# source folder -> (destination subfolder, label in the file name)
STATES = {"MTX": ("no ALD", "no_ALD"), "ALD_SPUTTER": ("ALD", "ALD")}
FILE_NAME = "1.s2p"
N_LINES = 8
FOLDER_RE = re.compile(r"^\s*LINEA\s+(\d{2})\s*$", re.IGNORECASE)


def collect(dry_run: bool) -> None:
    log = []
    for src_state, (dest_sub, label) in STATES.items():
        state_dir = os.path.join(SRC_ROOT, src_state)
        dest = os.path.join(DEST_ROOT, dest_sub)
        if not os.path.isdir(state_dir):
            print(f"[MISSING FOLDER] {state_dir}")
            log.append((label, "", state_dir, "", "missing folder"))
            continue
        if not dry_run:
            os.makedirs(dest, exist_ok=True)
        found = {}
        for name in sorted(os.listdir(state_dir)):
            m = FOLDER_RE.match(name)
            if m and os.path.isdir(os.path.join(state_dir, name)):
                found[m.group(1)] = name
        for nn in [f"{i:02d}" for i in range(N_LINES)]:
            if nn not in found:
                print(f"[MISSING LINE]   {src_state} LINEA {nn}")
                log.append((label, nn, "", "", "missing line folder"))
                continue
            src = os.path.join(state_dir, found[nn], FILE_NAME)
            dst = os.path.join(dest, f"{nn}_{label}.s2p")
            if not os.path.isfile(src):
                print(f"[MISSING FILE]   {src}")
                log.append((label, nn, src, dst, f"missing {FILE_NAME}"))
                continue
            status = "would copy" if dry_run else ("overwritten" if os.path.exists(dst) else "copied")
            if not dry_run:
                shutil.copy2(src, dst)
            print(f"[{status.upper():11s}] {src}  ->  {dst}")
            log.append((label, nn, src, dst, status))
        extra = sorted(set(found) - {f"{i:02d}" for i in range(N_LINES)})
        if extra:
            print(f"[NOTE] {src_state}: extra line folders not copied: {extra}")
    n_ok = sum(1 for r in log if r[4] in ("copied", "overwritten", "would copy"))
    print(f"== 5HK0005: {n_ok} of {2 * N_LINES} files {'found' if dry_run else 'copied'}\n")
    if not dry_run:
        os.makedirs(DEST_ROOT, exist_ok=True)
        with open(os.path.join(DEST_ROOT, "collect_log.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["state", "line", "source", "destination", "status"])
            w.writerows(log)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="list what would be copied, copy nothing")
    collect(ap.parse_args().dry_run)
