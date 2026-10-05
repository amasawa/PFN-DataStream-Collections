"""Checks pre-registration 3 (withheld-class episodes on real streams) exactly as written in the log. Written before
any episode was run."""
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
from stream_eval import summarise

s = summarise("../results/stream_novel", 10)
s.to_csv("../results/stream_novel/summary.csv", index=False)
s["src"] = s.stream.str.extract(r"nov-(.*)-\d+-\d+_s0")[0]
pd.set_option("display.width", 220)
cols = ["auroc_novel", "resets_novel", "acc_novel", "acc"]
print("episodes per policy:", s.groupby("policy").size().to_dict())
print("mean over episodes\n", s.groupby("policy")[cols].mean().round(4).to_string())
print("mean of per-stream means\n", s.groupby(["policy", "src"])[cols].mean().groupby("policy").mean().round(4).to_string())
a = s.pivot_table(index="stream", columns="policy", values="auroc_novel").dropna()
src = a.index.str.extract(r"nov-(.*)-\d+-\d+_s0")[0].values
for b in ("ddm", "fifo", "pxreset"):
    d = a.triage_np - a[b]; ps = d.groupby(src).mean()
    print(f"N1/N2 AUROC triage_np - {b}: mean {d.mean():+.4f}, wins {(d > 0).sum()}/{len(d)}, Wilcoxon two-sided p={wilcoxon(d).pvalue:.4f}; "
          f"per stream: positive on {(ps > 0).sum()}/{len(ps)} streams, {ps.round(3).to_dict()}")
r = s.pivot_table(index="stream", columns="policy", values="resets_novel")
print("N3 resets in the 10 batches after the event (sum over episodes):", r.sum().to_dict())
c = s.pivot_table(index="stream", columns="policy", values="acc_novel")
print("N4 accuracy in the 10 batches after the event, triage_np - ddm: mean %+.4f (>= -0.005?)" % (c.triage_np - c.ddm).mean(),
      "; triage_np - fifo: %+.4f" % (c.triage_np - c.fifo).mean())
