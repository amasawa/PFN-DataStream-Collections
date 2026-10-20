#!/bin/bash
# P2 production (REGISTRATION_P2_20261020): CPU tasks of tasks_p2.jsonl on the P2 node type (AMD EPYC 9654, partition amd).
# Fixed 2 cores per worker (the tasks use 1 or 2 threads): NW = cpus / 2 workers. TASKS (default tasks_p2.jsonl) selects
# the list, e.g. sbatch --export=ALL,TASKS=tasks_stage2_fsnet_ext.jsonl (P2b and the dtmoe CPU lists run the same way).
#SBATCH -J mice_p2
#SBATCH -A p_p2105445
#SBATCH -p amd
#SBATCH --qos=cpu-500_core-a800-8_card
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -c 48
#SBATCH -t 24:00:00
#SBATCH -o /ssdfs/datahome/u2105445/mice_rerun/logs/%x_%j.out

source /ssdfs/datahome/u2105445/mice_rerun/repo/experiments/clean_rerun_mice_h800/cluster/env.sh
NW=$((SLURM_CPUS_PER_TASK / 2))
TASKS=${TASKS:-tasks_p2.jsonl}
L=$WORK/logs
cd "$RR"
date; hostname; lscpu | grep "Model name"; echo "TASKS=$TASKS NW=$NW cpus=$SLURM_CPUS_PER_TASK (2 per worker) mem/cpu=${SLURM_MEM_PER_CPU:-}"
( echo "time,load1,job_rss_mib"
  while true; do echo "$(date '+%F %T'),$(cut -d' ' -f1 /proc/loadavg),$(ps -u "$USER" -o rss= | awk '{s+=$1} END {printf "%d", s/1024}')"; sleep 60; done
) > "$L/p2_${SLURM_JOB_ID}_res.csv" 2>&1 &
SAMPLER=$!
for w in $(seq 1 "$NW"); do
  "$PY" rerun.py worker "${SLURM_JOB_ID}_w${w}" --gpu cpu --tasks "$TASKS" > "$L/p2_${SLURM_JOB_ID}_w${w}.log" 2>&1 &
done
wait $(jobs -p | grep -v "^$SAMPLER$")
kill $SAMPLER
date
