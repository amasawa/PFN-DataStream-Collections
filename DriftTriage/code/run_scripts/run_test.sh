#!/bin/bash
# Pre-registered DriftTriage test (see logs/EXPERIMENT_LOG.md). Run once.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
L=../results/test.log
$PY -u obs.py --seeds 10 11 12 13 14 >> $L 2>&1
$PY -u obs_out.py 10 11 12 13 14 >> $L 2>&1
$PY -u coverage_check.py 10 11 12 13 14 >> $L 2>&1
$PY -u stream_bench.py --seeds 10 11 12 13 14 15 16 17 18 19 --policies fifo ltm ddm pxreset triage --out ../results/stream_test >> $L 2>&1
echo TEST_DONE $(date +%T) >> $L
