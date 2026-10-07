#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
root="$HOME/pfn-runs/night-20261007"
py="$HOME/pfn-venvs/venv/bin/python"
if [ -f "$root/STOP" ] && [ "${1:-}" != '--resume' ]; then
  echo 'This run was stopped for investigation. Inspect events.log; explicitly use --resume to restart.' >&2
  exit 1
fi
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export TABPFN_MODEL_CACHE_DIR="$HOME/pfn-venvs/cache/tabpfn"
if tmux has-session -t pfn-night-20261007 2>/dev/null; then
  echo 'Supervisor already running; controller snapshots were not changed.'
  exit 0
fi
"$py" "$repo/experiments/night_20261007/prepare.py" "$root"
mkdir -p "$root/controller"
for name in worker.py supervisor.py analyse.py checkpointed_baselines.py; do
  cp "$repo/experiments/night_20261007/$name" "$root/controller/$name"
done
if [ -f "$root/STOP" ]; then mv "$root/STOP" "$root/STOP.previous"; fi
if tmux has-session -t pfn-night-20261007 2>/dev/null; then
  echo 'Supervisor tmux session already exists.'
else
  tmux new-session -d -s pfn-night-20261007 "exec '$py' -u '$root/controller/supervisor.py' '$root' '$repo' --hours 8 --max-workers ${MAX_WORKERS:-6} >> '$root/supervisor-console.log' 2>&1"
fi
echo "Status: $root/status.json"
echo "Events: $root/events.log"
echo "GPU samples: $root/gpu.csv"
