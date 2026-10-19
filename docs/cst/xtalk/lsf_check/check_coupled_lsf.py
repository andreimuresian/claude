"""Run lumerical/coupled_element_setup.lsf in numpy (lsf_exec.py translates the
LSF subset the scripted elements use) and compare every entry with the Python
twin, coupled_line.py. Run from this folder: python check_coupled_lsf.py"""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from lsf_exec import run
from mzm_interconnect.coupled_line import coupled_sparams_from_tables
from mzm_interconnect.scripted_line import read_tl_table
d = os.path.join(HERE, '..', 'coupled_tables') + os.sep
pe, po = d + 'xtalk200_dz45_even.txt', d + 'xtalk200_dz45_odd.txt'
def rd(p):
    rows = [list(map(float, l.split())) for l in open(p) if l.strip() and not l.strip()[0].isalpha()]
    return np.array(rows)
L, ng, ng2 = 14e-3, 2.27, 2.31
props = dict(table_even=pe, table_odd=po, line_length=L, ng=ng, ng2=ng2, second_modulation=1, R0=50.0,
             far_end_output=1, near_end_output=1, modulating=1, wave_convention="voltage", phase_convention="engineering", fir_taps=0)
S, LOG, code = run(os.path.join(ROOT, 'mzm_interconnect', 'lumerical', 'coupled_element_setup.lsf'), props, rd)
B = coupled_sparams_from_tables(pe, po, L, ng=ng, ng2=ng2)
P = ["A1", "A2", "B1", "B2"]
err = 0
for i in range(4):
    for j in range(4):
        x = S[(P[i], P[j])][1:]; y = B["S"][i][j][1:]   # skip DC row
        err = max(err, np.max(np.abs(x - y)))
print("S max diff", err, " entries", len(S))
for key, names in (("T", ("modulation A", "modulation B")), ("T2", ("modulation 2 A", "modulation 2 B")),
                   ("FE", ("far end A", "far end B")), ("NE", ("near end A", "near end B"))):
    e = 0
    for k in range(2):
        for j in range(4):
            x = S[(names[k], P[j])][1:]; y = B[key][k][j][1:]
            e = max(e, np.max(np.abs(x - y)) / np.max(np.abs(y)))
    print(key, "max rel diff", e)
print(LOG)

r = __import__("mzm_interconnect.coupled_line", fromlist=["x"]).terminated_response(B, 35.0, 42.0)
print("V check NE_B vs V[B1]", np.max(abs(r["NE_B"] - r["V"][2])), " FE_B vs V[B2]", np.max(abs(r["FE_B"] - r["V"][3])))
