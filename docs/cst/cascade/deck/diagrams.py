import os, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
NAVY, RED, BLUE, ORANGE, GREY, GREEN = '#0E2268', '#F20013', '#5AA0F0', '#E07B39', '#8A8F99', '#2E8B57'
def sv(fig, n): fig.savefig(os.path.join(IMG, n), dpi=180, bbox_inches='tight', transparent=False, facecolor='white'); plt.close(fig)

# --- runs diagram
fig, ax = plt.subplots(figsize=(8, 2.6)); ax.axis('off'); ax.set_xlim(-1.2, 10.4); ax.set_ylim(-0.4, 3.1)
for y, L, lab in [(2.5, 0.9, '0.5 mm'), (1.5, 1.8, '1 mm'), (0.5, 9.0, '5 mm')]:
    ax.add_patch(Rectangle((0, y-.2), .35, .4, fc=ORANGE, ec='k', lw=.6)); ax.add_patch(Rectangle((.35, y-.06), L, .12, fc=BLUE))
    ax.add_patch(Rectangle((.35+L, y-.2), .35, .4, fc=ORANGE, ec='k', lw=.6)); ax.text(-0.2, y, lab, ha='right', va='center', fontsize=12, weight='bold', color=NAVY)
ax.text(0, -0.25, 'orange = CST waveguide port region (same in every run)    blue = uniform CPW line', fontsize=10, color='#444')
sv(fig, 'runs.png')

# --- port model diagram
fig, ax = plt.subplots(figsize=(9.5, 2.9)); ax.axis('off'); ax.set_xlim(0, 19); ax.set_ylim(-1.3, 3.6)
def box(x, w, col, lab, sub=None):
    ax.add_patch(Rectangle((x, 1.3), w, 1.4, fc=col, ec='k', lw=.8)); ax.text(x+w/2, 2.0, lab, ha='center', va='center', fontsize=15, weight='bold', color='white' if col != 'white' else NAVY)
    if sub: ax.text(x+w/2, 0.95, sub, ha='center', va='top', fontsize=10, color='#333')
box(0.5, 2.6, ORANGE, 'P', 'port 1 region'); box(3.6, 11.0, BLUE, 'L(ℓ) = clean line', 'γ = α + jβ ,  Zc'); box(15.1, 2.6, ORANGE, 'P̃', 'port 2 (mirror)')
for x in (3.1, 14.6): ax.annotate('', (x+.5, 2.0), (x, 2.0), arrowprops=dict(arrowstyle='-', lw=2))
ax.text(9.5, 3.25, 'Every CST run:   T_run(ℓ) = P · L(ℓ) · P̃', ha='center', fontsize=14, weight='bold', color=NAVY)
# lumped P inset
y0 = -0.75; ax.plot([0.4, 1.0], [y0, y0], 'k', lw=1.5)
xs = [1.0+i*0.15 for i in range(9)]
import numpy as np
t = np.linspace(0, 1, 200); ax.plot(1.0+1.2*t, y0+0.12*np.sin(2*np.pi*4*t), 'k', lw=1.5); ax.text(1.6, y0+0.25, 'L_s', ha='center', fontsize=11)
ax.plot([2.2, 3.2], [y0, y0], 'k', lw=1.5); ax.plot([2.8, 2.8], [y0, y0-0.18], 'k', lw=1.5)
ax.plot([2.6, 3.0], [y0-0.18, y0-0.18], 'k', lw=2); ax.plot([2.6, 3.0], [y0-0.3, y0-0.3], 'k', lw=2); ax.text(2.35, y0-0.3, 'C_p', fontsize=11, ha='right')
ax.text(4.0, y0-0.05, 'P = series L_s, then shunt C_p     (L_s ≈ 2.8 pH,  C_p ≈ 1.3 fF  ≈ 9.5 µm of extra line)', fontsize=11, va='center', color='#333')
sv(fig, 'port_model.png')

# --- de-embedding diagram
fig, ax = plt.subplots(figsize=(9.5, 2.8)); ax.axis('off'); ax.set_xlim(0, 19); ax.set_ylim(0, 3.4)
def seq(y, items):
    x = 0.3
    for lab, w, col in items:
        if col is None: ax.text(x+w/2, y, lab, ha='center', va='center', fontsize=15); x += w; continue
        ax.add_patch(Rectangle((x, y-.32), w, .64, fc=col, ec='k', lw=.6)); ax.text(x+w/2, y, lab, ha='center', va='center', fontsize=12, weight='bold', color='white'); x += w+0.08
seq(2.7, [('T_short⁻¹ · T_long  =', 4.2, None), ('P̃⁻¹', 1.0, ORANGE), ('L_s⁻¹', 1.1, BLUE), ('P⁻¹', 0.9, '#C0C0C0'), ('P', 0.9, '#C0C0C0'), ('L_l', 1.6, BLUE), ('P̃', 1.0, ORANGE)])
ax.annotate('cancel', (8.9, 2.25), (8.9, 1.85), ha='center', fontsize=11, color=GREY, arrowprops=dict(arrowstyle='-[', color=GREY))
seq(1.2, [('=', 4.2, None), ('P̃⁻¹', 1.0, ORANGE), ('L(Δℓ)', 2.6, BLUE), ('P̃', 1.0, ORANGE)])
ax.text(10.2, 1.2, '→  trace exact: cosh γΔℓ  (γ clean)\n→  √(B/C): residue of P̃, 2nd order (~10⁻⁴)', fontsize=12, va='center', color=NAVY)
sv(fig, 'deemb.png')
