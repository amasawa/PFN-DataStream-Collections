#!/bin/bash
# Pre-registration F (see logs/EXPERIMENT_LOG.md, 2026-10-04 21:11): frozen mice and the context baselines with a second
# backbone (TabICL, 4 estimators) on the four real streams of pre-registration C. Run once; resumable (micev has
# mid-stream checkpoints). Usage: run_heldout_tabicl.sh <tag> stream [stream ...]
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4 MICE_BACKBONE=tabicl
PY=$HOME/pfn-venvs/venv/bin/python
OUT=../results_heldout_tabicl; mkdir -p $OUT; TAG=$1; shift
for s in "$@"; do
  $PY -u run.py --streams $s --methods fifo1000 ddm1000 winens1000 micev1000_500 --out $OUT >> $OUT/log_$TAG.txt 2>&1
  $PY -c "import reweight; reweight.freeze('$OUT', 'micev1000_500', 10, 0.0, 'mice')" >> $OUT/log_$TAG.txt 2>&1
  echo STREAM_DONE $s $(date +%T) >> $OUT/log_$TAG.txt
done
echo CHAIN_DONE $(date +%T) >> $OUT/log_$TAG.txt
