"""Round-9 benchmark analysis (registered in PLAN.md, "Round 9 addition"; 28 GB cap correction recorded before
resuming). Stage "cost" reads only timings and memory and fixes M* by rule B; stage "accuracy" (run only after M* is
written) adds the paired accuracies on the same prefixes and the bit-identity check of MICE's expert predictions.
Usage: python analyse_bench.py <bench root> cost|accuracy"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "MICE/code"))
POL = ["micev1000_500", "fifo1000", "fifo1500", "fifo2000", "fifo3000", "fifo5000", "fifo13400", "winens1000"]
STREAMS = ["h4_airlines_d", "h4_covertype_d", "insects_abrupt_balanced"]
FROZEN = {"h4_airlines_d": "results_heldout4", "h4_covertype_d": "results_heldout4", "insects_abrupt_balanced": "results_test"}


def records(root):
    recs = [json.loads(l) for l in open(root / "bench.jsonl")]
    disc = {(r["discarded"]["rep"], r["discarded"]["policy"], r["discarded"]["stream"], ) for r in recs if "discarded" in r}
    out = {}
    for i, r in enumerate(recs):
        if "policy" in r and r["ok"]:
            k = (r["rep"], r["policy"], r["stream"])
            if k in disc and r.get("peak_reserved_mib", 0) > 28672:
                continue                      # the discarded oversubscribed run
            out[k] = r
    return out


def cost(root):
    rec = records(root)
    rows = []
    for (rep, pol, s), r in rec.items():
        z = np.load(root / f"rep{rep}" / f"{s}__{pol}.npz")
        wt = z["wt"][1:]
        row = dict(rep=rep, policy=pol, stream=s, mean_s=wt.mean(), median_s=np.median(wt), p95_s=np.percentile(wt, 95),
                   max_s=wt.max(), rows_per_s=100 * len(wt) / wt.sum(), peak_alloc_mib=r["peak_alloc_mib"],
                   peak_reserved_mib=r["peak_reserved_mib"], peak_rss_mib=r["peak_rss_mib"], calls=float(z["calls"]))
        if pol.startswith("micev"):
            closing = np.array([(t * 100) % 500 == 0 for t in range(1, len(z["wt"]))])
            row["closing_mean_s"], row["nonclosing_mean_s"] = wt[closing].mean(), wt[~closing].mean()
            c = pickle.load(open(root / f"rep{rep}" / f"{s}__{pol}.pkl", "rb"))
            import time, reweight
            t0 = time.perf_counter(); reweight.simulate2(c, outer="brier", scale=0.5, temper=True)
            row["replay_s_per_batch"] = (time.perf_counter() - t0) / len(c["cache"])
            row["mean_s"] += row["replay_s_per_batch"]           # two-level rule amortised per batch
            row["pool_experts_mean"] = np.mean([sum(1 for u in st["P"] if u > 0) for st in c["cache"]])
        rows.append(row)
    d = pd.DataFrame(rows)
    per = d.groupby(["policy", "stream"]).mean(numeric_only=True).reset_index()
    agg = per.groupby("policy").mean(numeric_only=True).reindex(POL)
    pd.set_option("display.width", 250)
    print(agg[["mean_s", "median_s", "p95_s", "max_s", "rows_per_s", "peak_alloc_mib", "peak_reserved_mib", "peak_rss_mib"]].round(3))
    mice = agg.loc["micev1000_500", "mean_s"]
    cand = {m: agg.loc[f"fifo{m}", "mean_s"] for m in (1500, 2000, 3000)}
    within = {m: v for m, v in cand.items() if 1 / 1.25 <= v / mice <= 1.25}
    pick = min(within or cand, key=lambda m: abs(np.log(cand[m] / mice)))
    status = "matched (within 1.25)" if within else "bracketing (none within 1.25)"
    print(f"MICE amortised mean s/batch {mice:.3f}; candidates {({m: round(v, 3) for m, v in cand.items()})}; "
          f"M* = {pick} ({status})")
    d.to_csv(root / "bench_cost_runs.csv", index=False); agg.to_csv(root / "bench_cost_policy.csv")
    json.dump(dict(M_star=pick, status=status, mice_mean_s=mice, candidates=cand), open(root / "m_star.json", "w"), indent=1)


def accuracy(root):
    assert (root / "m_star.json").exists(), "fix M* first"
    import reweight
    rec = records(root); rows = []
    for (rep, pol, s) in rec:
        if pol.startswith("micev"):
            c = pickle.load(open(root / f"rep{rep}" / f"{s}__{pol}.pkl", "rb"))
            a = reweight.simulate2(c, outer="brier", scale=0.5, temper=True); acc = 100 * np.mean([a[k] for k in sorted(a)])
            fz = pickle.load(open(REPO / "MICE" / FROZEN[s] / f"{s}__micev1000_500.pkl", "rb"))
            same = all(st["t"] == sf["t"] and st["P"].keys() == sf["P"].keys() and
                       all(np.array_equal(st["P"][k], sf["P"][k]) for k in st["P"]) for st, sf in zip(c["cache"], fz["cache"]))
        else:
            acc = 100 * np.nanmean(np.load(root / f"rep{rep}" / f"{s}__{pol}.npz")["acc"][1:]); same = None
        rows.append(dict(rep=rep, policy=pol, stream=s, acc=acc, identical_to_frozen=same))
    d = pd.DataFrame(rows)
    print("MICE expert predictions identical to frozen cache:", d[d.policy.str.startswith("micev")].identical_to_frozen.all())
    print(d.groupby(["policy", "stream"]).acc.mean().unstack().reindex(POL).round(2))
    d.to_csv(root / "bench_accuracy_runs.csv", index=False)


if __name__ == "__main__":
    root = Path(sys.argv[1])
    cost(root) if sys.argv[2] == "cost" else accuracy(root)
