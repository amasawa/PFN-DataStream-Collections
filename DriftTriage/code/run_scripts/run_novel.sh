#!/bin/bash
# Pre-registration 3 (see logs/EXPERIMENT_LOG.md, 2026-10-04 21:32): withheld-class episodes on real streams, frozen
# triage_np against fifo, ddm and pxreset. Run once; resumable (stream_bench.py skips existing outputs).
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python; L=../results/novel.log
$PY -u stream_bench.py --families $($PY novel_episodes.py) --seeds 0 --policies fifo ddm pxreset triage_np --out ../results/stream_novel >> $L 2>&1
echo NOVEL_DONE $(date +%T) >> $L
