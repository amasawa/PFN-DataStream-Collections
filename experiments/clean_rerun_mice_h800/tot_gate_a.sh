#!/bin/bash
# Gate (a) of TOT (REGISTRATION_P6_GATE_A_20261020.md): the released LSTD-TOT code, unchanged, on ETTh2 pred_len 1,
# seed 2023 (run_LSTD_TOT.py's default), on one GPU (the released code requires CUDA: main.py asserts it; amendment
# below), 1 CPU thread, 12 h wall-clock limit. The code is copied into <out>/code first (it writes checkpoints and results next to
# itself). Writes <out>/gate_a.json with the final online MSE and the verdict of the registered rule.
# Usage: tot_gate_a.sh <python of venv-tot> <out dir>
set -u
PYT=$1; OUT=$2; SRC=$HOME/ext-baselines/TOT_neurips_supp/source_code/LSTD-TOT
test -e $OUT && { echo "$OUT exists"; exit 1; }; mkdir -p $OUT
cp -r $SRC $OUT/code && rm -rf $OUT/code/checkpoints/* $OUT/code/__pycache__
CFG=$(cd $OUT/code && $PYT -c "import importlib.util as u; s=u.spec_from_file_location('c','LSTD_TOT_config.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print(m.d['ETTh2'][1])")
cd $OUT/code
start=$(date +%s)
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 WANDB_MODE=disabled \
  timeout 43200 bash -c "$PYT ./main.py $CFG --seed 2023 --gpu 0" > $OUT/log.txt 2>&1
rc=$?; wall=$(( $(date +%s) - start ))
$PYT - "$OUT" "$rc" "$wall" <<'PY'
import json, re, sys
out, rc, wall = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
m = re.findall(r"^mse:([0-9.eE+-]+), mae:([0-9.eE+-]+)", open(f"{out}/log.txt").read(), re.M)
MEAN, SD = 0.374, 0.0031          # arXiv 2510.18281v1 Table A14 (p. 37) and Table A16 (p. 38): LSTD+TOT, ETTh2, 1
if rc == 124:
    verdict = "pending (12 h wall-clock limit reached)"
elif rc != 0 or not m:
    verdict = "skipped (the released code did not finish)"
else:
    mse = float(m[-1][0]); verdict = "pass" if abs(mse - MEAN) <= 2 * SD else "skipped (outside 2 sd)"
rec = dict(rc=rc, wall_s=wall, mse=float(m[-1][0]) if m else None, mae=float(m[-1][1]) if m else None,
           target_mean=MEAN, target_sd=SD, threshold=2 * SD, verdict=verdict)
json.dump(rec, open(f"{out}/gate_a.json", "w"), indent=1); print(json.dumps(rec))
PY
