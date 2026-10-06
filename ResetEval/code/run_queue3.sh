#!/bin/bash
# Work-queue chain over several queue files, in order (run_queue2.sh generalised). Queue lines:
#   "stream data_dir [seed [M [polset [kind]]]]"   defaults 0 1000 std tfm; kind = tfm (reset_eval.py) | ht | nb (trained_eval.py)
# A line is claimed with an atomic mkdir lock under ~/.reset_locks/<queue name>/<key>; a finished line gets a "done" file in
# its lock, so a lock without "done" whose chain was stopped (supervisor.sh releases it) is picked up again: the chain
# keeps passing over its queues until one pass claims nothing. The running key is written to ~/.reset_locks/run/<pid>.
# Usage: bash run_queue3.sh <log file> <queue file> [<queue file> ...]
cd "$(dirname "$0")"
LOG=$1; shift
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=2
mkdir -p ~/.reset_locks/run
while true; do
  claimed=0
  for Q in "$@"; do
    LOCK=$HOME/.reset_locks/$(basename "$Q" .txt); mkdir -p "$LOCK"   # Linux fs: mkdir on /mnt/c (drvfs) is not atomic
    while read -r s d seed m ps kind; do
      seed=${seed:-0}; m=${m:-1000}; ps=${ps:-std}; kind=${kind:-tfm}
      key=$s; [ "$seed" != 0 ] && key=${key}_s$seed; [ "$m" != 1000 ] && key=${key}_M$m
      [ "$ps" != std ] && key=${key}_$ps; [ "$kind" != tfm ] && key=${key}_$kind
      mkdir "$LOCK/$key" 2>/dev/null || continue
      claimed=1; echo "$LOCK/$key" > ~/.reset_locks/run/$$
      if [ "$kind" = tfm ]; then
        cmd="RESET_SEED=$seed RESET_M=$m RESET_POLSET=$ps RESET_DATA=$d nice ~/pfn-venvs/venv/bin/python -u reset_eval.py $s"
      else
        cmd="RESET_DATA=$d nice -n 19 ~/pfn-venvs/stream/bin/python -u trained_eval.py $kind $s"
      fi
      until eval "$cmd" >> "$LOG" 2>&1; do echo "RETRY $(date +%T) $key" >> "$LOG"; sleep 45; done
      touch "$LOCK/$key/done"; echo "STREAM_DONE $(date +%T) $key" >> "$LOG"
    done < "$Q"
  done
  [ $claimed = 0 ] && break
done
rm -f ~/.reset_locks/run/$$
echo "CHAIN_DONE $(date +%T)" >> "$LOG"
