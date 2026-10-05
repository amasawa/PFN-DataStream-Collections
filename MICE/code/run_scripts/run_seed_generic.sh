#!/bin/bash
# Seed replications (pre-registration K', see logs/EXPERIMENT_LOG.md, 2026-10-05). Run once; resumable; retries.
# Usage: run_seed_generic.sh <tag> <seed> <out-dir-name> "<methods>" stream [stream ...]
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
TAG=$1; export MICE_SEED=$2; OUT=../$3; METHODS=$4; shift 4
PY=$HOME/pfn-venvs/venv/bin/python; mkdir -p $OUT
for s in "$@"; do
  until $PY -u run_seed.py --streams $s --methods $METHODS --out $OUT >> $OUT/log_$TAG.txt 2>&1; do
    echo RETRY $s $(date +%T) >> $OUT/log_$TAG.txt; sleep 60
  done
  echo STREAM_DONE $s $(date +%T) >> $OUT/log_$TAG.txt
done
echo CHAIN_DONE $(date +%T) >> $OUT/log_$TAG.txt
