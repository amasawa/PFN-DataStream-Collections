#!/bin/bash
# dtmoe on the cluster CPU: determinism probe of the three m2 probe ids (AMENDMENT_20261020c), each run twice in fresh
# processes on the P2 node type (AMD EPYC 9654), single-thread (tasks_dtmoe_cpu.jsonl, cluster/make_tasks_dtmoe_cpu.py).
#SBATCH -J mice_probe_dtcpu
#SBATCH -A p_p2105445
#SBATCH -p amd
#SBATCH --qos=cpu-500_core-a800-8_card
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -c 6
#SBATCH -t 24:00:00
#SBATCH -o /ssdfs/datahome/u2105445/mice_rerun/logs/%x_%j.out

source /ssdfs/datahome/u2105445/mice_rerun/repo/experiments/clean_rerun_mice_h800/cluster/env.sh
Q=$WORK/qualify_dtmoe_cpu
mkdir -p "$Q"
cd "$RR"
date; hostname
lscpu | grep -E "Model name"
q() {
  test -e "$Q/$1" && { echo "[$1] exists: skipped"; return; }
  echo "[$1] $(date '+%F %T') start $2"
  "$PY" rerun.py qualify "$2" "$Q/$1" --tasks tasks_dtmoe_cpu.jsonl > "$Q/$1.out" 2>&1
  echo "[$1] $(date '+%F %T') end rc=$? $2: $(tail -1 "$Q/$1.out")"
}
q 9 "dtmoe_cpu_dev:elec2__dtmoe_L16_lr0.0001_s1_m2" &
q 10 "dtmoe_cpu_dev:elec2__dtmoe_L32_lr0.0001_s1_m2" &
q 11 "dtmoe_cpu_dev:insects_abrupt_balanced__dtmoe_L32_lr0.001_s5_m2" &
wait
date
