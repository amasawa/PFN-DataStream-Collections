#!/bin/bash
# Synthetic confirmation of mice3 (see logs/EXPERIMENT_LOG.md, 2026-10-05 03:55): fresh grid seeds 20, 21. Starts after
# the three chains of pre-registration H, so that at most three processes share the GPU. Run once; resumable.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python; OUT=../results_grid_test3; mkdir -p $OUT
until [ "$(cat ../results_heldout3/log_*.txt 2>/dev/null | grep -c CHAIN_DONE)" = 3 ]; do sleep 120; done
for s in 20 21; do for c in 5 30 100; do for b in 500 2000; do
  until $PY -u run.py --streams grid_c${c}_b${b}_s$s --methods fifo1000 ddm1000 winens1000 micev1000_500 --out $OUT >> $OUT/log.txt 2>&1; do
    echo RETRY $(date +%T) >> $OUT/log.txt; sleep 60; done
done; done; done
echo GRID3_DONE $(date +%T) >> $OUT/log.txt
