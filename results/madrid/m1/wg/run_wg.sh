cd /home/user/claude/results/madrid/m1/wg
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
touch sweep_wg.txt sweep_wg_val.txt
python3 -c "
import json
d=set()
for f in ('sweep_wg.txt','sweep_wg_val.txt'):
  for l in open(f):
    if l.startswith('RESULT'):
      r=json.loads(l[7:]); d.add((round(r['wg'],4),round(r['gap'],4),round(r['buf'],4),round(r['cap_w'],4)))
for l in open('jobs_wg.txt'):
  a=l.split()
  if (round(float(a[0]),4),round(float(a[1]),4),round(float(a[2]),4),round(float(a[3]),4)) not in d: print(l.strip())" > jobs_wg_todo.txt
cat jobs_wg_todo.txt | xargs -P3 -L1 sh -c 'NG=$(python3 -c "print(round(1.872+0.052*($0-1.0),4))"); out=$(WG=$0 NGUESS=$NG python3 ../run_m1r.py $1 $2 $3 $4 $5 $6); if [ "$7" = val ]; then echo "$out" >> sweep_wg_val.txt; else echo "$out" >> sweep_wg.txt; fi'
echo ALLDONE >> sweep_wg.txt
