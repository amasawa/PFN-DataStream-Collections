#!/bin/bash
# DriftTriage dev streams: families sine2d, lin; seeds 0-4; all policies. Resumable. Usage: bash run_scripts/run_stream_dev.sh <out>
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
OUT=${1:-../results/stream_dev}
$HOME/pfn-venvs/venv/bin/python -u stream_bench.py --seeds 0 1 2 3 4 --out $OUT >> $OUT.log 2>&1
echo DONE $(date +%T) >> $OUT.log
