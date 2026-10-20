#!/bin/bash
# P2 determinism probe (REGISTRATION_P2_20261020 "Local evidence": seven task ids), on the P2 CPU node type
# (AMD EPYC 9654, partition amd). The seven qualify runs go in parallel, 2 cores each (the P2 tasks use 1 or 2 threads).
#SBATCH -J mice_probe_p2
#SBATCH -A p_p2105445
#SBATCH -p amd
#SBATCH --qos=cpu-500_core-a800-8_card
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -c 14
#SBATCH -t 06:00:00
#SBATCH -o /ssdfs/datahome/u2105445/mice_rerun/logs/%x_%j.out

source /ssdfs/datahome/u2105445/mice_rerun/repo/experiments/clean_rerun_mice_h800/cluster/env.sh
Q=$WORK/qualify_p2
mkdir -p "$Q"
cd "$RR"
date; hostname
lscpu | grep -E "Model name|^CPU\(s\)|Socket|Thread"; free -g | head -2
q() {
  test -e "$Q/$1" && { echo "[$1] exists: skipped"; return; }
  echo "[$1] $(date '+%F %T') start $2"
  "$PY" rerun.py qualify "$2" "$Q/$1" --tasks tasks_p2.jsonl > "$Q/$1.out" 2>&1
  echo "[$1] $(date '+%F %T') end rc=$? $2: $(tail -1 "$Q/$1.out")"
}
q 1 "results_river:elec2__hat" &
q 2 "results_trained_dev:elec2__mooe_lin_50_0.1_0.01" &
q 3 "mice-main-trained-grid20:grid_c5_b500_s20__nse" &
q 4 "mice-table1-trained-probs:h2_phishing__levbag" &
q 5 "mice-confirm-cp-20261017-cpu:cc_btc_2013__arf" &
q 6 "ts_dev:elec2__adaptz_L1_lr0.001_s1_m0.001" &
q 7 "results_heldout34_trained:h3_poker_b__mooe_rff2000_100_2_0.01" &
wait
date
