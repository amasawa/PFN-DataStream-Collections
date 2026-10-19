"""run.py with another frozen backbone (phase P3 of the clean rerun: extra backbones), without touching run.py: run.TFM
is replaced, as run_seed.py does; policies, constants and outputs are those of run.py. Same arguments as run.py.
P3_BACKBONE selects the backbone, P3_WEIGHTS the directory of the downloaded weights (no network access is needed):
  tabpfn_v2.5, tabpfn_v2.6, tabpfn_v3, tabpfn_v3.5  tabpfn 9.0.0, create_default_for_version, 4 estimators (main venv)
  tabdpt                                            tabdpt 1.3.1, weights tabdpt1_3, full context, 4 ensemble members
                                                    (venv-tabdpt; settings as ResetEval/code/reset_eval.py)
  mitra2                                            autogluon.tabular 1.6.3 MitraClassifier, mitra-classifier-2,
                                                    fine_tune = False: the backbone stays frozen (venv-mitra)
  limix2                                            LimiX (commit 516bf39), LimiX-2, 4 of the 32 pipelines (members)
                                                    of cls_default_noretrieval_v2.json, evenly spaced over the list
                                                    (0, 8, 16, 24) (venv-limix)
As in run.TFM: a context with one class predicts it with probability 1 (no backbone call); probabilities are placed
in the columns of the global label set. The non-TabPFN backbones get labels remapped to 0..k-1 (k classes in the
context), and their k columns are mapped back."""
import argparse, json, os
import numpy as np
import run

BB = os.environ.get("P3_BACKBONE", "")
W = os.environ.get("P3_WEIGHTS", "")
TABPFN = {"tabpfn_v2.5": ("V2_5", "tabpfn/tabpfn-v2.5-classifier-v2.5_default.ckpt"),
          "tabpfn_v2.6": ("V2_6", "tabpfn/tabpfn-v2.6-classifier-v2.6_default.ckpt"),
          "tabpfn_v3": ("V3", "tabpfn/tabpfn-v3-classifier-v3_default.ckpt"),
          "tabpfn_v3.5": ("V3_5", "tabpfn/tabpfn-v3.5-20260909.safetensors")}
N_EST = 4                                    # estimators / ensemble members, as TabPFN v2 and TabICL in run.TFM
MITRA_EST = int(os.environ.get("P3_MITRA_EST", N_EST))
os.environ.setdefault("HF_HUB_OFFLINE", "1")                # weights come from P3_WEIGHTS only
_PATCHED = set()                                            # library patches are applied once per process


def _patch_mitra():
    """MitraClassifier.fit reloads the checkpoint for every member and call; with fine_tune = False the weights do not
    change (checked: state-dict hash before and after fit), so one loaded model is kept per process."""
    if "mitra" in _PATCHED:
        return
    from autogluon.tabular.models.mitra._internal.models import tab2d
    _load, cache = tab2d.Tab2D.from_pretrained, {}

    def load(cls, path, device="cuda"):
        key = (path, str(device))
        if key not in cache:
            cache[key] = _load.__func__(cls, path, device=device)
        return cache[key]
    tab2d.Tab2D.from_pretrained = classmethod(load); _PATCHED.add("mitra")


def _patch_limix():
    """LimiX's CacheManager creates a hard-coded /mnt/public directory in its constructor; the cache is unused
    (use_data_cache = False), so it is pointed to one temporary directory."""
    if "limix" in _PATCHED:
        return
    import tempfile
    from inference.v2_0 import predictor as _lp
    _cm, tmp = _lp.LimiXPredictor.CacheManager, tempfile.mkdtemp(prefix="limix_cache_")
    _lp.LimiXPredictor.CacheManager = type("CacheManager", (_cm,), {"__init__": lambda s, cache_dir=None: _cm.__init__(s, tmp)})
    _PATCHED.add("limix")


class TFM:
    def __init__(self, n_classes, seed=0):
        self.K, self.seed, self.calls = n_classes, seed, 0
        if BB in TABPFN:
            from tabpfn import TabPFNClassifier
            from tabpfn.constants import ModelVersion
            v, f = TABPFN[BB]
            self.m = TabPFNClassifier.create_default_for_version(getattr(ModelVersion, v), device="cuda", random_state=seed,
                                                                 n_estimators=N_EST, ignore_pretraining_limits=True,
                                                                 model_path=f"{W}/{f}")
        elif BB == "tabdpt":
            from tabdpt import TabDPTClassifier
            self.m = TabDPTClassifier(compile=False, verbose=False, device="cuda",
                                      model_weight_path=f"{W}/tabdpt/tabdpt1_3.safetensors")
        elif BB == "mitra2":
            from autogluon.tabular.models.mitra.sklearn_interface import MitraClassifier
            _patch_mitra()
            self.m = MitraClassifier(n_estimators=MITRA_EST, device="cuda", fine_tune=False,
                                     hf_model=f"{W}/mitra-classifier-2", seed=seed, verbose=False)
        elif BB == "limix2":
            import torch
            from inference.predictor import LimiXPredictor
            for k, v in (("RANK", "0"), ("WORLD_SIZE", "1"), ("MASTER_ADDR", "127.0.0.1"), ("MASTER_PORT", "29500")):
                os.environ.setdefault(k, v)                                   # as the LimiX README example
            import inference
            _patch_limix()
            cfg = json.load(open(os.path.join(os.path.dirname(os.path.dirname(inference.__file__)), "config",
                                              "cls_default_noretrieval_v2.json")))
            n = len(cfg["pipelines"])
            cfg["pipelines"] = [cfg["pipelines"][i * n // N_EST] for i in range(N_EST)]   # evenly spaced: 0, 8, 16, 24
            self.m = LimiXPredictor(device=torch.device("cuda"), model_path=f"{W}/limix-2/LimiX-2.ckpt",
                                    inference_config=cfg, seed=seed)
        else:
            raise SystemExit(f"P3_BACKBONE must be one of {sorted(TABPFN) + ['tabdpt', 'mitra2', 'limix2']}, got {BB!r}")

    def predict(self, Xc, yc, Xq):
        P = np.zeros((len(Xq), self.K))
        labs = np.unique(yc)
        if len(labs) == 1:
            P[:, labs[0]] = 1.0
            return P
        if BB in TABPFN:
            self.m.fit(Xc, yc)
            P[:, self.m.classes_.astype(int)] = self.m.predict_proba(Xq)
        else:
            yr = np.searchsorted(labs, yc)                                    # labels 0..k-1; columns follow labs
            if BB == "tabdpt":
                self.m.fit(Xc, yr)
                p = self.m.ensemble_predict_proba(Xq, n_ensembles=N_EST, seed=self.seed)
            elif BB == "mitra2":
                # Mitra's preprocessing draws from the global random / np.random (feature mirroring, permutations)
                # and its interface no longer seeds them (AutoGluon >= 1.4). Each call seeds them with the backbone
                # seed, as TabPFN's fixed random_state does per fit, and restores the caller's state afterwards.
                import random, torch
                st = random.getstate(), np.random.get_state()
                with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
                    random.seed(self.seed); np.random.seed(self.seed); torch.manual_seed(self.seed)
                    try:
                        self.m.fit(Xc, yr)
                        p = self.m.predict_proba(Xq)
                    finally:
                        random.setstate(st[0]); np.random.set_state(st[1])
            else:
                p = self.m.predict(Xc, yr, Xq, task_type="Classification")
            p = np.asarray(p, dtype=float)
            assert p.shape == (len(Xq), len(labs)), (BB, p.shape, len(labs))
            assert np.allclose(p.sum(1), 1, atol=1e-4), (BB, "probabilities do not sum to 1")
            P[:, labs] = p
        self.calls += 1
        return P


_TFM0 = run.TFM          # TabPFN v2 of run.py: the reference of the smoke test (time rule of ACTIVATION)
run.TFM = TFM


def smoke(stream, B, n, out):
    """H800 smoke test (ACTIVATION "Extra backbones"): time per call and peak memory on n FIFO contexts of 1000 rows,
    under a per-process memory cap of P3_MEM_CAP_GB (28); predictions are discarded, no accuracy is computed.
    P3_BACKBONE = tabpfn_v2 measures the reference (run.py's TFM). An error (out of memory, class or feature count) is
    recorded with its message instead of a time."""
    import time, torch, traceback
    cap = float(os.environ.get("P3_MEM_CAP_GB", 28))
    torch.cuda.set_per_process_memory_fraction(min(1.0, cap * 2**30 / torch.cuda.get_device_properties(0).total_memory))
    z = np.load(f"{run.DATA}/{stream}.npz"); X, y = z["X"], z["y"].astype(int)
    rec = dict(backbone=BB or "tabpfn_v2", stream=stream, n_classes=int(len(np.unique(y))), n_features=int(X.shape[1]),
               mem_cap_gb=cap, gpu=torch.cuda.get_device_name(0), s_per_call=[], error=None)
    try:
        f = _TFM0(int(y.max()) + 1) if BB in ("", "tabpfn_v2") else TFM(int(y.max()) + 1)
        for t in range(1, n + 1):
            t0 = time.time(); Pq = f.predict(*run.fifo(X, y, t + 9, B, 1000), X[(t + 9) * B:(t + 10) * B])
            torch.cuda.synchronize()
            assert np.allclose(Pq.sum(1), 1, atol=1e-4), "probabilities do not sum to 1"
            rec["s_per_call"].append(time.time() - t0)
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"[:2000]; traceback.print_exc()
    rec["median_s_after_first"] = float(np.median(rec["s_per_call"][1:])) if len(rec["s_per_call"]) > 1 else None
    rec["peak_mem_gb"] = torch.cuda.max_memory_allocated() / 2**30
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(rec, open(out + ".tmp", "w"), indent=1); os.replace(out + ".tmp", out)
    print(json.dumps(rec))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--methods", nargs="+")
    ap.add_argument("--B", type=int, default=100); ap.add_argument("--out", default="../results_dev")
    ap.add_argument("--smoke", type=int, default=0, help="smoke test: number of calls; writes --smoke-out only")
    ap.add_argument("--smoke-out")
    a = ap.parse_args()
    if a.smoke:
        smoke(a.streams[0], a.B, a.smoke, a.smoke_out)
    else:
        os.makedirs(a.out, exist_ok=True)
        for s in a.streams:
            for meth in a.methods:
                run.run(s, meth, a.B, a.out)
