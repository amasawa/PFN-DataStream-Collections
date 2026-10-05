#!/bin/bash
# Pre-registration 2 (see logs/EXPERIMENT_LOG.md, 2026-10-04 13:22): frozen triage_np on fresh synthetic seeds 20-29,
# then on the held-out real streams. Run once; resumable (stream_bench.py skips existing outputs).
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
POL="fifo ltm ddm pxreset triage_np triage"
L=../results/test2.log
$PY -u stream_bench.py --seeds 20 21 22 23 24 25 26 27 28 29 --policies $POL --out ../results/stream_test2 >> $L 2>&1
echo SYN_DONE $(date +%T) >> $L
$PY -u stream_bench.py --families real:insects_incremental_abrupt_balanced real:covertype real:insects_gradual_imbalanced real:insects_abrupt_imbalanced --seeds 0 --policies $POL --out ../results/stream_heldout >> $L 2>&1
echo TEST2_DONE $(date +%T) >> $L
