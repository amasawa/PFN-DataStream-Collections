#!/bin/bash
# HANDOFF step 3: determinism probe of the 8 non-dtmoe probe ids, on one A800 under the production configuration
# (MPS, 3 processes on the GPU, 7 cores; AMENDMENT_20261020b item 2): three lanes, each running its probes in order.
#SBATCH -J mice_probe
#SBATCH -A p_p2105445
#SBATCH -p A800
#SBATCH --qos=cpu-500_core-a800-8_card
#SBATCH -N 1
#SBATCH --gres=gpu:a800:1
#SBATCH --ntasks-per-node=1
#SBATCH -c 7
#SBATCH -t 08:00:00
#SBATCH -o /ssdfs/datahome/u2105445/mice_rerun/logs/%x_%j.out

source /ssdfs/datahome/u2105445/mice_rerun/repo/experiments/clean_rerun_mice_h800/cluster/env.sh
Q=$WORK/qualify
mkdir -p "$Q"
cd "$RR"
q() {  # $1 = probe number (HANDOFF step 3 order), $2 = task id
  test -e "$Q/$1" && { echo "[$1] $Q/$1 exists: skipped"; return; }
  echo "[$1] $(date '+%F %T') start $2"
  "$PY" rerun.py qualify "$2" "$Q/$1" > "$Q/$1.out" 2>&1
  echo "[$1] $(date '+%F %T') end rc=$? $2: $(tail -1 "$Q/$1.out")"
}
date; hostname; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
mps_start
( q 1 "results_heldout3:h3_airlines_b__micev1000_500"; q 2 "results_test:agrawal_s10__fifo1000"
  q 7 "mice-tkde-control-20261009:mis_micev_mis_b700_c30_s30" ) &
( q 3 "results_heldout_tabicl:covertype__ddm1000"; q 4 "results_probs:covertype__ddm1000"
  q 6 "mice-r14b-acc:c_b2000_c100_s50_o0__snap1000_500.k2" ) &
( q 5 "mice-r14-test:t_b2000_c100_s40_o0__micecp1000_500"; q 8 "drtabpfn:elec2" ) &
wait
mps_stop
date
