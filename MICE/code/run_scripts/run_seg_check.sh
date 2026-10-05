#!/bin/bash
# Dev check of segment length 500 on the family streams (seed 0 only), after dev pass 2. Resumable.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
until grep -q DEV2_DONE ../results_dev/progress.log 2>/dev/null; do sleep 30; done
for fam in sea stagger agrawal sine rbf hyperplane; do
  $HOME/pfn-venvs/venv/bin/python -u run.py --streams ${fam}_s0 --methods micev1000_500 --out ../results_dev >> ../results_dev/log_seg.txt 2>&1
done
echo SEG_DONE $(date +%T) >> ../results_dev/progress.log
