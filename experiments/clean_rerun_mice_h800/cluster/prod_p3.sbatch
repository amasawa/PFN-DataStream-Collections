#!/bin/bash
# P3 step 4 (HANDOFF P3 order, AMENDMENT_20261020d): production of tasks_p3b.jsonl on one A800, NW workers
# (OMP_NUM_THREADS=4 tasks: 3 per GPU as for the OMP 4 results_* sets), --gpu shared, EXCL = p3_smoke plus the sets of
# any excluded or paused backbone. Submit: sbatch --export=ALL,EXCL=<sets> prod_p3.sbatch
#SBATCH -J mice_p3
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
NW=${NW:-3}
: "${EXCL:?set EXCL}"
L=$WORK/logs
cd "$RR"
date; hostname; echo "NW=$NW GPUs=$CUDA_VISIBLE_DEVICES exclude-sets: $EXCL"
( echo "time,gpu,util_pct,mem_used_mib,mem_total_mib"
  while true; do t=$(date '+%F %T')
    nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | sed "s/^/$t,/; s/, /,/g"
    sleep 60; done ) > "$L/p3_${SLURM_JOB_ID}_res.csv" 2>&1 &
SAMPLER=$!
for w in $(seq 1 "$NW"); do
  "$PY" rerun.py worker "${SLURM_JOB_ID}_w${w}" --gpu shared --tasks tasks_p3b.jsonl --exclude-sets "$EXCL" \
    > "$L/p3_${SLURM_JOB_ID}_w${w}.log" 2>&1 &
done
wait $(jobs -p | grep -v "^$SAMPLER$")
kill $SAMPLER
date
