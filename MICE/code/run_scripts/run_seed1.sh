#!/bin/bash
# Pre-registration K (see logs/EXPERIMENT_LOG.md, 2026-10-05): the four b-segments of the third held-out set with
# backbone seed 1. Run once; resumable; retries after a CUDA failure.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4 MICE_SEED=1
PY=$HOME/pfn-venvs/venv/bin/python; OUT=../results_heldout3_seed1; mkdir -p $OUT
for s in h3_poker_b h3_insects_b h3_covertype_b h3_airlines_b; do
  until $PY -u run_seed.py --streams $s --methods fifo1000 ddm1000 winens1000 micev1000_500 --out $OUT >> $OUT/log_seed1.txt 2>&1; do
    echo RETRY $s $(date +%T) >> $OUT/log_seed1.txt; sleep 60
  done
  echo STREAM_DONE $s $(date +%T) >> $OUT/log_seed1.txt
done
echo CHAIN_DONE $(date +%T) >> $OUT/log_seed1.txt
