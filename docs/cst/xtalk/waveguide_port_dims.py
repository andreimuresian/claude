# Port dimensions sketch, drawn to scale (µm). Thin layers exaggerated slightly so they are visible.
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ws,g,wg,pitch=35,4.15,49.85,200
half_w=pitch/2+ws/2+g+wg            # outer ground edge, ~171.5
side,top,bot,si=300,300,100,525
fig,ax=plt.subplots(figsize=(9,9))
X0,X1=-half_w-side,half_w+side
ax.add_patch(Rectangle((X0,-si-10),X1-X0,si,fc="#c8c8c8"))            # Si
ax.add_patch(Rectangle((X0,-10),X1-X0,10,fc="#cfe8ff"))                # SiO2 + LN (exaggerated)
ax.text(X1-10,-6,"LiNbO3 + SiO2 (thin)",ha="right",va="center",fontsize=8)
ax.text(0,-si/2-10,"Si 525 µm\n(layers extend to the port edges)",ha="center",fontsize=10)
for cx in (-pitch/2,pitch/2):
    for x0,w in [(cx-ws/2-g-wg,wg),(cx-ws/2,ws),(cx+ws/2+g,wg)]:
        ax.add_patch(Rectangle((x0,0),w,8,fc="gold",ec="k",lw=.5))
ax.text(-pitch/2,15,"line A",ha="center"); ax.text(pitch/2,15,"line B",ha="center")
Y0,Y1=-si-10-bot,top
ax.add_patch(Rectangle((X0,Y0),X1-X0,Y1-Y0,fill=False,ec="red",lw=2.5))
def dim(x0,y0,x1,y1,t,**k):
    ax.annotate("",xy=(x1,y1),xytext=(x0,y0),arrowprops=dict(arrowstyle="<->",color="red"))
    ax.text((x0+x1)/2,(y0+y1)/2,t,color="red",fontsize=9,ha="center",va="center",
            bbox=dict(fc="white",ec="none",pad=1),**k)
dim(half_w,120,X1,120,"side 300 µm")
dim(-half_w,-120+250,-X1+0,130,"") if False else None
dim(X0+60,0,X0+60,Y1,"top\n300 µm")
dim(X0+60,-si-10,X0+60,Y0,"air 100 µm")
dim(X0,Y0-40,X1,Y0-40,f"total width ≈ {X1-X0:.0f} µm")
dim(X1+40,Y0,X1+40,Y1,f"total\n≈ {Y1-Y0:.0f} µm",rotation=0)
ax.text(0,Y0+20,"open air (background) under the Si",ha="center",fontsize=8)
ax.set_aspect("equal"); ax.set_xlim(X0-80,X1+140); ax.set_ylim(Y0-90,Y1+40)
ax.set_xlabel("x (µm)"); ax.set_ylabel("y (µm)")
ax.set_title("Waveguide port, full cross-section (to scale)\nmetal at y = 0; red box = port edge")
fig.tight_layout(); fig.savefig("/home/user/claude/docs/cst/xtalk/waveguide_port_dims.png",dpi=120)
