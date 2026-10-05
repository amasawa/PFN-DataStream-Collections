#!/bin/bash
# Reruns of ddm and ltm that store per-row probabilities (see logs/EXPERIMENT_LOG.md, 2026-10-05). Resumable; retries.
# Usage: run_probs.sh <tag> <wait-file-or-> stream [stream ...]    (waits until <wait-file> contains CHAIN_DONE)
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python; OUT=../results_probs; mkdir -p $OUT; TAG=$1; WAIT=$2; shift 2
if [ "$WAIT" != "-" ]; then until [ "$(grep -c CHAIN_DONE $WAIT 2>/dev/null)" -ge 1 ]; do sleep 60; done; fi
for s in "$@"; do
  until $PY -u run_probs.py --streams $s --methods ddm1000 ltm1000_75 --out $OUT >> $OUT/log_$TAG.txt 2>&1; do
    echo RETRY $s $(date +%T) >> $OUT/log_$TAG.txt; sleep 60
  done
done
echo CHAIN_DONE $(date +%T) >> $OUT/log_$TAG.txt
