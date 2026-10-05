#!/bin/bash
# Development run of the locally referenced error policy (see logs/EXPERIMENT_LOG.md, 2026-10-05). Resumable; retries
# after a CUDA failure. Usage: run_lref_dev.sh <tag> <out-subdir> <seeds> <policies> -- family [family ...]
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
TAG=$1; OUT=../results/$2; SEEDS=$3; POL=$4; shift 5
LOG=../results/lref_dev_$TAG.log; mkdir -p $OUT
for f in "$@"; do
  until $PY -u stream_bench.py --families $f --seeds $SEEDS --policies $POL --out $OUT >> $LOG 2>&1; do
    echo RETRY $f $(date +%T) >> $LOG; sleep 60
  done
done
echo CHAIN_DONE $(date +%T) >> $LOG
