#!/bin/bash
# Guard of the dtmoe CPU lanes (AMENDMENT_BASELINES_20261018e.md item 1). Every 60 s; trips on: ~/pfn-runs/GPU_STOP
# (fecs_watch writes it on any nvlddmkm event), fecs_watch heartbeat older than 150 s, 1-minute load > 18 on two
# consecutive checks, or the running Drift-Resilient TabPFN stream slower by > 20% (median batch time of its last 25
# checkpointed batches vs the median of its earlier batches from batch 11 on, once >= 75 batches exist). A trip writes
# $D/STOP with the reason and kills every dtmoe process of $D (their partial outputs are quarantined by dtmoe_cpu.sh and
# not counted as deaths); dtmoe restarts only after the coordinator has logged the cause and removed STOP.
# Started by dtmoe_cpu.sh (one instance, flock); exits when no dtmoe_cpu.sh is running.
D=$HOME/pfn-runs/mice-table1-newbase/dtmoe_cpu; DR=$HOME/pfn-runs/mice-table1-newbase/drtabpfn
PY=$HOME/pfn-venvs/tsbase/bin/python; hi=0
exec 8> $D/guard.lock; flock -w 90 8 || exit 0   # one guard (waits for an exiting one); dtmoe_cpu.sh starts it on every invocation
trip() {
  echo "$(date '+%F %T') $*" > $D/STOP; echo "$(date '+%F %T') guard trip: $*" >> $D/progress.txt
  for i in 1 2 3 4 5 6; do   # repeated: a task that passed its STOP check just before the write may start late
    ps -eo pid,args | awk -v d="$D" '/[r]un_ts.py/ && index($0, "--out " d) {print $1}' | xargs -r kill; sleep 5
  done
  exit 0
}
sleep 10
while ps -eo args | grep -q "[d]tmoe_cpu.sh"; do
  [ -e $HOME/pfn-runs/GPU_STOP ] && trip "GPU_STOP present"
  [ $(( $(date +%s) - $(stat -c %Y $HOME/pfn-runs/fecs_watch.log.last 2>/dev/null || echo 0) )) -lt 150 ] || trip "fecs_watch not alive"
  l=$(cut -d' ' -f1 /proc/loadavg)
  if awk -v l=$l 'BEGIN {exit !(l > 18)}'; then hi=$((hi + 1)); [ $hi -ge 2 ] && trip "load $l > 18 twice"; else hi=0; fi
  ck=$(ls -t $DR/*.ckpt.npz 2>/dev/null | head -1)   # the running stream (finished streams keep no checkpoint)
  if [ -n "$ck" ]; then
    r=$($PY -c "
import numpy as np, sys
c = np.load(sys.argv[1]); t = int(c['t']); w = c['wt'][:t]
if t >= 75:
    a, b = np.median(w[t - 25:t]), np.median(w[11:t - 25])
    print('%.3f %.3f' % (a, b) if a > 1.2 * b else '')" $ck 2>/dev/null)
    [ -n "$r" ] && trip "DR batch time $r (recent vs earlier median) on $(basename $ck)"
  fi
  sleep 60
done
echo "$(date '+%F %T') guard exits (no dtmoe_cpu.sh running)" >> $D/progress.txt
