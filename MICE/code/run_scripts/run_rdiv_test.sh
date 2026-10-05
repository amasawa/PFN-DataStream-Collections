#!/bin/bash
# Pre-registration D: runs once, after the held-out chain has released the GPU (at most two GPU processes at a time).
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
until grep -q HELDOUT_DONE ../results_heldout/log.txt; do sleep 60; done
[ -f ../results_grid_test/rdiv_test.csv ] || $HOME/pfn-venvs/venv/bin/python -u check_rdiv_test.py > ../results_grid_test/rdiv_test.log 2>&1
echo RDIV_TEST_DONE $(date +%T) >> ../results_grid_test/rdiv_test.log
