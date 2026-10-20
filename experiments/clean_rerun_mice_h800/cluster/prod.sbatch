#!/bin/bash
# HANDOFF step 4: P1 production on 4 A800 of one node, NW workers per GPU (rerun.py worker --gpu shared).
# No MPS (user decision 2026-10-20 22:41 AEDT: the probes ran without MPS, see CLUSTER_RERUN_LOG.md).
# Submit: sbatch --export=ALL,NW=3,EXCL=<sets> prod.sbatch
# A sampler writes GPU utilisation / memory and the job's resident memory every 60 s to logs/prod_<job>_res.csv.
#SBATCH -J mice_prod
#SBATCH -A p_p2105445
#SBATCH -p A800
#SBATCH --qos=cpu-500_core-a800-8_card
#SBATCH -N 1
#SBATCH --gres=gpu:a800:4
#SBATCH --ntasks-per-node=1
#SBATCH -c 28
#SBATCH -t 24:00:00
#SBATCH -o /ssdfs/datahome/u2105445/mice_rerun/logs/%x_%j.out

source /ssdfs/datahome/u2105445/mice_rerun/repo/experiments/clean_rerun_mice_h800/cluster/env.sh
: "${NW:?set NW}" "${EXCL:?set EXCL}"
L=$WORK/logs
cd "$RR"
date; hostname; echo "NW=$NW GPUs=$CUDA_VISIBLE_DEVICES cpus=$SLURM_CPUS_PER_TASK mem/node=${SLURM_MEM_PER_NODE:-} mem/cpu=${SLURM_MEM_PER_CPU:-}"
echo "exclude-sets: $EXCL"

(  # resource sampler
  echo "time,gpu,util_pct,mem_used_mib,mem_total_mib,job_rss_mib,node_mem_used_gib"
  while true; do
    t=$(date '+%F %T')
    rss=$(ps -u "$USER" -o rss= | awk '{s+=$1} END {printf "%d", s/1024}')
    nm=$(free -g | awk '/^Mem:/ {print $3}')
    nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits \
      | while IFS=', ' read -r i u m mt; do echo "$t,$i,$u,$m,$mt,$rss,$nm"; done
    sleep 60
  done
) > "$L/prod_${SLURM_JOB_ID}_res.csv" 2>&1 &
SAMPLER=$!

IFS=, read -ra G <<< "$CUDA_VISIBLE_DEVICES"
for g in "${G[@]}"; do
  for w in $(seq 1 "$NW"); do
    CUDA_VISIBLE_DEVICES=$g "$PY" rerun.py worker "${SLURM_JOB_ID}_g${g}_w${w}" --gpu shared --exclude-sets "$EXCL" \
      > "$L/prod_${SLURM_JOB_ID}_g${g}_w${w}.log" 2>&1 &
  done
done
wait $(jobs -p | grep -v "^$SAMPLER$")
kill $SAMPLER
date
