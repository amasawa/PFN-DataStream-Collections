#!/bin/bash
# Pre-registration C (see logs/EXPERIMENT_LOG.md, 2026-10-04 13:22): frozen mice and the TFM baselines on the held-out
# real streams. Run once; resumable. Waits for the family test (pre-registration B) so that it never shares the GPU
# with it.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python
OUT=../results_heldout; mkdir -p $OUT
until grep -q TEST_DONE ../results_test/log_fam.txt; do sleep 30; done
for s in insects_incremental_abrupt_balanced covertype insects_gradual_imbalanced insects_abrupt_imbalanced; do
  $PY -u run.py --streams $s --methods fifo1000 ltm1000_75 ddm1000 winens1000 micev1000_500 --out $OUT >> $OUT/log.txt 2>&1
  $PY -c "import reweight; reweight.freeze('$OUT', 'micev1000_500', 10, 0.0, 'mice')" >> $OUT/log.txt 2>&1
  echo STREAM_DONE $s $(date +%T) >> $OUT/log.txt
done
echo HELDOUT_DONE $(date +%T) >> $OUT/log.txt
