#!/bin/bash
# P3 step 3 (HANDOFF P3 order, AMENDMENT_20261020d): determinism probe of tabpfn35 and tabdpt on
# results_heldout4_<tag>:h4_airlines_d__fifo1000 (two fresh runs, bit-identical), tasks_p3b.jsonl, one A800.
#SBATCH -J mice_probe_p3
#SBATCH -A p_p2105445
#SBATCH -p A800
#SBATCH --qos=cpu-500_core-a800-8_card
#SBATCH -N 1
#SBATCH --gres=gpu:a800:1
#SBATCH --ntasks-per-node=1
#SBATCH -c 7
#SBATCH -t 24:00:00
#SBATCH -o /ssdfs/datahome/u2105445/mice_rerun/logs/%x_%j.out

source /ssdfs/datahome/u2105445/mice_rerun/repo/experiments/clean_rerun_mice_h800/cluster/env.sh
Q=$WORK/qualify_p3
mkdir -p "$Q"
cd "$RR"
date; hostname
q() {
  test -e "$Q/$1" && { echo "[$1] exists: skipped"; return; }
  echo "[$1] $(date '+%F %T') start"
  "$PY" rerun.py qualify "results_heldout4_$1:h4_airlines_d__fifo1000" "$Q/$1" --tasks tasks_p3b.jsonl > "$Q/$1.out" 2>&1
  echo "[$1] $(date '+%F %T') end rc=$?: $(tail -1 "$Q/$1.out")"
}
q tabpfn35 &
q tabdpt &
wait
date
