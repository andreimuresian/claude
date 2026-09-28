"""Why does the 2.5 mm line, extrapolated to 14 mm, give a different EO bandwidth
than the 14 mm line?  (DESIGN_JEREZ_V1_suspe_siliconetch_275, CST TD.)

Run:  python compare_2p5_vs_14mm.py      -> prints the report, writes
      eo_bw_2p5_vs_14mm.png and eo_bw_2p5_vs_14mm.json next to this file.

Fixed choices (change here):  Rt = 55 ohm (load), Zs = 50 ohm (source),
n_g = 2.27 (thesis central value, 500-LHS range 2.24-2.29), device L = 14 mm.

The two CST runs are NOT identical apart from length.  From the file headers:
    2.5 mm : NCELL = 11, START_POSITION = 0.15 mm, w = 180 um
    14  mm : NCELL = 69, START_POSITION = 0.10 mm, w = 200 um
so the 2.5 mm line is 0.15 mm plain CPW + 2.2 mm loaded + 0.15 mm plain CPW
(12 % of its length unloaded), the 14 mm line is 1.4 % unloaded.
"""
import json
import os

import numpy as np
from scipy.optimize import minimize

from tline import (C0, abcd_to_s, bw3db, eo_db, eo_response, gamma_L,
                   read_s2p, s_to_abcd)

HERE = os.path.dirname(os.path.abspath(__file__))
RT, ZS, NG, LDEV = 55.0, 50.0, 2.27, 14e-3
L_S, L_L = 2.5e-3, 14e-3
END_S, LMID_S = 0.15e-3, 2.2e-3          # 2.5 mm line: unloaded ends, loaded core


def dbcm(g):                              # gamma [1/m] -> alpha [dB/cm]
    return 20 / np.log(10) * g.real / 100


def nm(f, g):
    return g.imag * C0 / (2 * np.pi * f)


# ---- ABCD helpers for de-embedding the unloaded end sections ---------------
def _line(g, z, L):
    return np.cosh(g * L), z * np.sinh(g * L), np.sinh(g * L) / z, np.cosh(g * L)


def _inv(X):
    A, B, C, D = X
    det = A * D - B * C
    return D / det, -B / det, -C / det, A / det


def _mul(X, Y):
    A1, B1, C1, D1 = X
    A2, B2, C2, D2 = Y
    return A1 * A2 + B1 * C2, A1 * B2 + B1 * D2, C1 * A2 + D1 * C2, C1 * B2 + D1 * D2


def _shunt(Y):
    o = np.ones_like(Y)
    return o, 0 * Y, Y, o


def _series(Z):
    o = np.ones_like(Z)
    return o, Z, 0 * Z, o


def deembed_ends(f, S, z0, p, alpha_u, end, lmid):
    """Strip an end box from both sides and return gamma [1/m], Zc of the core.
    End box, port side -> core:  plain CPW (n_u, Z_u, alpha_u [Np/m], length
    `end`), then a junction series L_j and shunt C_j.  p = (n_u, Z_u, C_j, L_j)."""
    n_u, z_u, c_j, l_j = p
    w = 2 * np.pi * f
    E = _mul(_line(alpha_u + 1j * w * n_u / C0, z_u + 0j, end),
             _mul(_series(1j * w * l_j), _shunt(1j * w * c_j)))
    E_out = (E[3], E[1], E[2], E[0])                  # mirrored box, output side
    core = _mul(_mul(_inv(E), s_to_abcd(S, z0)), _inv(E_out))
    gl, zc = gamma_L(abcd_to_s(*core, z0), z0)
    return gl / lmid, zc


END_MODELS = {'line': (0, 0), 'line+Cj': (1, 0), 'line+Lj': (0, 1), 'line+Cj+Lj': (1, 1)}


def fit_ends_from_short_line_only(f, S, z0, model='line'):
    """Choose the end-box parameters so the de-embedded core alpha(f), Zc(f)
    are smooth.  Uses ONLY the 2.5 mm file - nothing from the 14 mm line.
    Ends are assumed to lose like the core (self-consistent, 3 passes)."""
    use_c, use_l = END_MODELS[model]
    band = (f > 2e9) & (f < 79e9)
    au = np.zeros(len(f))
    unpack = lambda q: (q[0], q[1], q[2] * 1e-15 * use_c, q[3] * 1e-12 * use_l)

    def rough(q):
        g, z = deembed_ends(f, S, z0, unpack(q), au, END_S, LMID_S)
        return (np.sum(np.diff(dbcm(g)[band], 2) ** 2)
                + 1e-4 * np.sum(np.abs(np.diff(z[band], 2)) ** 2))

    starts = [[n0, z0_, c0, l0] for n0 in (1.9, 2.2) for z0_ in (50, 65)
              for c0 in ((0, 5, 20) if use_c else (0,))
              for l0 in ((0, 5, 20) if use_l else (0,))]
    for _ in range(3):
        best = min((minimize(rough, q0, method='Nelder-Mead',
                             options=dict(xatol=1e-5, fatol=1e-14, maxiter=8000))
                    for q0 in starts), key=lambda r: r.fun)
        p = unpack(best.x)
        g, z = deembed_ends(f, S, z0, p, au, END_S, LMID_S)
        k = np.polyfit(np.sqrt(f[band]), g.real[band], 1)
        au = np.polyval(k, np.sqrt(f)).clip(0)
    return p, k, g, z


def main():
    fs, Ss, z0 = read_s2p(os.path.join(HERE, 'data/JEREZ_V1_2p5mm.s2p'))
    fl, Sl, _ = read_s2p(os.path.join(HERE, 'data/JEREZ_V1_14mm.s2p'))
    fs, Ss, fl, Sl = fs[1:], Ss[1:], fl[1:], Sl[1:]    # drop DC (TD-extrapolated)

    gls, zs = gamma_L(Ss, z0)
    gll, zl = gamma_L(Sl, z0)
    g_s = gls / L_S
    # 14 mm quantities on the 2.5 mm grid (smooth, so interpolation is safe)
    g_l = (np.interp(fs, fl, gll.real) + 1j * np.interp(fs, fl, gll.imag)) / L_L
    z_l = np.interp(fs, fl, zl.real) + 1j * np.interp(fs, fl, zl.imag)

    def bw(g, z, f=fs):
        return bw3db(f, eo_db(eo_response(f, g, z, LDEV, NG, RT, ZS))) / 1e9

    res = {'settings': dict(Rt=RT, Zs=ZS, ng=NG, L_device_mm=LDEV * 1e3)}
    res['bw_GHz'] = {
        '2.5mm_extrapolated': bw(g_s, zs),
        '14mm': bw(gll / L_L, zl, fl),
    }
    # attribution: take alpha, beta, Zc from one line or the other
    att = {}
    for a in 'sl':
        for b in 'sl':
            for z in 'sl':
                g = ({'s': g_s, 'l': g_l}[a].real
                     + 1j * {'s': g_s, 'l': g_l}[b].imag)
                att[f'alpha={a},beta={b},Zc={z}'] = bw(g, {'s': zs, 'l': z_l}[z])
    res['attribution_GHz'] = att

    # half-wave resonances of the 2.5 mm line (beta L = k pi)
    n_mid = np.median(nm(fs, g_s)[(fs > 5e9)])
    res['halfwave_2p5mm_GHz'] = [k * C0 / (2 * n_mid * L_S) / 1e9 for k in (1, 2, 3)]

    # de-embed the ends: fit on the 2.5 mm file alone, apply the SAME end box
    # to the 14 mm line (its ends are 0.10 mm).  Four end models = sensitivity.
    sens = {}
    for model in END_MODELS:
        p, k, g_dm, z_dm = fit_ends_from_short_line_only(fs, Ss, z0, model)
        au_l = np.polyval(k, np.sqrt(fl)).clip(0)
        g_lm, z_lm = deembed_ends(fl, Sl, z0, p, au_l, 0.10e-3, 13.8e-3)
        row = dict(n_u=p[0], Z_u=p[1], C_j_fF=p[2] * 1e15, L_j_pH=p[3] * 1e12,
                   bw_2p5_deemb=bw(g_dm, z_dm), bw_14_deemb=bw(g_lm, z_lm, fl))
        for F in (20, 40, 60, 70):
            i, j = int(np.argmin(abs(fs - F * 1e9))), int(np.argmin(abs(fl - F * 1e9)))
            row[f'alpha{F}_2p5'] = dbcm(g_dm[i])
            row[f'alpha{F}_14'] = dbcm(g_lm[j])
        sens[model] = row
        if model == 'line':                 # physically plausible; used in the table/plot
            n_u, z_u, g_d, z_d = p[0], p[1], g_dm, z_dm
    res['end_model_sensitivity'] = sens
    res['ends_fit_from_2p5mm_only'] = dict(n_u=n_u, Z_u=z_u)
    res['bw_GHz']['2.5mm_deembedded_extrapolated'] = sens['line']['bw_2p5_deemb']
    # two-line estimate (length-independent error cancels, ends ~equal)
    g_2 = (g_l * L_L - gls) / (L_L - L_S)
    res['bw_GHz']['two_line(alpha,beta)+14mm_Zc'] = bw(g_2, z_l)

    band = (fs > 2e9) & (fs < 80e9)
    res['Zc_std_ohm'] = {'2.5mm': float(zs.real[band].std()),
                         '2.5mm_deembedded': float(z_d.real[band].std()),
                         '14mm': float(z_l.real[band].std())}
    tab = []
    for F in (10, 20, 30, 40, 50, 60, 70):
        i = int(np.argmin(abs(fs - F * 1e9)))
        tab.append(dict(f_GHz=F,
                        alpha_2p5=dbcm(g_s[i]), alpha_2p5_deemb=dbcm(g_d[i]),
                        alpha_14=dbcm(g_l[i]), alpha_twoline=dbcm(g_2[i]),
                        nm_2p5=nm(fs[i], g_s[i]), nm_2p5_deemb=nm(fs[i], g_d[i]),
                        nm_14=nm(fs[i], g_l[i]),
                        Zc_2p5=zs[i].real, Zc_2p5_deemb=z_d[i].real, Zc_14=z_l[i].real))
    res['table'] = tab

    # ---- report ------------------------------------------------------------
    print(f"Rt={RT} ohm  Zs={ZS} ohm  n_g={NG}  L={LDEV*1e3:.0f} mm")
    for k, v in res['bw_GHz'].items():
        print(f"  EO 3 dB BW  {k:32s} {v:6.2f} GHz" if np.isfinite(v)
              else f"  EO 3 dB BW  {k:32s}  > 80 GHz (no -3 dB crossing in band)")
    print("  2.5 mm half-wave resonances: "
          + ", ".join(f"{x:.1f}" for x in res['halfwave_2p5mm_GHz']) + " GHz")
    print(f"  ends fitted from 2.5 mm file alone: n_u={n_u:.3f}  Z_u={z_u:.1f} ohm")
    print("  Zc std 2-80 GHz: " + ", ".join(f"{k} {v:.1f}" for k, v in res['Zc_std_ohm'].items()))
    print("\n  f   | alpha dB/cm: 2.5  2.5de  14   2-line | n_m: 2.5   2.5de  14    | Zc: 2.5  2.5de  14")
    for r in tab:
        print(f"  {r['f_GHz']:3d} | {r['alpha_2p5']:10.2f} {r['alpha_2p5_deemb']:5.2f} {r['alpha_14']:5.2f} "
              f"{r['alpha_twoline']:5.2f} | {r['nm_2p5']:.3f} {r['nm_2p5_deemb']:.3f} {r['nm_14']:.3f} | "
              f"{r['Zc_2p5']:5.1f} {r['Zc_2p5_deemb']:5.1f} {r['Zc_14']:5.1f}")
    print("\n  end-model sensitivity (ends fitted on the 2.5 mm file only, same box applied to 14 mm):")
    print("    model        n_u   Z_u   Cj[fF]  Lj[pH] | alpha40 2.5/14 | alpha70 2.5/14 | BW 2.5de  14de")
    for m, r in res['end_model_sensitivity'].items():
        print(f"    {m:11s} {r['n_u']:5.2f} {r['Z_u']:5.1f} {r['C_j_fF']:7.1f} {r['L_j_pH']:7.1f} | "
              f"{r['alpha40_2p5']:5.2f} {r['alpha40_14']:5.2f}   | {r['alpha70_2p5']:5.2f} {r['alpha70_14']:5.2f}   | "
              f"{r['bw_2p5_deemb']:6.1f} {r['bw_14_deemb']:6.1f}")
    print("\n  attribution (which line each of alpha, beta, Zc comes from):")
    for k, v in att.items():
        print(f"    {k:22s} {v:6.2f} GHz")
    with open(os.path.join(HERE, 'eo_bw_2p5_vs_14mm.json'), 'w') as fh:
        json.dump(res, fh, indent=1, default=float)

    plot(fs, fl, g_s, zs, g_d, z_d, gll / L_L, zl, res)


def plot(fs, fl, g_s, zs, g_d, z_d, g14, z14, res):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    ink, ink2, grid, surf = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
    c14, c25, c25d = '#2a78d6', '#eb6834', '#1baf7a'   # categorical slots 1-3
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': ink2, 'axes.labelcolor': ink,
                         'xtick.color': ink2, 'ytick.color': ink2, 'text.color': ink,
                         'axes.facecolor': surf, 'figure.facecolor': surf})
    fig, ax = plt.subplots(2, 2, figsize=(11, 7.2), sharex=True)
    eo = lambda f, g, z: eo_db(eo_response(f, g, z, LDEV, NG, RT, ZS))
    b = res['bw_GHz']
    series = [
        (fl, g14, z14, c14, f"14 mm line  (BW {b['14mm']:.1f} GHz)"),
        (fs, g_s, zs, c25, f"2.5 mm line, extrapolated  (BW {b['2.5mm_extrapolated']:.1f} GHz)"),
        (fs, g_d, z_d, c25d, "2.5 mm line, ends de-embedded  (BW > 80 GHz)"),
    ]
    for f, g, z, c, lab in series:
        ax[0, 0].plot(f / 1e9, eo(f, g, z), color=c, lw=2, label=lab)
        ax[0, 1].plot(f / 1e9, z.real, color=c, lw=2)
        ax[1, 0].plot(f / 1e9, dbcm(g), color=c, lw=2)
        ax[1, 1].plot(f / 1e9, nm(f, g), color=c, lw=2)
    ax[0, 0].axhline(-3, color=ink2, lw=1, ls='--')
    ax[0, 0].set_ylim(-8, 3)
    ax[0, 1].set_ylim(20, 100)
    ax[1, 0].set_ylim(-1, 9)
    ax[1, 1].set_ylim(2.15, 2.40)
    titles = ['EO response at 14 mm (Rt 55 Ω, Zs 50 Ω, n_g 2.27) [dB]',
              'Re Zc from √(B/C) [Ω]', 'α per unit length [dB/cm]', 'n_m']
    for a, t in zip(ax.ravel(), titles):
        a.set_title(t, loc='left', fontsize=10, color=ink)
        a.grid(color=grid, lw=0.8)
        a.set_axisbelow(True)
        for s in ('top', 'right'):
            a.spines[s].set_visible(False)
        for x in res['halfwave_2p5mm_GHz']:
            a.axvline(x, color=ink2, lw=0.8, ls=':')
        a.set_xlim(0, 80)
    ax[0, 1].text(res['halfwave_2p5mm_GHz'][0] + 0.8, 92,
                  'dotted: half-wave resonances\nof the 2.5 mm line (βL = kπ)',
                  color=ink2, fontsize=8, va='top')
    for a in ax[1]:
        a.set_xlabel('frequency [GHz]')
    ax[0, 0].legend(loc='lower left', frameon=False, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'eo_bw_2p5_vs_14mm.png'), dpi=150)


if __name__ == '__main__':
    main()
