#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
root="$HOME/pfn-runs/night-20261007"
if tmux has-session -t pfn-night-20261007 2>/dev/null; then
  supervisor_pid=$(tmux list-panes -t pfn-night-20261007 -F '#{pane_pid}')
  if ! tr '\0' ' ' < "/proc/$supervisor_pid/cmdline" | rg -q '/night-20261007/controller/supervisor.py'; then
    echo 'Unexpected tmux process; refusing to terminate it.' >&2
    exit 1
  fi
  kill -TERM "$supervisor_pid"
  for attempt in $(seq 1 120); do
    if ! tmux has-session -t pfn-night-20261007 2>/dev/null; then break; fi
    sleep 1
  done
  if tmux has-session -t pfn-night-20261007 2>/dev/null; then
    echo 'Supervisor still shutting down; retry later.' >&2
    exit 1
  fi
fi
exec bash "$repo/experiments/night_20261007/launch.sh"
