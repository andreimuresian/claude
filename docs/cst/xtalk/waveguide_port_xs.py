import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
# schematic, not to scale vertically
ws,g,wg,pitch=35,4.15,49.85,200
def line(cx): # returns list of (x0,w,label)
    return [(cx-ws/2-g-wg,wg,"G"),(cx-ws/2,ws,"S"),(cx+ws/2+g,wg,"G")]
fig,axs=plt.subplots(2,1,figsize=(11,9))
for k,ax in enumerate(axs):
    half = k==1
    xl = 0 if half else -480; xr=480
    # layers (y in schematic units)
    ax.add_patch(Rectangle((-480,-60),960,40,fc="#c8c8c8",ec="none"))  # Si (compressed)
    ax.text(250,-42,"Si 525 µm (drawn compressed)",fontsize=8)
    ax.add_patch(Rectangle((-480,-20),960,14,fc="#cfe8ff",ec="none")); ax.text(250,-15,"SiO2 4.7 µm",fontsize=8)
    ax.add_patch(Rectangle((-480,-6),960,6,fc="#ffd9a8",ec="none")); ax.text(250,-5,"LiNbO3 film",fontsize=8)
    names={-pitch/2:"A",pitch/2:"B"}
    for cx in (-pitch/2,pitch/2):
        for x0,w,lab in line(cx):
            ax.add_patch(Rectangle((x0,0),w,4,fc="gold",ec="k",lw=.5))
            ax.text(x0+w/2,6,lab+"_"+names[cx],ha="center",fontsize=8)
    ax.text(-pitch/2,14,"line A (GSG)",ha="center",fontsize=9,weight="bold")
    ax.text(pitch/2,14,"line B (GSG)",ha="center",fontsize=9,weight="bold")
    # port frame
    ax.add_patch(Rectangle((xl,-75),xr-xl,135,fill=False,ec="red",lw=2,ls="-"))
    ax.text(xr-5,55,"waveguide port (one port, both lines)",color="red",ha="right",fontsize=9)
    ax.text(xr-5,-72,"bottom: below the whole Si",color="red",ha="right",fontsize=8)
    ax.annotate("",xy=(xr,30),xytext=(pitch/2+71.5,30),arrowprops=dict(arrowstyle="<->",color="red"))
    ax.text((xr+pitch/2+71.5)/2,32,"≥ ~300 µm",color="red",ha="center",fontsize=8)
    if half:
        ax.add_patch(Rectangle((-480,-80),480,145,fc="white",alpha=.75,ec="none"))
        ax.axvline(0,color="blue",lw=2.5)
        ax.text(-240,30,"NOT modelled\n(mirror image supplied by CST)",ha="center",color="gray",fontsize=10)
        ax.text(3,-95+10,"symmetry plane x = 0\n(magnetic wall → even modes; electric wall → odd modes)",color="blue",fontsize=8.5)
        ax.set_title("(b) Half model: one complete GSG line + half the 57 µm space between lines.\nPort edge lies ON the symmetry plane.")
    else:
        ax.axvline(0,color="blue",lw=1,ls=":")
        ax.set_title("(a) Full cross-section (recommended first run): one waveguide port covering both lines")
    ax.set_xlim(-500,500); ax.set_ylim(-100,70); ax.set_yticks([]); ax.set_xlabel("x (µm), horizontal to scale")
fig.tight_layout(); fig.savefig("/home/user/claude/docs/cst/xtalk/waveguide_port_xs.png",dpi=130)
