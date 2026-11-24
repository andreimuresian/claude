# Unattended: wait for the dataset, retry failures once, fit GP, optimise, GUI, figures, FEM validation, commit.
cd /home/user/claude/results/madrid/m1
until grep -q ALLDONE sweep_gp.txt; do sleep 20; done
if grep -q "^FAIL" sweep_gp.txt; then grep -v "^FAIL\|ALLDONE" sweep_gp.txt > s.tmp && mv s.tmp sweep_gp.txt; bash run_gp.sh; fi
grep -v "ALLDONE" sweep_gp.txt > s.tmp && mv s.tmp sweep_gp.txt
cd gp
python3 gp_build.py > gp_build.log 2>&1
python3 optimise.py 0.4 0.10 > optimise.log 2>&1
python3 make_gui.py >> optimise.log 2>&1
python3 figs_gp.py >> optimise.log 2>&1
cd /home/user/claude && git add -A results/madrid/m1 && git commit -qm "Madrid 1: dataset complete, GP surrogate, optimiser, offline predictor GUI

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EHQDy7yrZwCZyHELu6KFb3" && git push -q -u origin VPI-CODE
cd results/madrid/m1/gp && bash validate.sh
cd /home/user/claude && git add -A results/madrid/m1 && git commit -qm "Madrid 1: FEM validation of the surrogate optimum

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EHQDy7yrZwCZyHELu6KFb3" && git push -q -u origin VPI-CODE
echo PIPELINE_DONE
