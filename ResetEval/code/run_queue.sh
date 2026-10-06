#!/bin/bash
# Work-queue chain: claims streams from a queue file (one "stream data_dir" per line) with an atomic mkdir lock, runs
# reset_eval.py on each (resumes per policy; retries on failure), so any number of chains can share one queue.
# Usage: bash run_queue.sh <queue file> <log file>   (env: RESET_BACKBONE etc. are passed through)
cd "$(dirname "$0")"
Q=$1; LOG=$2; LOCK=$HOME/.reset_locks/$(basename "$Q" .txt); mkdir -p "$LOCK"   # Linux fs: mkdir on /mnt/c (drvfs) is not atomic
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=2
while read -r s d; do
  mkdir "$LOCK/$s" 2>/dev/null || continue
  until RESET_DATA=$d nice ~/pfn-venvs/venv/bin/python -u reset_eval.py "$s" >> "$LOG" 2>&1; do echo "RETRY $(date +%T) $s" >> "$LOG"; sleep 45; done
  echo "STREAM_DONE $(date +%T) $s" >> "$LOG"
done < "$Q"
echo "CHAIN_DONE $(date +%T)" >> "$LOG"
