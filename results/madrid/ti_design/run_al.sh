cd /home/user/claude/results/madrid/ti_design
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 N_TI=1.55+16j
cat jobs_al.txt | xargs -P4 -L1 sh -c 'python3 run_ti.py $0 $1 $2 2>&1 | grep "^RESULT" || echo "FAIL $0 $1 $2"' > sweep_al.txt
echo ALLDONE >> sweep_al.txt
