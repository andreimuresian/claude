import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig,ax=plt.subplots(figsize=(14,8.5)); ax.set_xlim(0,140); ax.set_ylim(0,85); ax.axis("off")
def box(x,y,w,h,t,fc="#eef4ff",ec="k",fs=9,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.4",fc=fc,ec=ec,lw=1.4))
    ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs,weight="bold" if bold else None)
def wire(pts,c="k",ls="-",lw=1.3):
    xs,ys=zip(*pts); ax.plot(xs,ys,c=c,ls=ls,lw=lw)
def arrow(a,b,c="k",ls="-"):
    ax.annotate("",xy=b,xytext=a,arrowprops=dict(arrowstyle="->",color=c,ls=ls,lw=1.3))
RF="#1f5fbf"; OPT="#2e8b57"; MOD="#c0392b"
# ENA
box(4,70,18,10,"ENA\nout | in1 | in2",fc="#f3f3f3",bold=True)
# coupled electrode block
box(40,40,40,26,"",fc="#fff4e0",ec=MOD)
ax.text(60,63.5,"COUPLED ELECTRODE  (scripted, NEW)",ha="center",fontsize=10,weight="bold",color=MOD)
ax.text(60,56,"line A  ─────────────────────────\nline B  ─────────────────────────",ha="center",fontsize=9,family="monospace")
ax.text(60,46.5,"inside: 2-line model, modes from CST port solve\n(n_eff, Z per mode)  → exact 4-port S\n+ exact V_A(z), V_B(z) integrals",ha="center",fontsize=8)
# RF ports
for y,l in [(58,"A1"),(52,"B1")]: ax.text(38.5,y,l,ha="right",fontsize=9,color=RF,weight="bold")
for y,l in [(58,"A2"),(52,"B2")]: ax.text(81.5,y,l,ha="left",fontsize=9,color=RF,weight="bold")
wire([(13,70),(13,58),(39,58)],RF); ax.text(14,60,"drive A (aggressor)",fontsize=8,color=RF)
box(24,47,9,5,"50 Ω\n(or ENA in1:\nNEXT)",fc="#e8f0ff",fs=7); wire([(33,52),(39,52)],RF)
box(88,55.5,9,5,"50 Ω",fc="#e8f0ff",fs=8); wire([(82,58),(88,58)],RF)
box(88,48.5,9,5,"50 Ω\n(probe: FEXT)",fc="#e8f0ff",fs=7); wire([(82,52),(88,51)],RF)
# modulation outputs
ax.text(60,37,"modulation outputs (voltage the light sees, 4 of them)",ha="center",fontsize=8,color=MOD)
for x,l in [(45,"mod A arm1"),(53,"mod A arm2"),(67,"mod B arm1"),(75,"mod B arm2")]:
    arrow((x,40),(x,30),MOD); pass
# MZM A and B
def mzm(x0,y0,name):
    box(x0,y0,8,5,"CW laser",fc="#eaf7ee",fs=8)
    box(x0+11,y0,7,5,"split",fc="#eaf7ee",fs=8)
    box(x0+21,y0+5,8,5,"OM arm1",fc="#eaf7ee",fs=8)
    box(x0+21,y0-5,8,5,"OM arm2\n+π/2",fc="#eaf7ee",fs=7)
    box(x0+32,y0,7,5,"combine",fc="#eaf7ee",fs=7)
    box(x0+42,y0,6,5,"PD",fc="#eaf7ee",fs=8)
    for a,b in [((x0+8,y0+2.5),(x0+11,y0+2.5)),((x0+18,y0+3.5),(x0+21,y0+7.5)),((x0+18,y0+1.5),(x0+21,y0-2.5)),
                ((x0+29,y0+7.5),(x0+32,y0+3.5)),((x0+29,y0-2.5),(x0+32,y0+1.5)),((x0+39,y0+2.5),(x0+42,y0+2.5))]:
        arrow(a,b,OPT)
    ax.text(x0+24,y0-9.5,name,ha="center",fontsize=9,weight="bold",color=OPT)
mzm(2,16,"MZM A (aggressor, existing chain)")
mzm(66,16,"MZM B (victim, copy of the chain)")
for x,t in [(45,"→A arm1"),(53,"→A arm2"),(67,"→B arm1"),(75,"→B arm2")]:
    ax.text(x,29,t,ha="center",fontsize=6.5,color=MOD,rotation=0, bbox=dict(fc="white",ec="none",pad=0.5))
# PD to ENA
wire([(50,18.5),(36,18.5)],"gray","--") if False else None; ax.text(26,3.5,"PD A → ENA in1 (EO through A→A)",fontsize=7.5,color="gray",ha="center")
wire([(114,18.5),(120,18.5),(120,82),(17,82),(17,80.5)],"gray","--"); ax.text(100,83,"EO crosstalk (A drive → MZM B optical output) → ENA in2",fontsize=8,color="gray")
ax.text(80,-1,"Same schematic for both: electrical crosstalk = read B1/B2 RF ports;  EO crosstalk = read PD of MZM B.",ha="center",fontsize=10,weight="bold")
fig.savefig("/home/user/claude/docs/cst/xtalk/interconnect_xtalk_scheme.png",dpi=115,bbox_inches="tight")
