#!/bin/bash
# Pre-registrations I and J (see logs/EXPERIMENT_LOG.md, 2026-10-05). Run once; resumable; retries after a CUDA failure.
# Usage: run_heldout4.sh <tag> <out-dir-name> <backbone: tabpfn|tabicl> <wait-for-file-or-> "<methods>" stream [stream ...]
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
TAG=$1; OUT=../$2; export MICE_BACKBONE=$3; WAIT=$4; METHODS=$5; shift 5
mkdir -p $OUT
if [ "$WAIT" != "-" ]; then until [ "$(grep -c CHAIN_DONE $WAIT 2>/dev/null)" -ge 1 ]; do sleep 60; done; fi
for s in "$@"; do
  until $PY -u run.py --streams $s --methods $METHODS --out $OUT >> $OUT/log_$TAG.txt 2>&1; do
    echo RETRY $s $(date +%T) >> $OUT/log_$TAG.txt; sleep 60
  done
  echo STREAM_DONE $s $(date +%T) >> $OUT/log_$TAG.txt
done
echo CHAIN_DONE $(date +%T) >> $OUT/log_$TAG.txt
