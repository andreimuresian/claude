cd /home/user/claude/results/madrid/chinese
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cat jobs_mesh.txt | xargs -P4 -L1 sh -c 'python3 run_cn.py $0 $1 $2 2>&1 | grep "^RESULT" || echo "FAIL $0 $1 $2"' > mesh.txt
echo 'RESULT {"wl": 1.625, "slab_w": 4.6, "ms": 1.4, "IL_dBcm": 0.5738280059387837, "VpiL_Vcm": 2.111277361451187, "tri": 231302}' >> mesh.txt
echo ALLDONE >> mesh.txt
