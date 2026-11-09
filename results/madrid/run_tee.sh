cd /home/user/claude/results/madrid
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python3 run_tee.py 3.2 0.12 0.0 10.0 0.5 1.4 tee_geo 2>&1 | grep RESULT >> sweep_tee.txt
grep -v " 0.5$" jobs_tee.txt | xargs -P4 -L1 sh -c 'python3 /home/user/claude/results/madrid/run_tee.py $0 $1 $2 $3 $4 1.4 2>&1 | grep RESULT || echo "FAIL $0 $1 $2 $3 $4"' >> sweep_tee.txt
