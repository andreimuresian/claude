cd /home/user/claude/results/madrid/trigalv
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 FULL_SKIN=1
cat jobs_fs.txt | xargs -P3 -L1 sh -c 'python3 run_tg.py $0 $1 $2 $3 2>&1 | grep "^RESULT" || echo "FAIL $0 $1 $2 $3"' > sweep_fs.txt
echo ALLDONE >> sweep_fs.txt
