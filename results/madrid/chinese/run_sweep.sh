cd /home/user/claude/results/madrid/chinese
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
touch sweep.txt
python3 -c "
import json
d={(r['wl'],r['slab_w']) for r in (json.loads(l[7:]) for l in open('sweep.txt') if l.startswith('RESULT'))}
for l in open('jobs_sweep.txt'):
  a=l.split()
  if (float(a[0]),float(a[1])) not in d: print(l.strip())" > jobs_todo.txt
cat jobs_todo.txt | xargs -P3 -L1 sh -c 'python3 run_cn.py $0 $1 $2 2>&1 | grep "^RESULT" || echo "FAIL $0 $1 $2"' >> sweep.txt
echo ALLDONE >> sweep.txt
