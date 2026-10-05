#!/bin/bash
# Development run of the delayed-label protocol on the five real streams already used (labels 10 batches late). Resumable per file.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python; OUT=../results_delay_dev; mkdir -p $OUT
$PY -u run_delay.py --delay 10 --streams insects_gradual_balanced insects_abrupt_balanced --out $OUT >> $OUT/log.txt 2>&1 &
$PY -u run_delay.py --delay 10 --streams elec2 insects_incremental_balanced --out $OUT >> $OUT/log.txt 2>&1 &
$PY -u run_delay.py --delay 10 --streams insects_incremental_reoccurring_balanced --out $OUT >> $OUT/log.txt 2>&1 &
wait; echo DONE $(date +%T) >> $OUT/log.txt
