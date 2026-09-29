"""Draw one dataset row exactly as the code builds it, for validation against
the CST Multilayer model.  Top view is to scale; the cross-section is a
schematic (layer thicknesses span 0.1 um to 550 um) with every value written.

Run:  python draw_geometry.py [row]      -> geometry_row<row>.png
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'mom'))
import mesh_generator as mg          # the geometry the solvers use
import stack_params as sp

INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
METAL, SLOT = '#eda100', '#fcfcfb'
C_LN, C_OX, C_SI, C_AIR = '#1baf7a', '#9ec5f0', '#c3c2b7', '#fcfcfb'


def main(row=118):
    d = pd.read_excel(os.path.join(HERE, '..', 'mom', 'data', 'EVALUATED_FULL_LHS_DATASET.xlsx'))
    r = d.loc[row]
    WS, GAP, MTX = r.WS, r.GAP, r.MTX
    L1, L2, W1, W2, ED = r.L1, r.L2, r.W1, r.W2, r.ETCH_DEPTH
    WG, P = 70.0, mg.PITCH * 1e6
    x_si, x_gi, x_go = WS / 2, WS / 2 + GAP, WS / 2 + GAP + WG
    slab = sp.TFLN * 1e6 - ED

    # geometry from the solver's own footprint (metres -> um)
    g = dict(WS=WS * 1e-6, GAP=GAP * 1e-6, WG=WG * 1e-6, L1=L1 * 1e-6, L2=L2 * 1e-6,
             W1=W1 * 1e-6, W2=W2 * 1e-6)
    fp = mg.footprint(g, 1, etched=True)

    plt.rcParams.update({'font.size': 8.5, 'text.color': INK, 'axes.edgecolor': INK2,
                         'xtick.color': INK2, 'ytick.color': INK2, 'figure.facecolor': SURF,
                         'axes.facecolor': SURF})
    fig = plt.figure(figsize=(13, 6.6))
    ax = fig.add_axes([0.04, 0.09, 0.50, 0.83])
    geoms = getattr(fp, 'geoms', [fp])
    for poly in geoms:
        xs, zs = poly.exterior.xy
        ax.fill([v * 1e6 for v in xs], [v * 1e6 for v in zs], color=METAL, lw=0)
        for hole in poly.interiors:
            hx, hz = hole.xy
            ax.fill([v * 1e6 for v in hx], [v * 1e6 for v in hz], color=SLOT, lw=0)
    ax.set_xlim(-x_go - 12, x_go + 12)
    ax.set_ylim(-8, P + 8)
    ax.set_aspect('equal')
    ax.set_xlabel('lateral position [µm]  (CST Y)')
    ax.set_ylabel('along the line [µm]  (CST X)')
    ax.set_title(f'Top view of one unit cell, dataset row {row} (to scale)', loc='left', fontsize=10)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.axhline(0, color=INK2, lw=0.6, ls=':'); ax.axhline(P, color=INK2, lw=0.6, ls=':')

    def dim(x0, y0, x1, y1, text, off=(0, 0), ha='center'):
        ax.annotate('', (x0, y0), (x1, y1), arrowprops=dict(arrowstyle='<->', color=INK, lw=0.8))
        ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], text, ha=ha, va='center',
                fontsize=8, color=INK, bbox=dict(fc=SURF, ec='none', pad=0.5))
    zc = P / 2
    dim(-x_si, 12, x_si, 12, f'WS = {WS:.2f}')
    dim(x_si, 30, x_gi, 30, f'GAP = {GAP:.2f}', off=(0, 6))
    dim(x_gi, 185, x_go, 185, f'WG = {WG:.0f} (fixed)')
    dim(x_gi, zc - L1 / 2 - 5, x_gi + W1, zc - L1 / 2 - 5, f'W1 = {W1:.2f}', off=(0, -5))
    dim(x_gi + W1, zc + L2 / 2 + 5, x_gi + W1 + W2, zc + L2 / 2 + 5, f'W2 = {W2:.2f}', off=(0, 5))
    dim(x_gi + W1 / 2, zc - L1 / 2, x_gi + W1 / 2, zc + L1 / 2, f'L1 = {L1:.2f}', off=(-1, 0), ha='right')
    dim(x_gi + W1 + W2 + 3, zc - L2 / 2, x_gi + W1 + W2 + 3, zc + L2 / 2, f'L2 = {L2:.2f}', off=(2, 0), ha='left')
    dim(-x_go - 6, 0, -x_go - 6, P, f'pitch\n{P:.0f}', off=(0, 30))
    ax.text(0, zc, 'signal', ha='center', va='center', color=INK, fontsize=9)
    ax.text(-x_go + WG / 2, 20, 'ground', ha='center', color=INK, fontsize=9)
    ax.text(x_gi + W1 + W2 / 2, zc, 'slot\n(vacuum)', ha='center', va='center', color=INK2, fontsize=8)

    # ---- cross-section schematic through the tee centre ------------------------
    bx = fig.add_axes([0.58, 0.09, 0.40, 0.83])
    bx.set_xlim(0, 10); bx.set_ylim(0, 10); bx.axis('off')
    bx.set_title(f'Cross-section at the tee centre (schematic, not to scale)', loc='left', fontsize=10)
    layers = [(C_AIR, 'air (vacuum) — open above', 7.4, 9.3),
              (C_LN, f'LiNbO₃ slab  {slab:.3f} µm = 0.460 − ETCH ({ED:.3f})\n'
                     'ε lateral 28 / vertical 43 / along line 43 (CST)', 5.9, 6.6),
              (C_OX, f'SiO₂ BOX  {sp.BOX_H*1e6:.1f} µm,  ε 3.9', 4.4, 5.9),
              (C_SI, f'Si handle  {sp.SI_H*1e6:.0f} µm,  ε 11.7,  σ 2.5e-4 S/m', 1.6, 4.4),
              (C_AIR, 'air (vacuum) — open below', 0.3, 1.6)]
    for col, lab, y0, y1 in layers:
        bx.add_patch(Rectangle((0.2, y0), 9.6, y1 - y0, fc=col, ec=INK2, lw=0.5))
        bx.text(5.0, (y0 + y1) / 2, lab, ha='center', va='center', fontsize=8, color=INK)
    # metal row on top of the LN slab: gnd | slot | gap | signal | gap | slot | gnd
    y0, y1 = 6.6, 7.4
    segs = [('gnd', 0.4, 1.6), ('slot', 1.6, 2.6), ('gap', 2.6, 3.4), ('sig', 3.4, 6.6),
            ('gap', 6.6, 7.4), ('slot', 7.4, 8.4), ('gnd', 8.4, 9.6)]
    for kind, a, b in segs:
        if kind in ('gnd', 'sig'):
            bx.add_patch(Rectangle((a, y0), b - a, y1 - y0, fc=METAL, ec=INK2, lw=0.5))
    bx.text(5.0, 7.0, f'signal  WS {WS:.2f}', ha='center', va='center', fontsize=8)
    bx.text(1.0, 7.0, 'gnd', ha='center', va='center', fontsize=8)
    bx.text(9.0, 7.0, 'gnd', ha='center', va='center', fontsize=8)
    bx.text(2.1, 7.0, 'slot', ha='center', va='center', fontsize=7.5, color=INK2)
    bx.text(7.9, 7.0, 'slot', ha='center', va='center', fontsize=7.5, color=INK2)
    bx.text(3.0, 7.55, f'GAP {GAP:.2f}', ha='center', va='bottom', fontsize=7.5)
    bx.text(9.8, 7.55, f'MTX {MTX:.3f} µm (gold, σ 4.561e7 S/m)', ha='right', va='bottom', fontsize=7.5)
    bx.text(0.2, 0.0, 'Not modelled (CST Multilayer has none of these): optical rib, SiO₂ cap (CAP_W),\n'
            'metal outside the two 70 µm grounds.  Cross-section drawn through the stem+head (z = pitch/2).',
            fontsize=7.5, color=INK2, va='bottom')
    out = os.path.join(HERE, f'geometry_row{row}.png')
    fig.savefig(out, dpi=150)
    print(out)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 118)
