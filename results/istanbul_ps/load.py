import numpy as np, openpyxl
ws=openpyxl.load_workbook("TER_MTX.xlsx",data_only=True).active
W=np.array([ws.cell(r,1).value for r in range(3,7)],float)
FIELDS=[int(ws.cell(48,c).value.split("_")[-1]) for c in range(2,15)]
D={}
for wf,r0 in (("6IS0001",49),("6IS0002",56)):
    for j,f in enumerate(FIELDS): D[(wf,f)]=np.array([ws.cell(r0+i,2+j).value for i in range(4)],float)
# field map: column (0=left .. 2=right), row (0=top .. 4=bottom)
POS={f:(2 if f<5 else 1 if f<10 else 0, f%5) for f in range(15)}
