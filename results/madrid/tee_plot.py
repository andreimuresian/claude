import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R=sorted([json.loads(l[7:]) for l in open("sweep_tee.txt") if l.startswith("RESULT")],key=lambda r:r["mtx_gnd"])
r10=[r for r in R if r["mtx_gnd"]==10][0]; R=[r for r in R if r["mtx_gnd"]<=2]
x=[r["mtx_gnd"] for r in R]
fig,(a1,a2)=plt.subplots(1,2,figsize=(12,4.4))
a1.plot(x,[r["VpiL_Vcm"] for r in R],"o-",color="#0E2268",label="signal 10 µm, ground swept")
a1.axhline(r10["VpiL_Vcm"],color="#0E2268",ls=":",label=f"signal 10 / ground 10 µm: {r10['VpiL_Vcm']:.3f}")
a1.axhline(1.8539,color="0.5",ls="--",label="design B, signal 2 / ground 2 µm: 1.854")
a2.plot(x,[r["IL_dBcm"] for r in R],"s-",color="#F20013",label="signal 10 µm, ground swept")
a2.axhline(0.2134,color="0.5",ls="--",label="design B (2 / 2 µm): 0.213")
a1.set_ylabel("Vπ·L (V·cm)"); a2.set_ylabel("IL (dB/cm)"); a2.set_ylim(0.2,0.23)
for a in (a1,a2): a.set_xlabel("ground electrode thickness (µm)"); a.grid(alpha=.3); a.legend(fontsize=8.5)
fig.suptitle("MADRID no ALD, λ = 1625 nm · gap 3.2 µm, buffer 120 nm, cap 3.0×0.5 µm · signal 10 µm, ground (tee tongue) 0.3–2.0 µm",fontsize=11)
fig.tight_layout(); fig.savefig("madrid_tee_ground_sweep.png",dpi=170)
