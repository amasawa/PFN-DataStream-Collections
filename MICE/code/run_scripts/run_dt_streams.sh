#!/bin/bash
# MICE and its baselines on the typed-drift dev streams of DriftTriage (sine2d, lin; dev seeds 0-4). Resumable.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python; OUT=../results_dt_dev; mkdir -p $OUT
w() { for s in 0 1 2 3 4; do $PY -u run.py --streams dt_$1_s$s --methods fifo1000 ddm1000 micev1000_500 --out $OUT >> $OUT/log_$1.txt 2>&1; done; }
w sine2d & w lin & wait
$PY -c "import reweight; reweight.freeze('$OUT', 'micev1000_500', 10, 0.0, 'mice')"
echo DONE $(date +%T) >> $OUT/log_lin.txt
