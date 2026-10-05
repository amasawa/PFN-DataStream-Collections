#!/bin/bash
# Addendum to pre-registration E, step 2: the best configuration of the extended grid on the held-out and grid test
# streams (once), and one more enlargement of the feature map (4000 features) on the development streams.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=$HOME/pfn-venvs/stream/bin/python; M=mooe_rff2000_100_2_0.01; O=../results_trained; D=../results_trained_dev
DEV="elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced"
HELD="insects_incremental_abrupt_balanced covertype insects_gradual_imbalanced insects_abrupt_imbalanced"
G=""; for c in 5 30 100; do for b in 500 2000; do for s in 10 11; do G="$G grid_c${c}_b${b}_s$s"; done; done; done
(for s in $DEV; do echo "$s mooe_rff4000_100_2_0.01"; done | xargs -P 5 -L 1 sh -c "OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 $PY -u run_trained.py --streams \$0 --methods \$1 --out $D" >> $D/log_ext.txt 2>&1; echo EXT4000_DONE $(date +%T) >> $D/log_ext.txt) &
for s in $HELD $G; do echo $s; done | xargs -P 6 -I{} sh -c "$PY -u run_trained.py --streams {} --methods $M --out $O" >> $O/log.txt 2>&1
for s in $DEV; do cp $D/${s}__$M.npz $O/; done
echo MOOE_EXT_DONE $(date +%T) >> $O/log.txt
wait
