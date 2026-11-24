cd /home/user/claude/results/madrid/m1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 WL=1.525 NGUESS=1.916
python3 -c "
for i in range(21): print(3.2,0.05,3.0,0.5,1.0,round(9.0+0.1*i,2))" | xargs -P4 -L1 python3 run_m1r.py > sweep_sw1525.txt
echo ALLDONE >> sweep_sw1525.txt
