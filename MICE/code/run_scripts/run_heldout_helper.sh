#!/bin/bash
# Speeds up pre-registration C without changing any command: once the DriftTriage chain has released the GPU, this
# takes over the LAST held-out stream (same run.py call as run_heldout.sh, the long method first). The main chain is
# stopped right after it finishes the third stream, so the two never work on the same stream. Resumable.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
OUT=../results_heldout; S=insects_abrupt_imbalanced
until grep -q TEST2_DONE ../../DriftTriage/results/test2.log || ! tmux has-session -t dt_chain 2>/dev/null; do sleep 60; done
echo HELPER_START $(date +%T) >> $OUT/log.txt
(until grep -q "STREAM_DONE insects_gradual_imbalanced" $OUT/log.txt; do sleep 5; done
 tmux kill-session -t mice_heldout 2>/dev/null; echo MAIN_STOPPED $(date +%T) >> $OUT/log.txt) &
$PY -u run.py --streams $S --methods micev1000_500 winens1000 ddm1000 ltm1000_75 fifo1000 --out $OUT >> $OUT/log.txt 2>&1
wait
$PY -c "import reweight; reweight.freeze('$OUT', 'micev1000_500', 10, 0.0, 'mice')" >> $OUT/log.txt 2>&1
echo STREAM_DONE $S $(date +%T) >> $OUT/log.txt
echo HELDOUT_DONE $(date +%T) >> $OUT/log.txt
