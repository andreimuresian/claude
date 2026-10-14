"""Coupled pendulums: the time-domain picture of the two pair modes."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
w0, kap = 2*np.pi, 0.05                     # pendulum frequency, weak spring
we, wo = w0, w0*np.sqrt(1 + 2*kap)          # together: spring idle; opposite: spring stretched
t = np.linspace(0, 40, 6000)
x1 = 0.5*(np.cos(we*t) + np.cos(wo*t)); x2 = 0.5*(np.cos(we*t) - np.cos(wo*t))
fig = plt.figure(figsize=(13, 7.6))
# sketches of the two modes
for k, (title, s2, col) in enumerate((("mode 1: swing TOGETHER\n(spring never stretched → slower)", 1, "#2e7d32"),
                                      ("mode 2: swing OPPOSITE\n(spring stretched → faster)", -1, "#7b1fa2"))):
    ax = fig.add_axes([0.05 + k*0.25, 0.58, 0.2, 0.36]); ax.axis("off"); ax.set_xlim(-1.6, 1.6); ax.set_ylim(-2.3, 0.4)
    ax.plot([-1.5, 1.5], [0, 0], "k", lw=3)
    for xa, sgn in ((-0.6, 1), (0.6, s2)):
        bx, by = xa + 0.45*sgn, -1.8
        ax.plot([xa, bx], [0, by], "k", lw=1.5); ax.add_patch(plt.Circle((bx, by), 0.17, color=col))
        ax.annotate("", xy=(bx + 0.35*sgn, by), xytext=(bx, by), arrowprops=dict(arrowstyle="->", color=col, lw=2))
    xs = np.linspace(-0.6 + 0.45*0.55, 0.6 + 0.45*s2*0.55, 60)
    ax.plot(xs, -1.0 + 0.05*np.sin(np.linspace(0, 14*np.pi, 60)), color="#888", lw=1.3)
    ax.set_title(title, fontsize=10.5, color=col)
axt = fig.add_axes([0.56, 0.6, 0.42, 0.32]); axt.axis("off")
axt.text(0, 0.9, "Push ONLY the left pendulum:", fontsize=12, weight="bold")
axt.text(0, 0.05, "= ½ × mode 1  +  ½ × mode 2\n\nThe two modes tick at slightly different rates.\n"
         "They slowly drift out of step, so the motion moves\nfrom the left pendulum to the right one and back.\n"
         "Nobody pushed the right pendulum: it moves because\nit is part of both modes.", fontsize=11)
ax = fig.add_axes([0.07, 0.08, 0.88, 0.40])
ax.plot(t, x1 + 1.3, color="#1565c0", lw=0.8, label="left pendulum (pushed)")
ax.plot(t, x2 - 1.3, color="#c62828", lw=0.8, label="right pendulum (never pushed)")
ax.plot(t, 1.3 + abs(np.cos((wo - we)*t/2)), "k--", lw=1); ax.plot(t, -1.3 + abs(np.sin((wo - we)*t/2)), "k--", lw=1)
ax.set_yticks([]); ax.set_xlabel("time"); ax.legend(loc="upper right", fontsize=10)
ax.set_title("Energy goes back and forth. Swap 'time' for 'position along the line': that is crosstalk.", fontsize=11.5)
plt.savefig("pendulums.png", dpi=130)
