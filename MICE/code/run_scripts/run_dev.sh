#!/bin/bash
# Dev runs: 18 synthetic streams (seeds 0-2), all methods, M=1000, B=100. Two workers by seed parity. Resumable.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
M="fifo1000 ltm1000_65 ltm1000_75 ltm1000_85 oracle1000 mice1000"
w() { for s in "$@"; do for fam in sea stagger agrawal sine rbf hyperplane; do
  $PY -u run.py --streams ${fam}_s$s --methods $M --out ../results_dev >> ../results_dev/log_w$1.txt 2>&1; done; done; }
mkdir -p ../results_dev
w 0 2 &
w 1 &
wait
echo DEV_DONE $(date +%T) >> ../results_dev/progress.log
