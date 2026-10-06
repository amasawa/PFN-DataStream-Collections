"""Status of run_queue3.sh queues from the result files: prints "<queue> <lines> <complete> <unclaimed>" per queue.
complete = every policy file of the line exists; unclaimed = no lock directory for the line's key.
Usage: python queue_status.py <queue file> [...]"""
import os
import sys

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
DETS = ["ddm", "eddm", "fhddm", "hddma", "hddmw", "adwin", "ph", "kswin"]
HSENS = [f"+hedge@e{e}g{g}" for e, g in [(0.5, 0.5), (1, 0.5), (4, 0.5), (8, 0.5), (2, 0.25), (2, 0.75), (2, 0.9)]]
POLSETS = {"std": ["none", "ddmM"] + [d + v for d in DETS for v in ("", "+half", "+hedge")],
           "hsens": [d + v for d in DETS for v in HSENS]}
TRAINED = ["none"] + [d + v for d in DETS for v in ("", "+hedge")]


def line_status(q, line):
    f = line.split() + [None] * 6
    s, seed, m, ps, kind = f[0], f[2] or "0", f[3] or "1000", f[4] or "std", f[5] or "tfm"
    key = s + (f"_s{seed}" if seed != "0" else "") + (f"_M{m}" if m != "1000" else "") + \
        (f"_{ps}" if ps != "std" else "") + (f"_{kind}" if kind != "tfm" else "")
    if kind == "tfm":
        d, pols = f"{RES}/tabpfn{'' if seed == '0' else '_s' + seed}_M{m}", POLSETS[ps]
    else:
        d, pols = f"{RES}/trained_{kind}", TRAINED
    done = all(os.path.exists(f"{d}/{s}__{p}.npz") for p in pols)
    lock = os.path.expanduser(f"~/.reset_locks/{os.path.basename(q)[:-4]}/{key}")
    return done, not os.path.isdir(lock)


if __name__ == "__main__":
    for q in sys.argv[1:]:
        st = [line_status(q, l) for l in open(q) if l.strip()]
        print(os.path.basename(q)[:-4], len(st), sum(d for d, _ in st), sum(u and not d for d, u in st))
