cd /home/user/claude/results/madrid/m1/gemini
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cat jobs.txt | xargs -P4 -I{} sh -c 'L="{}"; TAG=${L%% *}; ENVS=$(echo "$L" | sed "s/^[^ ]* //; s/ -- .*//"); ARGS=${L#* -- }; out=$(env $ENVS python3 ../run_m1r.py $ARGS); echo "$TAG $out"' > results.txt
echo ALLDONE >> results.txt
