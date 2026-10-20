#!/bin/bash
# P3 step 1 (HANDOFF P3 order, AMENDMENT_20261020d): smoke test of set p3_smoke (TabPFN-3.5, TabDPT and the TabPFN v2
# reference, 6 tasks) by one worker, alone on one A800 (--gpu exclusive). Writes $RUNS/mice-p3-smoke/*.json.
#SBATCH -J mice_p3smoke
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
cd "$RR"
date; hostname; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
"$PY" rerun.py worker "${SLURM_JOB_ID}_w1" --gpu exclusive --sets p3_smoke --tasks tasks_p3b.jsonl
date
