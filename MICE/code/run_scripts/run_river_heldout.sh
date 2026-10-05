#!/bin/bash
# river baselines (CPU) on the held-out real streams of pre-registration C, same protocol as run.py. Resumable.
cd "$(dirname "$0")/.." || exit 1
PY=$HOME/pfn-venvs/stream/bin/python
OUT=../results_heldout; mkdir -p $OUT
for s in insects_incremental_abrupt_balanced covertype insects_gradual_imbalanced insects_abrupt_imbalanced; do
  $PY -u run_river.py --streams $s --methods arf srp hat --out $OUT >> $OUT/log_river_$s.txt 2>&1 &
done
wait; echo RIVER_DONE $(date +%T) >> $OUT/log_river.txt
