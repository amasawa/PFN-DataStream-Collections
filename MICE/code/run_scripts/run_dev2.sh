#!/bin/bash
# Dev pass 2 (after run_dev.sh): ddm, winens and micev (cached experts) on the 18 synthetic dev streams. Resumable.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
until grep -q DEV_DONE ../results_dev/progress.log 2>/dev/null; do sleep 30; done
w() { for s in "$@"; do for fam in sea stagger agrawal sine rbf hyperplane; do
  $PY -u run.py --streams ${fam}_s$s --methods ddm1000 winens1000 micev1000 --out ../results_dev >> ../results_dev/log2_w$1.txt 2>&1
done; done; }
w 0 2 &
w 1 &
wait
echo DEV2_DONE $(date +%T) >> ../results_dev/progress.log
