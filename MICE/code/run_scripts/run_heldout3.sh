#!/bin/bash
# Pre-registration H (see logs/EXPERIMENT_LOG.md, 2026-10-05 03:50): the two-timescale MICE (mice2) and the TFM
# baselines (TabPFN v2) on later, never-loaded segments of four real streams. Run once; resumable; retries after a
# CUDA failure. Usage: run_heldout3.sh <tag> stream [stream ...]
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
OUT=../results_heldout3; mkdir -p $OUT; TAG=$1; shift
for s in "$@"; do
  until $PY -u run.py --streams $s --methods fifo1000 ltm1000_75 ddm1000 winens1000 micev1000_500 --out $OUT >> $OUT/log_$TAG.txt 2>&1; do
    echo RETRY $s $(date +%T) >> $OUT/log_$TAG.txt; sleep 60
  done
  echo STREAM_DONE $s $(date +%T) >> $OUT/log_$TAG.txt
done
echo CHAIN_DONE $(date +%T) >> $OUT/log_$TAG.txt
