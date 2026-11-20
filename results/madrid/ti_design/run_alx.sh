cd /home/user/claude/results/madrid/ti_design
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 N_TI=1.55+16j
python3 -c "print('\n'.join(f'{0.1+0.05*i:.2f}' for i in range(29)))" | xargs -P4 -I{} sh -c 'TI_X={} python3 run_ti.py 4.0 0.1 0.5 2>&1 | grep "^RESULT" || echo "FAIL {}"' > sweep_alx.txt
echo ALLDONE >> sweep_alx.txt
