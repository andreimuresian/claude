"""Jerez lifted, 1360 nm, WG_TOP 1.0 um: CAP_H sweep (0.3-1.9 um).  For each CAP_H:
unbuffered gap 4.2 reference, buffered (200 nm) at gaps 3.3-3.6 and 4.2.  Matching gap g*
(buffered Vpi*L = unbuffered reference), slope, buffer penalty, DC field in the rib."""
import re, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SP = "/tmp/claude-0/-home-user-claude/fd41e088-2b12-5532-ab62-ef0605547492/scratchpad/"
OUT = "/home/user/claude/results/jerez_gap/"
K = 20 * np.log10(np.e) * 2 * np.pi / 1.36e-6 / 100
BUF = 0.2
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

R = {}   # (cap, buffer, gap) -> dict
for l in open(SP + "j4_out.txt").readlines() + open(SP + "j3_out.txt").readlines():
    m = re.match(r"[SD]_c(\S+?)_b(\S+?)_g(\S+)\s+tri=\s*(\d+) neff=(\S+) Im=(\S+) .*VpiL=(\S+) Gamma=(\S+) Ex_core_mean=(\S+)", l)
    if m:
        R[(round(float(m[1]), 2), float(m[2]), float(m[3]))] = dict(VpiL=float(m[7]), IL=K * abs(float(m[6])),
                                                                     Gamma=float(m[8]), Ex=float(m[9]))
for l in open(SP + "j1_out.txt"):        # CAP 1.4 / 0.5 buffered 3.3-3.6 and refs from the gap sweep (WG_TOP 1.0)
    m = re.match(r"J([BN])_c(\S+)_w1\.0_g(\S+)\s+tri=.*Im=(\S+) IL=\S+ VpiL=(\S+)", l)
    if m:
        key = (round(float(m[2]), 2), BUF if m[1] == "B" else 0.0, float(m[3]))
        R.setdefault(key, dict(VpiL=float(m[5]), IL=K * abs(float(m[4]))))

caps = sorted({k[0] for k in R})
rows = []
for c in caps:
    try:
        ref = R[(c, 0.0, 4.2)]["VpiL"]
        gb = np.array([g for g in (3.3, 3.4, 3.5, 3.6, 4.2) if (c, BUF, g) in R])
        vb = np.array([R[(c, BUF, g)]["VpiL"] for g in gb])
    except KeyError:
        continue
    s, b = np.polyfit(gb, vb, 1)
    near = gb <= 3.61
    gstar = float(np.interp(ref, vb[near], gb[near])) if vb[near].min() <= ref <= vb[near].max() else float((ref - b) / s)
    P = R[(c, BUF, 4.2)]["VpiL"] - ref
    rows.append(dict(cap_h=c, ref_noBuf_g42=ref, buf_g42=R[(c, BUF, 4.2)]["VpiL"], buf_g34=R[(c, BUF, 3.4)]["VpiL"],
                     slope=s, penalty=P, gstar=gstar, lin_dev=float(np.max(np.abs(np.polyval([s, b], gb) - vb))),
                     Ex_noBuf_g42=R[(c, 0.0, 4.2)].get("Ex"), Ex_buf_g42=R[(c, BUF, 4.2)].get("Ex"),
                     IL_buf_at_gstar=float(np.exp(np.interp(gstar, gb[near], np.log([R[(c, BUF, g)]["IL"] for g in gb[near]]))))))
with open(OUT + "cap_sweep.csv", "w") as f:
    keys = list(rows[0])
    f.write(",".join(keys) + "\n")
    for r in rows:
        f.write(",".join("" if r[k] is None else f"{r[k]:.5f}" for k in keys) + "\n")
for r in rows:
    print(f"CAP {r['cap_h']:.2f}: ref {r['ref_noBuf_g42']:.4f}  buf4.2 {r['buf_g42']:.4f}  P {r['penalty']:.4f}  "
          f"s {r['slope']:.4f}  g* {r['gstar']:.3f}  lin dev {1e3*r['lin_dev']:.1f} mV*cm  IL(g*) {r['IL_buf_at_gstar']:.4f}")

c = np.array([r["cap_h"] for r in rows])
fig, ax = plt.subplots(2, 2, figsize=(12, 8))
a = ax[0, 0]
a.plot(c, [r["gstar"] for r in rows], "o-", color="#2a78d6", ms=6)
a.set_xlabel("CAP_H (µm, from the gold bottom)"); a.set_ylabel("matching gap g* (µm)")
a.set_title("Buffered gap with the same Vπ·L as unbuffered gap 4.2 µm")
a = ax[0, 1]
a.plot(c, [r["ref_noBuf_g42"] for r in rows], "D-", color="#7f8c8d", mfc="white", ms=6, label="no buffer, gap 4.2 µm (target)")
a.plot(c, [r["buf_g42"] for r in rows], "o-", color="#eb6834", ms=5, label="200 nm buffer, gap 4.2 µm")
a.plot(c, [r["buf_g34"] for r in rows], "o-", color="#2a78d6", ms=5, label="200 nm buffer, gap 3.4 µm")
a.set_xlabel("CAP_H (µm, from the gold bottom)"); a.set_ylabel("Vπ·L (V·cm)"); a.legend(fontsize=8.5)
a.set_title("Vπ·L vs cap height")
a = ax[1, 0]
a.plot(c, [r["slope"] for r in rows], "o-", color="#1baf7a", ms=5, label="slope s of the buffered curve (V·cm/µm)")
a.plot(c, [r["penalty"] for r in rows], "s-", color="#eb6834", ms=5, label="buffer penalty P at gap 4.2 (V·cm)")
a.set_xlabel("CAP_H (µm, from the gold bottom)"); a.legend(fontsize=8.5); a.set_title("g* = 4.2 − P / s")
a = ax[1, 1]
v_nb = np.array([r["ref_noBuf_g42"] for r in rows]); v_b = np.array([r["buf_g42"] for r in rows])
a.plot(c, v_nb / v_nb[-1], "D-", color="#7f8c8d", mfc="white", ms=6, label="no buffer, gap 4.2: cap top at CAP_H above the slab")
a.plot(c + BUF, v_b / v_b[-1], "o-", color="#eb6834", ms=5, label="buffer, gap 4.2: cap top at CAP_H + 0.2 µm above the slab")
a.set_xlabel("cap top height above the LN slab (µm)"); a.set_ylabel(f"Vπ·L / Vπ·L(CAP_H = {c[-1]:.1f})")
a.legend(fontsize=8.5); a.set_title("Cap effect vs absolute cap-top height")
for a in ax.flat:
    a.grid(alpha=0.3, lw=0.4)
fig.suptitle("Buffered Jerez lifted, 1360 nm, WG_TOP 1.0 µm: CAP_H sweep", fontsize=11)
plt.tight_layout(); fig.savefig(OUT + "jerez_cap_sweep.png", dpi=150); plt.close(fig)
