#!/bin/bash
# Pre-registered grid test (seeds 10, 11). Run once. See logs/EXPERIMENT_LOG.md (pre-registration A).
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
for s in 10 11; do for nc in 5 30 100; do for b in 500 2000; do
  $PY -u run.py --streams grid_c${nc}_b${b}_s$s --methods fifo1000 ddm1000 winens1000 oracle1000 micev1000_500 \
      --out ../results_grid_test >> ../results_grid_test/log.txt 2>&1
done; done; done
$PY -c "import reweight; reweight.freeze('../results_grid_test', 'micev1000_500', 10, 0.0, 'mice')"
echo GRID_TEST_DONE $(date +%T) >> ../results_grid_test/log.txt
