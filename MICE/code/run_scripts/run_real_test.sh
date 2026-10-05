#!/bin/bash
# Pre-registered real-stream and family test (pre-registration B in logs/EXPERIMENT_LOG.md). Run once.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
OUT=../results_test; mkdir -p $OUT
w() { for s in "$@"; do $PY -u run.py --streams $s --methods fifo1000 ltm1000_75 ddm1000 winens1000 micev1000_500 --out $OUT >> $OUT/log_$1.txt 2>&1; done; }
w elec2 insects_abrupt_balanced insects_gradual_balanced &
w insects_incremental_reoccurring_balanced insects_incremental_balanced &
wait
for s in 10 11 12 13 14; do for fam in sea stagger agrawal sine rbf hyperplane; do
  $PY -u run.py --streams ${fam}_s$s --methods fifo1000 ltm1000_75 ddm1000 winens1000 oracle1000 micev1000_500 --out $OUT >> $OUT/log_fam.txt 2>&1
done; done
$PY -c "import reweight; reweight.freeze('$OUT', 'micev1000_500', 10, 0.0, 'mice')"
echo TEST_DONE $(date +%T) >> $OUT/log_fam.txt
