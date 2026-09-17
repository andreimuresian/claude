"""3D periodic unit cell of the T-stub loaded CPW.

Replaces the four CST Multilayer runs per geometry (200 um etched and
unetched, 400 um and 600 um arrays) with quasi-static solves on a single
200 um cell.  There are no ports anywhere in this formulation, so there is no
port mismatch to de-embed and the N+1 minus N difference is not needed.
"""

from .cell import build
from .electrostatic import capacitance, penalties

__all__ = ["build", "capacitance", "penalties"]
