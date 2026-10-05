#!/bin/bash
# Pre-registration N, CPU baselines on the third and fourth held-out sets: the frozen MOOE configurations,
# Learn++.NSE and the river learners, as in run_heldout2_cpu.sh. Run once; a finished cell is skipped by the runners.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
PY=$HOME/pfn-venvs/stream/bin/python; O=../results_heldout34_trained; mkdir -p $O
for s in h3_airlines_b h3_airlines_c h3_covertype_b h3_covertype_c h3_insects_b h3_insects_c h3_poker_b h3_poker_c \
         h4_airlines_d h4_airlines_e h4_covertype_d h4_covertype_e h4_poker_d h4_poker_e; do
  for m in mooe_rff2000_100_2_0.01 mooe_rff4000_100_2_0.01 nse arf srp hat levbag adwinbag; do echo "$s $m"; done; done | xargs -P 8 -L 1 sh -c \
  'case $1 in mooe*|nse) '"$PY"' -u run_trained.py --streams $0 --methods $1 --out '"$O"';; *) '"$PY"' -u run_river.py --streams $0 --methods $1 --out '"$O"';; esac' >> $O/log_cpu.txt 2>&1
echo CPU_DONE $(date +%T) >> $O/log_cpu.txt
