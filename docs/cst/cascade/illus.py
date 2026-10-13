import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
G, P, B, Z, X = '#4e8a12', '#e07b18', '#5aa0f0', '#8a5ad0', '#c0392b'
fig, ax = plt.subplots(figsize=(13, 7.6)); ax.set_xlim(-0.2, 13.2); ax.set_ylim(-0.6, 9.2); ax.axis('off')
def ref(x, y, col, lab, dashed=True):
    ax.add_patch(Rectangle((x, y-.3), .5, .6, fc='none' if dashed else col, ec=col, lw=2, ls='--' if dashed else '-'))
    ax.text(x+.25, y, lab, ha='center', va='center', fontsize=8, color=col, weight='bold')
def port(x, y): ax.add_patch(Rectangle((x, y-.22), .3, .44, fc=P, ec='k', lw=.6))
def line(x0, x1, y): ax.add_patch(Rectangle((x0, y-.07), x1-x0, .14, fc=B, ec='none'))
def row(y, title, segs, inner, outer, outer_lab):
    ax.text(0, y+(1.45 if inner else .62), title, fontsize=10.5, weight='bold', va='bottom')
    ref(0.3, y, outer, outer_lab); x = 0.8; L = 11.6/segs
    for k in range(segs):
        port(x, y); line(x+.3, x+L-.3, y); port(x+L-.3, y)
        if k < segs-1 and inner: ref(x+L-.25, y+.55, X, '50Ω'); ax.text(x+L, y+1.0, '✗', color=X, ha='center', fontsize=12)
        x += L
    ref(x, y, outer, outer_lab)
row(8.0, 'A. 5 mm CST run: one line, one port region at each end', 1, False, G, '50Ω')
row(5.7, 'B. Your picture of the 1 mm × 5 cascade: a 50 Ω mismatch at every joint (this does NOT happen)', 5, True, G, '50Ω')
row(3.6, 'C. What the cascade really is: 50 Ω only at the outer ends; the joints are line → line, but each joint keeps two port regions', 5, False, G, '50Ω')
row(1.3, 'D. C renormalised to Zc: only the outer references change (as in A); the port regions at the joints stay', 5, False, Z, 'Zc')
ax.text(0.3, -0.35, 'dashed box = reference impedance (bookkeeping only, not in the circuit)     orange = CST port region (real simulated '
        'transition, inside the data)     blue = uniform line', fontsize=8.5, color='#333')
for y, t in [(8.0, '2 port regions'), (3.6, '10 port regions'), (1.3, '10 port regions')]:
    ax.text(13.15, y-.55, t, ha='right', fontsize=9, color=P, weight='bold')
fig.tight_layout(); fig.savefig('cascade_illustration.png', dpi=150)
