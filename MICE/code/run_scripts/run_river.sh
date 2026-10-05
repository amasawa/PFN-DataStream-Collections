#!/bin/bash
# river baselines (CPU) on the real streams and the grid test streams, same batch protocol as run.py. Resumable.
cd "$(dirname "$0")/.." || exit 1
PY=$HOME/pfn-venvs/stream/bin/python
mkdir -p ../results_river
for s in elec2 insects_gradual_balanced insects_abrupt_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced; do
  $PY -u run_river.py --streams $s --methods arf srp hat --out ../results_river >> ../results_river/log_$s.txt 2>&1 &
done
wait
G=""; for c in 5 30 100; do for b in 500 2000; do for s in 10 11; do G="$G grid_c${c}_b${b}_s$s"; done; done; done
echo $G | tr ' ' '\n' | xargs -P 6 -I{} sh -c "$PY -u run_river.py --streams {} --methods arf srp hat --out ../results_river >> ../results_river/log_grid.txt 2>&1"
echo DONE $(date +%T) >> ../results_river/log_grid.txt
