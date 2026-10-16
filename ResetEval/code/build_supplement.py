"""Builds the anonymised supplementary archive of the TMLR submission: code, stream construction scripts and the
per-run results from which make_tables.py, make_figs.py and thm_check.py regenerate every table, figure and the
guarantee check. Not included: the cached TFM predictions (results/cache_*, results/probs_*; about 1.5 GB), run logs,
and the stream files (rebuilt from public sources by the stream scripts). User names and absolute paths are replaced.

Usage: python build_supplement.py <out.tgz>   (refuses to overwrite)"""
import io
from pathlib import Path
import re
import sys
import tarfile

HERE = Path(__file__).resolve().parent
PROJ, REPO = HERE.parent, HERE.parents[1]
OPS = {'keep_busy.sh', 'supervisor.sh', 'queue_status.py', 'after_gas.sh', 'stage_done.sh', 'relay_seeds.sh',
       'build_supplement.py'}
STREAMS = ['streams.py', 'streams_heldout.py', 'streams_heldout2.py', 'streams_heldout3.py', 'streams_heldout4.py',
           'grid_streams.py']
SKIP_RESULTS = re.compile(r'^(cache_|probs_)|\.(log|err|out)$|^console|^gpu_util|^queue_|keep_busy|finish_stage|^relay_|^stage_done|^supervisor')
TEXT = {'.py', '.sh', '.csv', '.txt', '.md', '.json'}
SCRUB = [(re.compile(re.escape(str(REPO))), '<repo>'), (re.compile(r'/mnt/c/Users/zhwu9808'), '<home>'),
         (re.compile(r'/home/zhwu9808'), '<home>'), (re.compile('zhwu9808'), 'user')]

README = """# Supplementary material: resets for in-context stream learners

code/      evaluation (reset_eval.py), replay and metrics (metrics_replay.py), analyses, tables (make_tables.py),
           figures (make_figs.py), guarantee check (thm_check.py), tests
streams/   construction of the real and synthetic streams from their public sources (the added sources:
           code/streams_new.py); the stream files are not included. streams_new.py reads the raw downloads from
           data/_raw/<source>/ (file names as opened in each of its functions, e.g. data/_raw/home/HT_Sensor_metadata.dat
           and data/_raw/home/HT_Sensor_dataset/HT_Sensor_dataset.dat) and writes data/<stream>.npz
results/   per-run results (per-batch accuracy, log-loss and reset positions for every stream, detector, action,
           backbone, seed and budget), summary and test CSVs, replayed metrics

Regenerating tables, figures and the guarantee check (Python 3.12, numpy, pandas, scipy, matplotlib):
    cd code && python make_tables.py && python make_figs.py && python thm_check.py
(tables and figures are written to overleaf/tmlr/tables and overleaf/tmlr/figs, the guarantee check to results/)
The data table (Table of sources) also needs the stream files. Rerunning the TFMs needs the streams and
TabPFN v2 / TabICL / TabDPT (versions in the paper's reproducibility appendix); the cached predictions will be
released with the paper.
"""


def add(tar, path, arc):
    data = path.read_bytes()
    if path.suffix in TEXT:
        text = data.decode('utf-8', errors='replace')
        for pat, rep in SCRUB:
            text = pat.sub(rep, text)
        data = text.encode()
    info = tarfile.TarInfo(arc); info.size = len(data); info.mtime = 0; info.uname = info.gname = ''
    tar.addfile(info, io.BytesIO(data))


def main(out):
    out = Path(out)
    assert not out.exists(), out
    with tarfile.open(out, 'w:gz') as tar:
        add_bytes = README.encode(); info = tarfile.TarInfo('supplement/README.md'); info.size = len(add_bytes)
        tar.addfile(info, io.BytesIO(add_bytes))
        for d in ('supplement/overleaf/tmlr/tables', 'supplement/overleaf/tmlr/figs'):   # outputs of the scripts
            info = tarfile.TarInfo(d); info.type = tarfile.DIRTYPE; info.mode = 0o755; tar.addfile(info)
        for p in sorted(HERE.iterdir()):
            if p.is_file() and p.name not in OPS and not p.name.startswith('run_queue'):
                add(tar, p, f'supplement/code/{p.name}')
        for name in STREAMS:
            add(tar, REPO / 'MICE/code' / name, f'supplement/streams/{name}')
        for p in sorted((PROJ / 'results').rglob('*')):
            rel = p.relative_to(PROJ / 'results')
            if p.is_file() and not SKIP_RESULTS.search(rel.parts[0]) and '__pycache__' not in rel.parts:
                add(tar, p, f'supplement/results/{rel.as_posix()}')
    print(out, f'{out.stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    main(sys.argv[1])
