#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "$0")/../.." && pwd)
run_root=/home/zhwu9808/pfn-runs/duo-heldout-20261008
python_bin=/home/zhwu9808/pfn-venvs/venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
"$python_bin" "$repo/experiments/duo_heldout_20261008/prepare.py" "$run_root"
mkdir -p "$repo/experiments/duo_heldout_20261008/frozen"
cp "$run_root/freeze.json" "$run_root/data_manifest.json" "$run_root/tasks.json" "$repo/experiments/duo_heldout_20261008/frozen/"
tmux new-session -d -s duo-heldout-20261008 \
  "$python_bin $run_root/controller/finish.py $run_root '$repo' > $run_root/supervisor-console.log 2>&1"
echo "Started frozen evaluation: $run_root (tmux duo-heldout-20261008)"
