cd /home/user/claude/results/madrid
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cat jobs.txt | xargs -P4 -L1 sh -c 'python3 /home/user/claude/results/madrid/run_point.py $0 $1 $2 $3 1.4 2>&1 | grep RESULT || echo "FAIL $0 $1 $2 $3"' >> sweep.txt
