#!/bin/bash
# Helpers for the family test of pre-registration B: the same command as run_real_test.sh on disjoint streams, so that
# the sequential main loop skips them (run.py skips existing outputs). Nothing else is changed.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python; OUT=../results_test
M="fifo1000 ltm1000_75 ddm1000 winens1000 oracle1000 micev1000_500"
(for fam in hyperplane rbf sine agrawal stagger sea; do $PY -u run.py --streams ${fam}_s14 --methods $M --out $OUT >> $OUT/log_fam_helper.txt 2>&1; done) &
(for fam in hyperplane rbf sine; do $PY -u run.py --streams ${fam}_s13 --methods $M --out $OUT >> $OUT/log_fam_helper.txt 2>&1; done) &
wait; echo HELPER_DONE $(date +%T) >> $OUT/log_fam_helper.txt
