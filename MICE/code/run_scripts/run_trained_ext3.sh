#!/bin/bash
# Addendum to pre-registration E, step 3: the 4000-feature MOOE is 0.05 points better on the development streams than
# the 2000-feature one, so by the rule written in the log it is also run on the held-out and grid test streams (once).
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
PY=$HOME/pfn-venvs/stream/bin/python; M=mooe_rff4000_100_2_0.01; O=../results_trained; D=../results_trained_dev
HELD="insects_incremental_abrupt_balanced covertype insects_gradual_imbalanced insects_abrupt_imbalanced"
G=""; for c in 5 30 100; do for b in 500 2000; do for s in 10 11; do G="$G grid_c${c}_b${b}_s$s"; done; done; done
for s in $HELD $G; do echo $s; done | xargs -P 6 -I{} sh -c "$PY -u run_trained.py --streams {} --methods $M --out $O" >> $O/log.txt 2>&1
for s in elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced; do cp $D/${s}__$M.npz $O/; done
echo MOOE_EXT3_DONE $(date +%T) >> $O/log.txt
