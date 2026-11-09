cd /home/user/claude/results/madrid/sweep2
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cat jobs.txt | xargs -P4 -L1 sh -c 'python3 /home/user/claude/results/madrid/sweep2/run_sw.py $0 $1 $2 $3 $4 $5 2>&1 | grep "^RESULT" || echo "FAIL $0 $1 $2 $3 $4 $5"' >> sweep.txt
echo ALLDONE >> sweep.txt
