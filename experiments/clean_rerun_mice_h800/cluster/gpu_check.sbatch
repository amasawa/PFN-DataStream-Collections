#!/bin/bash
# HANDOFF step 2 GPU check: driver, sm_80 in every CUDA environment, a small matmul; no task is run.
#SBATCH -J mice_gpucheck
#SBATCH -A p_p2105445
#SBATCH -p A800
#SBATCH --qos=cpu-500_core-a800-8_card
#SBATCH -N 1
#SBATCH --gres=gpu:a800:1
#SBATCH --ntasks-per-node=1
#SBATCH -c 7
#SBATCH -t 00:20:00
#SBATCH -o /ssdfs/datahome/u2105445/mice_rerun/logs/%x_%j.out

source /ssdfs/datahome/u2105445/mice_rerun/repo/experiments/clean_rerun_mice_h800/cluster/env.sh
date; hostname
nvidia-smi
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_mode --format=csv
for p in "$PY" "$PYDR" "$PYTOT" "$PYDPT"; do
  echo "== $p"
  "$p" -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0), torch.cuda.get_arch_list()); assert 'sm_80' in torch.cuda.get_arch_list(); x=torch.randn(1024,1024,device='cuda'); print('matmul ok', float((x@x).sum().isfinite()))" 2>&1
done
mps_start
"$PY" -c "import torch; x=torch.randn(1024,1024,device='cuda'); print('matmul under MPS ok', float((x@x).sum().isfinite()))"
echo "mps servers: $(echo get_server_list | nvidia-cuda-mps-control)"
mps_stop
date
