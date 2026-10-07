"""Where the dataset's large alpha_delta lives: median alpha_delta and the share
of rows with alpha_delta > 2 dB/cm, by the outer ground strip left behind the
slot (70 - W1 - W2, um) and the head-slot length L2 (um).  Test fixture only:
a description of the data, not a fit.   Run: python dataset_regime.py (-> dataset_regime.txt)
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = pd.read_excel(os.path.join(HERE, '..', 'mom', 'data', 'EVALUATED_FULL_LHS_DATASET.xlsx'))
D['strip'] = 70 - D.W1 - D.W2
D['big'] = D.alpha_delta_val > 2
for c in ('strip', 'L2', 'W1', 'WS', 'W2', 'L1', 'GAP', 'MTX'):
    print(f"Spearman(alpha_delta, {c:5}) = {D[c].corr(D.alpha_delta_val, method='spearman'):+.2f}")
D['L2 (um)'] = pd.cut(D.L2, [0, 100, 130, 150, 170, 200])
D['strip (um)'] = pd.cut(D.strip, [5, 10, 20, 40, 70])
for name, v, f in (("median alpha_delta (dB/cm)", 'alpha_delta_val', 'median'),
                   ("share of rows with alpha_delta > 2 dB/cm", 'big', 'mean'), ("rows", 'big', 'count')):
    print(f"\n{name}")
    print(D.pivot_table(index='L2 (um)', columns='strip (um)', values=v, aggfunc=f, observed=False).round(2).to_string())
