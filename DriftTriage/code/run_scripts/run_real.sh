#!/bin/bash
# Exploratory real-stream run (see logs/EXPERIMENT_LOG.md). Run once.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
$HOME/pfn-venvs/venv/bin/python -u stream_bench.py --families real:elec2 real:insects_abrupt_balanced real:insects_gradual_balanced real:insects_incremental_balanced real:insects_incremental_reoccurring_balanced --seeds 0 --policies fifo ltm ddm pxreset triage --out ../results/stream_real >> ../results/stream_real.log 2>&1
echo DONE $(date +%T) >> ../results/stream_real.log
