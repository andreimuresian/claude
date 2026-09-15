#!/usr/bin/env python
"""
Launcher for MZM Studio.

    python run_mzm_studio.py                     # dark theme, empty form
    python run_mzm_studio.py path/to/line.s2p    # open with that file loaded
    python run_mzm_studio.py --light
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mzm_interconnect import parameters as P   # noqa: E402
from mzm_interconnect.gui import launch        # noqa: E402

if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    theme = "light" if "--light" in args else "dark"
    args = [a for a in args if not a.startswith("--")]
    initial = None
    if args and os.path.isfile(args[0]):
        initial = P.defaults()
        initial["s2p_path"] = os.path.abspath(args[0])
        initial["out_dir"] = os.path.dirname(os.path.abspath(args[0]))
    launch(initial, theme=theme)
