#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
$HOME/pfn-venvs/venv/bin/python -u stream_bench.py --seeds 0 1 2 3 4 --policies triage4 ddmr --out ../results/stream_dev_v2 >> ../results/stream_dev_v2_t4.log 2>&1
echo DONE $(date +%T) >> ../results/stream_dev_v2_t4.log
