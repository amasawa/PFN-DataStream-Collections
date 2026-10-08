# dataStream — project instructions for Claude Code

Team rules (roles, routing, review formats, severity, safety) are in `~/.claude/CLAUDE.md`. This file adds only the
constraints specific to this repository.

## Layout and records
- Projects and their logs: see `README.md`. Each project keeps its own `logs/`; never mix them. Machine faults and
  fixes: `env/MACHINE_LOG.md`.
- Write logs in Chinese with timestamps taken from `date` (never estimated). During long runs, log important events
  about every 10 minutes and skip entries when nothing changed.
- Commit and push every significant attempt, code change or LaTeX change right after it, with explicit paths only
  (other agents may have uncommitted work in the tree).

## Experiments
- Raw runs live on Linux storage under `~/pfn-runs/<run>/`; locks and checkpoints must be there, not on `/mnt/c`
  (mkdir is not atomic there). Check `test -e` before creating a run directory: another agent may own it.
- Frozen evaluations (`experiments/*/PLAN*.md`, `experiments/duo_heldout_20261008/`): plan, criteria and evaluator are
  committed before any run; operational changes go into a dated amendment (e.g. `AMENDMENT_20261008.md`) committed
  before execution and before any score is inspected; never evaluate partial outputs; report failures.
- Environment for TabPFN/TabICL runs: `~/pfn-venvs/venv`, `OMP_NUM_THREADS=1` (keep it for frozen runs: thread count
  can change floating-point order), no `PYTORCH_CUDA_ALLOC_CONF=expandable_segments`, `CUDA_LAUNCH_BLOCKING=0`.
- This machine (RTX 5000 Ada 32 GB, WSL2) has intermittent CUDA failures ("unspecified launch failure", "illegal
  memory access") that kill one process; never catch them and continue in-process. Retry in a new process from an
  atomically written checkpoint. For TabPFN v2 workloads, 2–3 concurrent workers gave the best throughput; 4–8
  produced failure storms (2026-10-08). Supervisor: `experiments/night_20261007/supervisor.py` (`--resource-mode`).
- Keep GPU utilisation high (user goal >= 90%, GPU memory and RAM < 90%) but measure completed tasks per hour, not
  utilisation alone.

## Papers
- LaTeX compiles locally with Tectonic: `/mnt/c/Users/zhwu9808/Desktop/GRPO/.runtime/envs/paper/bin/tectonic -X
  compile main.tex` (XeTeX falls back from Times; the venue build is pdfLaTeX on Overleaf).
- Tables are generated from result CSVs by each paper's `make_tables.py`; check every number in the text against the
  CSVs before committing.
- MICE is submitted; MICE-DUO (`MiceDuo/paper/`) and ResetEval (`ResetEval/overleaf/tmlr/`) are in progress.

## Consultations in this repo
- Codex runs on the user's ChatGPT quota: bounded questions, evidence inline, diffs instead of whole files, at most
  8 findings. Never let Codex create run directories or write files.
- Record each consultation's question, answer, and accepted/rejected findings in the relevant project log.
