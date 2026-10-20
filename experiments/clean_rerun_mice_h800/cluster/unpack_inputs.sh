#!/bin/bash
# Check and untar the input bundles on the cluster (HANDOFF step 1, P2 and P3 inputs).
# Usage: bash unpack_inputs.sh p1|p2|p3
# Each bundle is first checked with its SHA256SUMS; each tar is extracted into its registered place and then
# checked with its <tar>.files.sha256 in that place. Any mismatch stops (exit non-zero) before the next tar.
set -euo pipefail
WORK=/ssdfs/datahome/$USER/mice_rerun
HOME_J=$WORK/home

untar_check() {  # $1 = tar, $2 = destination directory
  local tarf=$1 dest=$2
  mkdir -p "$dest"
  tar -xf "$tarf" -C "$dest" --no-same-owner
  (cd "$dest" && sha256sum -c --quiet "$tarf.files.sha256") && echo "OK  $(basename "$tarf") -> $dest"
}

case ${1:-} in
  p1)
    B=$WORK/bundle
    (cd "$B" && sha256sum -c --quiet SHA256SUMS) && echo "OK  bundle SHA256SUMS"
    untar_check "$B/MICE_data.tar" "$WORK/repo/MICE"
    for t in "$B"/runs/*.tar; do
      root=$(basename "$t" .tar)
      test -e "$HOME_J/pfn-runs/$root" && { echo "STOP: $HOME_J/pfn-runs/$root exists"; exit 1; }
      untar_check "$t" "$HOME_J/pfn-runs/$root"
    done
    untar_check "$B/ext-baselines.tar" "$HOME_J/ext-baselines"
    grep -q 'Drift-Resilient_TabPFN/tabpfn/model_cache/tabpfn_dist_model_1.cpkt' "$B/ext-baselines.tar.files.sha256" \
      && echo "OK  DR model_cache listed"
    untar_check "$B/tabpfn_cache.tar" "$HOME_J/pfn-venvs/cache"
    ls -la "$HOME_J/pfn-venvs/cache/tabpfn/"*.ckpt
    ;;
  p2)
    B=$WORK/bundle_p2
    (cd "$B" && sha256sum -c --quiet SHA256SUMS) && echo "OK  bundle_p2 SHA256SUMS"
    untar_check "$B/ext-baselines-p2.tar" "$HOME_J/ext-baselines"
    ;;
  p3)
    B=$WORK/bundle_p3
    (cd "$B" && sha256sum -c --quiet SHA256SUMS) && echo "OK  bundle_p3 SHA256SUMS"
    untar_check "$B/p3_weights.tar" "$HOME_J"
    untar_check "$B/ext-baselines-p3.tar" "$HOME_J/ext-baselines"
    ;;
  *) echo "usage: $0 p1|p2|p3"; exit 2 ;;
esac
