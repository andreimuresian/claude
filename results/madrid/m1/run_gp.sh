cd /home/user/claude/results/madrid/m1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
touch sweep_gp.txt
python3 -c "
import json
d={(r['gap'],r['buf'],r['cap_w'],r['cap_h'],r['mtx_small']) for r in (json.loads(l[7:]) for l in open('sweep_gp.txt') if l.startswith('RESULT'))}
for l in open('jobs_gp.txt'):
  k=tuple(map(float,l.split()[:5]))
  if k not in d: print(l.strip())" > jobs_gp_todo.txt
cat jobs_gp_todo.txt | xargs -P4 -L1 python3 run_m1r.py >> sweep_gp.txt
echo ALLDONE >> sweep_gp.txt
