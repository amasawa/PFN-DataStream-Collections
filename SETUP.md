# Setting up a second machine

Code, logs and small result tables are in git. Data, `.npz` results and caches are not (see `.gitignore`).

## 1. Code
```bash
git clone git@github.com:amasawa/PFN-DataStream-Collections.git dataStream && cd dataStream
```

## 2. Data
**Since the split (2026-10-07):** All untracked files of this repository (MICE/data, ResetEval results and caches, ...) are in `datastream-data.tar`
(OneDrive, University of Sydney, `datastream-data/`, with `SHA256SUMS`, `setup.sh` and `README-WJD02YF4.txt`).
`setup.sh` makes a deploy key, clones the repository and unpacks the archive; it was used on WJD02YF4 on 2026-10-07.
The description below is of the joint repository `oodpfn` before the split.

The untracked files under `AgDR/data/`, `GOR/data/`, `MICE/data/` and `DriftTriage/data/` (283 files, 3.4 GB) are
packed in `pfn-data.tar`, kept in OneDrive (University of Sydney) under `pfn-data/`, next to `SHA256SUMS`.
Unpack in the repository root; the archive stores paths relative to it:
```bash
sha256sum -c SHA256SUMS      # with the tar files in the current directory
tar -xf pfn-data.tar
tar -xf pfn-refs.tar         # optional: reference PDFs -> pdfs/refs/
```
`pfn-results.tar` (optional, 5 GB) holds the untracked result files (`.npz`, caches). It is only needed to rebuild
tables and figures without rerunning, or to resume a run; unpack it the same way.

To rebuild `MICE/data/` without the archive, run in `MICE/code/` with the `stream` environment:
`streams.py --real`, `grid_streams.py`, `streams_heldout.py`, `streams_heldout2.py`. The last one expects the six
CSV files of github.com/ogozuacik/concept-drift-datasets-scikit-multiflow in `MICE/data/external_cdd/`.

## 3. Environments
Python 3.12; exact versions in `env/`. The scripts are started with `~/pfn-venvs/<name>/bin/python`.

| environment | file | used for |
|---|---|---|
| `venv` | `env/requirements-venv.txt` | TabPFN v2, TabICL, all experiments |
| `venv-tabdpt` | `env/requirements-venv-tabdpt.txt` | TabDPT baseline |
| `stream` | `env/requirements-stream.txt` | river stream generators (`MICE/code/streams*.py`) |

```bash
python3.12 -m venv ~/pfn-venvs/venv && ~/pfn-venvs/venv/bin/pip install -r env/requirements-venv.txt
```
`torch` is the CUDA 12.6 build (`+cu126`); install it from the matching PyTorch index if pip cannot resolve it.
TabPFN v2 weights are downloaded on first use.

## 4. Two machines at once
- Data are read-only, so sharing them causes no conflict.
- Give each machine different work (a different project, stream or seed). Result files are named after
  stream, condition and policy, not after the machine, so the same job on two machines writes the same file names.
- `git pull --rebase` before starting and before every push; append to `logs/EXPERIMENT_LOG.md` only for the
  project the machine is working on.
