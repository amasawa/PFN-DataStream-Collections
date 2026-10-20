"""TOT check on the cluster GPU before its development grid (AMENDMENT_20261020b item 3): time per batch of the
adapter on one A800 in deterministic mode, gate (b), and the projected cost of the development grid. No accuracy is
reported or kept: run_ts.run's per-run print is discarded and its temporary outputs are deleted; only times, the
projection and gate (b) (whether the predictions differ) are written.
- Timing: the 8 combinations of L {16, 32} x n_steps {1, 5} on the first 400 rows of elec2 (8 features) and of
  insects_abrupt_balanced (33 features); lr 1e-3, lambda 1e-5; median of the time of batches 1-3.
- Projection: per stream type, the sum over the four (L, steps) combinations of the time per batch, times the batches
  of the five development streams (elec2 453; four INSECTS streams 2138), times 9 (lr x lambda): every one of the 180
  tasks counted once. Compared with the registered CPU reference times (local CPU, one thread, 2026-10-20).
- Gate (b) (AMENDMENT_BASELINES_20261018 item 2): lambda 0 and lambda 1e-5 must give different predictions, on the first
  1500 rows of elec2 (a development stream), L 16, n_steps 1, lr 1e-3.
- Verdict: "proceed" only if gate (b) holds, the projected development cost is at most 300 GPU-hours, and the
  aggregate speed-up (projected CPU-hours / projected GPU-hours) is at least 5; otherwise "not run (gate b)" or
  "not run, for its cost".
Usage (venv-tot, TS_DEVICE=cuda, TS_DETERMINISTIC=1, CUBLAS_WORKSPACE_CONFIG=:4096:8): python tot_check.py <out.json>"""
import contextlib, json, os, shutil, sys, tempfile
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, f"{REPO}/experiments/mice_table1_fill_20261018")
import torch                                                   # noqa: E402
import run_ts, run_ts_tot                                      # noqa: E402

CPU_REF = {"elec2": {(16, 1): 1.1, (32, 1): 3.2, (16, 5): 4.3, (32, 5): 14.1},
           "insects_abrupt_balanced": {(16, 1): 25.4, (32, 1): 57.0, (16, 5): 112.6, (32, 5): 208.0}}
BATCHES = {"elec2": 453, "insects_abrupt_balanced": 528 + 241 + 570 + 799}


def main(out):
    assert run_ts.DEV.type == "cuda" and os.environ.get("TS_DETERMINISTIC") == "1"
    torch.set_num_threads(1); sys.path.insert(0, run_ts_tot.TOT_DIR); run_ts._count_triggers()
    tmp = tempfile.mkdtemp(prefix="tot_check_")
    for s, n in (("elec2", 400), ("insects_abrupt_balanced", 400), ("elec2", 1500)):
        z = np.load(f"{REPO}/MICE/data/{s}.npz")
        np.savez(f"{tmp}/{s}_{n}.npz", X=z["X"][:n], y=z["y"][:n], concept=z["concept"][:n])
    t = {}
    for s in CPU_REF:
        for (L, st) in CPU_REF[s]:
            d = f"{tmp}/o_{s}_{L}_{st}"
            os.makedirs(d)
            with contextlib.redirect_stdout(open(os.devnull, "w")):
                run_ts.run(tmp, d, f"{s}_400", "tot", L, 1e-3, st, 1e-5)
            w = np.load(f"{d}/{s}_400__tot_L{L}_lr0.001_s{st}_m1e-05.npz")["wt"][1:]
            t[f"{s} L{L} s{st}"] = float(np.median(w))
    proj_gpu = sum(sum(t[f"{s} L{L} s{st}"] for (L, st) in CPU_REF[s]) * BATCHES[s] * 9 for s in CPU_REF) / 3600
    proj_cpu = sum(sum(CPU_REF[s].values()) * BATCHES[s] * 9 for s in CPU_REF) / 3600
    assert sum(len(CPU_REF[s]) * 9 * {"elec2": 1, "insects_abrupt_balanced": 4}[s] for s in CPU_REF) == 180
    P = {}
    for lam in (0.0, 1e-5):
        d = f"{tmp}/b_{lam:g}"
        os.makedirs(d)
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            run_ts.run(tmp, d, "elec2_1500", "tot", 16, 1e-3, 1, lam)
        P[lam] = np.load(f"{d}/elec2_1500__tot_L16_lr0.001_s1_m{lam:g}.npz")["P"]
    gate_b = not np.array_equal(P[0.0], P[1e-5])
    shutil.rmtree(tmp)
    speedup = proj_cpu / proj_gpu
    verdict = ("not run (gate b: lambda has no effect)" if not gate_b else
               "proceed" if proj_gpu <= 300 and speedup >= 5 else "not run, for its cost")
    rec = dict(gpu=torch.cuda.get_device_name(0), s_per_batch=t, projected_dev_gpu_h=proj_gpu, projected_dev_cpu_h=proj_cpu,
               aggregate_speedup=speedup, gate_b_predictions_differ=bool(gate_b), verdict=verdict)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(rec, open(out + ".tmp", "w"), indent=1); os.replace(out + ".tmp", out); print(json.dumps(rec))


if __name__ == "__main__":
    main(sys.argv[1])
