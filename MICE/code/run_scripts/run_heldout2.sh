#!/bin/bash
# Pre-registration G (see logs/EXPERIMENT_LOG.md, 2026-10-04 23:58): frozen mice and the TFM baselines (TabPFN v2) on
# the second set of held-out real streams. Run once; resumable (micev has mid-stream checkpoints).
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
OUT=../results_heldout2; mkdir -p $OUT
for s in h2_spam h2_phishing h2_weather h2_rialto h2_poker h2_airlines; do
  # a CUDA launch failure kills the process (seen with four processes on the GPU): retry, finished cells are skipped
  until $PY -u run.py --streams $s --methods fifo1000 ltm1000_75 ddm1000 winens1000 micev1000_500 --out $OUT >> $OUT/log.txt 2>&1; do
    echo RETRY $s $(date +%T) >> $OUT/log.txt; sleep 60
  done
  $PY -c "import reweight; reweight.freeze('$OUT', 'micev1000_500', 10, 0.0, 'mice')" >> $OUT/log.txt 2>&1
  echo STREAM_DONE $s $(date +%T) >> $OUT/log.txt
done
echo HELDOUT2_DONE $(date +%T) >> $OUT/log.txt
