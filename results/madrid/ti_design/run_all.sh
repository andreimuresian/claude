cd /home/user/claude/results/madrid/ti_design
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
touch sweep.txt
python3 -c "
import json
d={(r['gti'],r['ti_h'],r['ti_p']) for r in (json.loads(l[7:]) for l in open('sweep.txt') if l.startswith('RESULT'))}
for l in open('jobs.txt'):
  a,b,c=map(float,l.split())
  if (a,b,c) not in d: print(l.strip())" > jobs_todo.txt
cat jobs_todo.txt | xargs -P4 -L1 sh -c 'python3 run_ti.py $0 $1 $2 2>&1 | grep "^RESULT" || echo "FAIL $0 $1 $2"' >> sweep.txt
echo ALLDONE >> sweep.txt
