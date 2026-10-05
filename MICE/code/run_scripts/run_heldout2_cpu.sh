#!/bin/bash
# Pre-registration G, CPU baselines: frozen MOOE configurations, Learn++.NSE and the river learners. Run once.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
PY=$HOME/pfn-venvs/stream/bin/python; O=../results_heldout2; mkdir -p $O
for s in h2_spam h2_phishing h2_weather h2_rialto h2_poker h2_airlines; do
  for m in mooe_rff2000_100_2_0.01 mooe_rff4000_100_2_0.01 nse arf srp hat levbag adwinbag; do echo "$s $m"; done; done | xargs -P 8 -L 1 sh -c \
  'case $1 in mooe*|nse) '"$PY"' -u run_trained.py --streams $0 --methods $1 --out '"$O"';; *) '"$PY"' -u run_river.py --streams $0 --methods $1 --out '"$O"';; esac' >> $O/log_cpu.txt 2>&1
echo CPU_DONE $(date +%T) >> $O/log_cpu.txt
