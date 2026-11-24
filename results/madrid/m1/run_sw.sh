cd /home/user/claude/results/madrid/m1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cat jobs_sw.txt | xargs -P3 -L1 sh -c 'python3 run_m1.py $0 $1 $2 $3 $4 $5 2>&1 | grep "^RESULT" || echo "FAIL $0 $1 $2 $3 $4 $5"' > sweep_sw.txt
echo ALLDONE >> sweep_sw.txt
