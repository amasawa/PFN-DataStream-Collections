#!/bin/bash
# Drift-Resilient TabPFN (set drtabpfn, 92 tasks, no time estimate): its own job at the QOS maximum time limit
# (HANDOFF step 4, AMENDMENT_20261020 item 7). One A800, 7 cores, NW workers (OMP_NUM_THREADS=1 tasks; user: 6 per GPU).
#SBATCH -J mice_dr
#SBATCH -A p_p2105445
#SBATCH -p A800
#SBATCH --qos=cpu-500_core-a800-8_card
#SBATCH -N 1
#SBATCH --gres=gpu:a800:1
#SBATCH --ntasks-per-node=1
#SBATCH -c 7
#SBATCH -t 7-00:00:00
#SBATCH -o /ssdfs/datahome/u2105445/mice_rerun/logs/%x_%j.out

source /ssdfs/datahome/u2105445/mice_rerun/repo/experiments/clean_rerun_mice_h800/cluster/env.sh
NW=${NW:-6}
L=$WORK/logs
cd "$RR"
date; hostname; echo "NW=$NW GPUs=$CUDA_VISIBLE_DEVICES"
( echo "time,gpu,util_pct,mem_used_mib,mem_total_mib"
  while true; do t=$(date '+%F %T')
    nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | sed "s/^/$t,/; s/, /,/g"
    sleep 60; done ) > "$L/dr_${SLURM_JOB_ID}_res.csv" 2>&1 &
SAMPLER=$!
for w in $(seq 1 "$NW"); do
  "$PY" rerun.py worker "${SLURM_JOB_ID}_w${w}" --gpu shared --sets drtabpfn > "$L/dr_${SLURM_JOB_ID}_w${w}.log" 2>&1 &
done
wait $(jobs -p | grep -v "^$SAMPLER$")
kill $SAMPLER
date
