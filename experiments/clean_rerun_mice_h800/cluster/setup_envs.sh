#!/bin/bash
# Build the Python environments of env_lock/ on the cluster login node (HANDOFF step 2, P2, P3).
# Usage: bash setup_envs.sh <env> [<env> ...]   env in: venv drtabpfn totgpu stream tsbase tabdpt
# Each env is a plain venv on a conda base Python of the version in env_lock/python_versions.txt,
# installed with --no-deps from its lock file, then its pip freeze is written to cluster/env_freeze_<env>.txt
# and compared with the lock (any difference is printed and makes the script exit non-zero).
set -euo pipefail
WORK=/ssdfs/datahome/$USER/mice_rerun
LOCK=$WORK/repo/experiments/clean_rerun_mice_h800/env_lock
OUT=$WORK/repo/experiments/clean_rerun_mice_h800/cluster
ENVS=$WORK/envs
CONDA=/share/apps/anaconda3/bin/conda
PYPI=https://pypi.tuna.tsinghua.edu.cn/simple
mkdir -p "$ENVS"

base() {  # $1 = 3.12.15 | 3.11.17
  local p=$ENVS/base_$1
  if [ ! -x "$p/bin/python" ]; then
    "$CONDA" create -y -p "$p" --override-channels -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main "python=$1" >/dev/null
  fi
  echo "$p/bin/python"
}

rc=0
for name in "$@"; do
  case $name in
    venv|tabdpt)   pyv=3.12.15; torchidx=https://download.pytorch.org/whl/cu126 ;;
    stream)        pyv=3.12.15; torchidx= ;;
    tsbase)        pyv=3.12.15; torchidx=https://download.pytorch.org/whl/cpu ;;
    drtabpfn|totgpu) pyv=3.11.17; torchidx=https://download.pytorch.org/whl/cu121 ;;
    *) echo "unknown env $name"; exit 2 ;;
  esac
  dest=$ENVS/$name
  test -e "$dest" && { echo "$dest exists: not touched"; rc=1; continue; }
  "$(base $pyv)" -m venv "$dest"
  req=$ENVS/req_$name.txt
  sed "s#-e file:///home/zhwu9808/ext-baselines/#-e $WORK/home/ext-baselines/#" "$LOCK/$name.txt" > "$req"
  extra=(); [ -n "$torchidx" ] && extra=(--extra-index-url "$torchidx")
  "$dest/bin/python" -m pip install -q --no-deps -i "$PYPI" "${extra[@]}" -r "$req"
  "$dest/bin/python" --version > "$OUT/env_freeze_$name.txt"
  "$dest/bin/python" -m pip freeze --all >> "$OUT/env_freeze_$name.txt"
  # compare the package lines (the editable line differs only by its path); names are compared in their
  # PEP 503 normal form, since pip freeze writes e.g. Jinja2 / typing_extensions where the lock has jinja2 / typing-extensions
  norm() { grep -vE '^Python |^-e |^# Editable' "$1" | grep -viE '^(pip|setuptools|wheel)==' \
             | awk -F'==' '{n=tolower($1); gsub(/[-_.]+/, "-", n); print n "==" $2}' | sort; }
  if diff <(norm "$req") <(norm "$OUT/env_freeze_$name.txt") > "$ENVS/diff_$name.txt"; then
    echo "$name: freeze matches lock ($("$dest/bin/python" --version))"
  else
    echo "$name: FREEZE DIFFERS FROM LOCK"; cat "$ENVS/diff_$name.txt"; rc=1
  fi
  for t in pip setuptools wheel; do
    l=$(grep -E "^$t==" "$req" || true); f=$(grep -E "^$t==" "$OUT/env_freeze_$name.txt" || true)
    [ -n "$l" ] && [ "$l" != "$f" ] && { echo "$name: $t lock=$l freeze=${f:-absent}"; rc=1; }
  done
done
exit $rc
