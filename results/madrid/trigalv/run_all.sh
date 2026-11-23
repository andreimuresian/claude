cd /home/user/claude/results/madrid/trigalv
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
touch sweep.txt
python3 -c "
import json
d={(r['g_al'],r['buf'],r['tox'],r['p']) for r in (json.loads(l[7:]) for l in open('sweep.txt') if l.startswith('RESULT'))}
for l in open('jobs.txt'):
  k=tuple(map(float,l.split()))
  if k not in d: print(l.strip())" > jobs_todo.txt
cat jobs_todo.txt | xargs -P3 -L1 sh -c 'python3 run_tg.py $0 $1 $2 $3 2>&1 | grep "^RESULT" || echo "FAIL $0 $1 $2 $3"' >> sweep.txt
echo ALLDONE >> sweep.txt
