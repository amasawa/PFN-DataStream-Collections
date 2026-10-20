# Job environment of the clean MICE rerun on the Tongji A800 cluster (HANDOFF step 2). Source it in every job.
WORK=/ssdfs/datahome/u2105445/mice_rerun
export REPO=$WORK/repo
export HOME=$WORK/home
export RUNS=$WORK/home/pfn-runs
export PY=$WORK/envs/venv/bin/python
export PYDR=$WORK/envs/drtabpfn/bin/python
export PYTOT=$WORK/envs/totgpu/bin/python
export PYST=$WORK/envs/stream/bin/python
export PYTS=$WORK/envs/tsbase/bin/python
export PYDPT=$WORK/envs/tabdpt/bin/python
export W3=$WORK/home/mice-p3-weights
export TABPFN_MODEL_CACHE_DIR=$WORK/home/pfn-venvs/cache/tabpfn
export HF_HOME=$WORK/hf
export HF_HUB_OFFLINE=1
export TABPFN_DISABLE_TELEMETRY=1
RR=$REPO/experiments/clean_rerun_mice_h800

# CUDA MPS (AMENDMENT_20261020b item 2): one control daemon per job, pipes and logs in node-local /tmp
mps_start() {
  export CUDA_MPS_PIPE_DIRECTORY=/tmp/mps_pipe_$SLURM_JOB_ID CUDA_MPS_LOG_DIRECTORY=/tmp/mps_log_$SLURM_JOB_ID
  mkdir -p "$CUDA_MPS_PIPE_DIRECTORY" "$CUDA_MPS_LOG_DIRECTORY"
  nvidia-cuda-mps-control -d && echo "MPS started on $(hostname) (GPUs $CUDA_VISIBLE_DEVICES)"
}
mps_stop() {
  echo quit | nvidia-cuda-mps-control
  echo "MPS stopped"
}
