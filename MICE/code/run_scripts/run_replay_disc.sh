#!/bin/bash
# Label-free discrepancy for the cached experts of the real streams (development use of the real streams).
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
$PY -u replay_disc.py ../results_test insects_gradual_balanced elec2 insects_abrupt_balanced >> ../results_test/log_disc.txt 2>&1 &
$PY -u replay_disc.py ../results_test insects_incremental_balanced insects_incremental_reoccurring_balanced >> ../results_test/log_disc.txt 2>&1 &
wait; echo DONE $(date +%T) >> ../results_test/log_disc.txt
