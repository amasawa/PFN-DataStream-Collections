#!/bin/bash
# Ablations of the context rule after the real-stream run (the real streams are development data from here on).
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
POL="triage_np triage_z triage_znp"
$PY -u stream_bench.py --families real:elec2 real:insects_gradual_balanced real:insects_abrupt_balanced --seeds 0 --policies $POL --out ../results/stream_real >> ../results/stream_real_ablate.log 2>&1 &
$PY -u stream_bench.py --families real:insects_incremental_balanced real:insects_incremental_reoccurring_balanced --seeds 0 --policies $POL --out ../results/stream_real >> ../results/stream_real_ablate.log 2>&1 &
wait
$PY -u stream_bench.py --seeds 0 1 2 3 4 --policies $POL --out ../results/stream_dev_v2 >> ../results/stream_real_ablate.log 2>&1
echo DONE $(date +%T) >> ../results/stream_real_ablate.log
