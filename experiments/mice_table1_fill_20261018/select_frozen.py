"""Frozen configuration of a Table 1 baseline from its development grid (PLAN_BASELINES.md, "Tuning"; amendment c):
highest mean development accuracy over the five development streams (accuracy of a stream = mean over its scored
batches), ties to the first configuration in sorted order of (L, lr, steps, mech). Boundary rule: if the best lies on
the boundary of lr (1e-4 or 1e-2) or n_steps (5; 1 is the smallest possible value), the grid is extended once and the
selection is redone on the extended grid. A configuration with a missing development stream is not eligible.
Writes <out>/frozen_<method>.json (scores of every configuration, the choice, the extension needed). Never reads a
test stream. With --final (after the one extension, AMENDMENT_BASELINES_20261018c.md): the configurations outside the
original grid are added; ties go to the original grid first, then to the added configurations, each in ascending
(L, lr, steps, mech); the re-selected best is frozen even if it lies on a boundary (no second extension); writes
<out>/frozen_<method>_final.json. Usage: python select_frozen.py <dev P dir> <method> <out dir> [--final]"""
import glob, json, os, re, sys
import numpy as np

DEV = ["elec2", "insects_abrupt_balanced", "insects_gradual_balanced", "insects_incremental_balanced",
       "insects_incremental_reoccurring_balanced"]
P, method, out = sys.argv[1:4]; final = "--final" in sys.argv
flags = glob.glob(f"{P}/UNVERIFIED*") + glob.glob(f"{P}/../UNVERIFIED*") + glob.glob(f"{P}/../../UNVERIFIED*")
if flags:                                                # amendment d item 7: nothing is selected from flagged outputs
    sys.exit(f"{method}: outputs flagged unverified ({flags}): not selecting")
GRID = {"lr": (1e-4, 1e-3, 1e-2), "steps": (1, 5)}         # the registered grid (L and mech: all their values)
pat = re.compile(rf"^(?P<s>.+)__{method}_L(?P<L>\d+)_lr(?P<lr>[0-9.e-]+)_s(?P<st>\d+)(_m(?P<m>[0-9.e-]+))?\.npz$")
acc = {}
for f in glob.glob(f"{P}/*__{method}_*.npz"):
    g = pat.match(os.path.basename(f))
    if not g or g["s"] not in DEV:
        continue
    cfg = (int(g["L"]), float(g["lr"]), int(g["st"]), None if g["m"] is None else float(g["m"]))
    acc.setdefault(cfg, {})[g["s"]] = float(np.nanmean(np.load(f)["acc"]))
MECH = {"dtmoe": (2.0,)}.get(method)   # AMENDMENT_20261020c (clean rerun): dtmoe only at its default drift_k_sigma 2
if MECH is not None:
    acc = {c: d for c, d in acc.items() if c[3] in MECH}
N_CFG = 2 * (len(MECH) if MECH is not None else 3)   # registered L (2 values) x mech values
added = lambda c: c[1] not in GRID["lr"] or c[2] not in GRID["steps"]
if not final:
    acc = {c: d for c, d in acc.items() if not added(c)}
rows = sorted(((cfg, d) for cfg, d in acc.items()), key=lambda r: (added(r[0]), r[0]))
eligible = [(cfg, float(np.mean([d[s] for s in DEV]))) for cfg, d in rows if all(s in d for s in DEV)]
if not final and (len(eligible) != 6 * N_CFG or len(rows) != 6 * N_CFG):   # the registered grid must be complete
    sys.exit(f"{method}: {len(eligible)} complete of {len(rows)} configurations, {6 * N_CFG} expected: not selecting")
if final:   # amendment c: the extended grid must be complete, nothing missing; expected count from the extension
    e = json.load(open(f"{out}/frozen_{method}.json"))["boundary_extension_needed"]
    n_cfg = N_CFG                                       # registered L (2 values) x mech values
    nl, ns = len(GRID["lr"]) + ("lr" in e), len(GRID["steps"]) + ("steps" in e)
    want = nl * ns * n_cfg
    if len(eligible) != want or len(eligible) != len(rows):
        sys.exit(f"{method}: {len(eligible)} complete of {len(rows)} configurations, {want} expected: not selecting")
best = max(eligible, key=lambda r: r[1])          # max keeps the first of equal values: the order above breaks ties
cfg = best[0]
lrs = sorted({c[1] for c, _ in eligible}); steps = sorted({c[2] for c, _ in eligible})
ext = {}
if final:
    pass                                            # no second extension; a boundary best is frozen as it is
elif cfg[1] == min(lrs):
    ext["lr"] = cfg[1] / 10
elif cfg[1] == max(lrs):
    ext["lr"] = cfg[1] * 10
if not final and cfg[2] == max(steps):
    ext["steps"] = 25
res = dict(method=method, dev_streams=DEV, n_configs=len(rows), n_eligible=len(eligible),
           scores=[dict(L=c[0], lr=c[1], steps=c[2], mech=c[3], mean_dev_acc=m) for c, m in eligible],
           incomplete=[dict(L=c[0], lr=c[1], steps=c[2], mech=c[3], streams=sorted(d)) for c, d in rows if len(d) < len(DEV)],
           best=dict(L=cfg[0], lr=cfg[1], steps=cfg[2], mech=cfg[3], mean_dev_acc=best[1]),
           boundary_extension_needed=ext, final=final,
           best_on_boundary=dict(lr=cfg[1] in (min(lrs), max(lrs)), steps=cfg[2] == max(steps)),
           outside_registered_grid=dict(lr=cfg[1] not in GRID["lr"], steps=cfg[2] not in GRID["steps"]))
os.makedirs(out, exist_ok=True)
json.dump(res, open(f"{out}/frozen_{method}{'_final' if final else ''}.json", "w"), indent=1)
print(method, "best", res["best"], "extension", ext or "none", f"({len(eligible)} eligible / {len(rows)})")
