# FEM validation of the surrogate optimum: top 5 designs, top-1 at buffer -40 nm, mesh check (MS 1.0) at top-1 and baseline.
cd /home/user/claude/results/madrid/m1/gp
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python3 - > val_jobs.txt <<'P'
import json; t = json.load(open("optimum_IL0.4_buf0.1.json"))["top"][:5]
for o in t: print("std", o["GAP"], o["BUFFER_H"], o["CAP_W"], o["CAP_H"], o["MTX_SMALL"])
o = t[0]; print("std", o["GAP"], round(o["BUFFER_H"] - 0.04, 4), o["CAP_W"], o["CAP_H"], o["MTX_SMALL"])
print("ms10", o["GAP"], o["BUFFER_H"], o["CAP_W"], o["CAP_H"], o["MTX_SMALL"]); print("ms10", 3.2, 0.1, 3.0, 0.5, 1.0)
P
cat val_jobs.txt | xargs -P4 -L1 sh -c 'if [ "$0" = ms10 ]; then MS=1.0 RIBPATCH=0 python3 ../run_m1.py $1 $2 $3 $4 $5 10.0 2>&1 | grep "^RESULT" | sed "s/^RESULT {/RESULT {\"mesh\": 1.0, /" || echo "FAIL ms10 $1 $2 $3 $4 $5"; else python3 ../run_m1r.py $1 $2 $3 $4 $5 10.0; fi' > validation.txt
echo ALLDONE >> validation.txt
