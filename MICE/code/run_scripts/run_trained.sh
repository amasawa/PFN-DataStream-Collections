#!/bin/bash
# Pre-registration E (see logs/EXPERIMENT_LOG.md, 2026-10-04 20:53): trained-expert baselines, CPU only. Resumable.
# 1) MOOE grid on the five development real streams; 2) select_mooe.py freezes one configuration (highest mean
# accuracy); 3) the frozen MOOE on the held-out real streams and the grid test streams, once. In parallel: Learn++.NSE
# and two more river ensembles with default settings on all 21 streams.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=$HOME/pfn-venvs/stream/bin/python
DEV="elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced"
HELD="insects_incremental_abrupt_balanced covertype insects_gradual_imbalanced insects_abrupt_imbalanced"
G=""; for c in 5 30 100; do for b in 500 2000; do for s in 10 11; do G="$G grid_c${c}_b${b}_s$s"; done; done; done
D=../results_trained_dev; O=../results_trained; mkdir -p $D $O
(for s in $DEV $HELD $G; do for m in nse levbag adwinbag; do echo "$s $m"; done; done | xargs -P 7 -L 1 sh -c \
  'if [ "$1" = nse ]; then '"$PY"' -u run_trained.py --streams $0 --methods nse --out '"$O"'; else '"$PY"' -u run_river.py --streams $0 --methods $1 --out '"$O"'; fi' >> $O/log_other.txt 2>&1
 echo OTHER_DONE $(date +%T) >> $O/log_other.txt) &
for f in lin rff; do for I in 50 100 500 1000; do for c in 0.1 0.3 1; do for g in 0.01 0.1 1; do for s in $DEV; do
  echo "$s mooe_${f}_${I}_${c}_${g}"; done; done; done; done; done | xargs -P 11 -L 1 sh -c "$PY -u run_trained.py --streams \$0 --methods \$1 --out $D" >> $D/log.txt 2>&1
echo GRID_DONE $(date +%T) >> $D/log.txt
M=$($PY select_mooe.py) || exit 1
echo "FROZEN $M" >> $O/log.txt
for s in $HELD $G; do echo $s; done | xargs -P 11 -I{} sh -c "$PY -u run_trained.py --streams {} --methods $M --out $O" >> $O/log.txt 2>&1
for s in $DEV; do cp $D/${s}__$M.npz $O/; done
echo MOOE_DONE $(date +%T) >> $O/log.txt
wait
echo TRAINED_DONE $(date +%T) >> $O/log.txt
