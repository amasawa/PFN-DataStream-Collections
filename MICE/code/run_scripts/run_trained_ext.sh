#!/bin/bash
# Addendum to pre-registration E: the frozen MOOE configuration lies on the border of the grid (largest step, smallest
# gamma), so the grid is extended on the development streams; if a better configuration exists it is ALSO run on the
# held-out and grid test streams, and both are reported.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=$HOME/pfn-venvs/stream/bin/python
DEV="elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced"
D=../results_trained_dev
for f in rff rff2000; do for I in 50 100; do for c in 1 2; do for g in 0.001 0.01; do for s in $DEV; do
  echo "$s mooe_${f}_${I}_${c}_${g}"; done; done; done; done; done | xargs -P 10 -L 1 sh -c "$PY -u run_trained.py --streams \$0 --methods \$1 --out $D" >> $D/log_ext.txt 2>&1
echo EXT_DONE $(date +%T) >> $D/log_ext.txt
