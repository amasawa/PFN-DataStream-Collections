#!/bin/bash
# P1 benchmark (HANDOFF step 4, exclusive tasks last): one job per task, one worker, --gpu exclusive, nothing else on
# the GPU; SETS = the benchmark's set (sbatch --export=ALL,SETS=mice-r13-bench-h800). Benchmarks get one attempt.
#SBATCH -J mice_bench
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
cd "$RR"
date; hostname; echo "SETS=$SETS"; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
ls -la "$TABPFN_MODEL_CACHE_DIR"
"$PY" rerun.py worker "${SLURM_JOB_ID}_w1" --gpu exclusive --sets "$SETS"
date
