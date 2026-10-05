#!/bin/bash
# Development run after pre-registration 3: coverage in embedding space (triage_emb) on the withheld-class episodes of
# the four development INSECTS streams (the *_balanced variants used as development data since 2026-10-04 08:41).
# triage_np is re-run into the same folder so that its raw coverage and uncertainty are stored as well.
cd "$(dirname "$0")/.." || exit 1
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=4
PY=$HOME/pfn-venvs/venv/bin/python; L=../results/emb_dev.log
# the embedding calls fail with a CUDA launch failure while four processes share the GPU: wait for the TabICL chains
until [ "$(cat ../../MICE/results_heldout_tabicl/log_*.txt | grep -c CHAIN_DONE)" = 2 ]; do sleep 120; done
E=$($PY novel_episodes.py | grep -E "insects_(abrupt|gradual|incremental|incremental_reoccurring)_balanced:")
for i in 1 2 3 4 5 6; do  # the first run died with a CUDA "unspecified launch failure" under GPU contention; resumable, so retry
  $PY -u stream_bench.py --families $E --seeds 0 --policies triage_emb triage_np --out ../results/stream_novel_dev >> $L 2>&1 && break
  echo RETRY $i $(date +%T) >> $L; sleep 20
done
echo EMB_DEV_DONE $(date +%T) >> $L
