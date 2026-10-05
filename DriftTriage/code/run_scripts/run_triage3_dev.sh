#!/bin/bash
# triage3 on the dev streams, after the v2 run has finished (same output folder, separate files). Resumable.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
until grep -q DONE ../results/stream_dev_v2.log; do sleep 30; done
$HOME/pfn-venvs/venv/bin/python -u stream_bench.py --seeds 0 1 2 3 4 --policies triage3 --out ../results/stream_dev_v2 >> ../results/stream_dev_v2_t3.log 2>&1
echo DONE $(date +%T) >> ../results/stream_dev_v2_t3.log
