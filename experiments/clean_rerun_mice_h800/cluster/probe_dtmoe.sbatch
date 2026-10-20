#!/bin/bash
# HANDOFF step 3, dtmoe probe with its cap (ACTIVATION item 2, AMENDMENT_20261020 item 3, AMENDMENT_20261020c _m2 ids):
# per id, a default-mode reference (rerun.py ref, wall time R), then the strict probe with --timeout 10 R.
# One A800 under the production configuration (MPS, 3 processes, 7 cores): one lane per id.
#SBATCH -J mice_probe_dtmoe
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
Q=$WORK/qualify
mkdir -p "$Q"
cd "$RR"
lane() {  # $1 = probe number, $2 = task id
  local n=$1 id=$2
  test -e "$Q/ref_$n" -o -e "$Q/$n" && { echo "[$n] exists: skipped"; return; }
  echo "[$n] $(date '+%F %T') ref start $id"
  "$PY" rerun.py ref "$id" "$Q/ref_$n" > "$Q/ref_$n.out" 2>&1
  local rc=$?
  echo "[$n] $(date '+%F %T') ref end rc=$rc: $(tail -1 "$Q/ref_$n.out")"
  test -f "$Q/ref_$n/ref.json" || { echo "[$n] no ref.json: strict probe not started"; return; }
  local cap
  cap=$("$PY" -c "import json,math; print(math.ceil(10*json.load(open('$Q/ref_$n/ref.json'))['wall_s']))") \
    || { echo "[$n] cannot read wall time from ref.json:"; cat "$Q/ref_$n/ref.json"; return; }
  echo "[$n] $(date '+%F %T') qualify start, --timeout $cap s"
  "$PY" rerun.py qualify "$id" "$Q/$n" --timeout "$cap" > "$Q/$n.out" 2>&1
  echo "[$n] $(date '+%F %T') qualify end rc=$?: $(tail -1 "$Q/$n.out")"
}
date; hostname; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
mps_start
lane 9  "dtmoe_dev:elec2__dtmoe_L16_lr0.0001_s1_m2" &
lane 10 "dtmoe_dev:elec2__dtmoe_L32_lr0.0001_s1_m2" &
lane 11 "dtmoe_dev:insects_abrupt_balanced__dtmoe_L32_lr0.001_s5_m2" &
wait
mps_stop
date
