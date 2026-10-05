#!/bin/bash
# Recall-versus-relearn grid (dev seeds 0,1): fifo, ddm, winens, oracle, micev with segment 500. Resumable.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
mkdir -p ../results_grid_dev
for s in 0 1; do for nc in 5 30 100; do for b in 500 2000; do
  $PY -u run.py --streams grid_c${nc}_b${b}_s$s --methods fifo1000 ddm1000 winens1000 oracle1000 micev1000_500 \
      --out ../results_grid_dev >> ../results_grid_dev/log.txt 2>&1
done; done; done
echo GRID_DONE $(date +%T) >> ../results_grid_dev/log.txt
