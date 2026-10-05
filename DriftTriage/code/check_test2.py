"""Checks the stream hypotheses H1-H4 of the DriftTriage pre-registration (pre-registration 2, test seeds 20-29, frozen triage_np) exactly as written."""
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

sys.path.insert(0, ".")
from stream_eval import summarise

s = summarise("../results/stream_test2", 10)
s.to_csv("../results/stream_test2/summary.csv", index=False)
s["family"] = s.stream.str.replace(r"_s\d+$", "", regex=True)
pd.set_option("display.width", 220)
print(s.groupby(["family", "policy"]).mean(numeric_only=True).round(4).to_string())
p = s.pivot_table(index=["family", "stream"], columns="policy", values="acc")
for fam in ("sine2d", "lin"):
    x = p.loc[fam]
    print(f"H1 {fam}: mean triage-ddm = {(x.triage_np - x.ddm).mean():+.4f} (>= -0.003?)", (x.triage_np - x.ddm).mean() >= -0.003,
          f"wins {(x.triage_np > x.ddm).sum()}/{len(x)}")
r = s.set_index(["family", "stream", "policy"])
sd = s[(s.family == "sine2d")]
print("H2a sine2d resets after translate, triage:", sd[sd.policy == "triage_np"].resets_translate.tolist())
need = lambda pol: s[s.policy == pol][["resets_tilt", "resets_translate", "resets_novel"]].sum().sum()
print("H2b needless resets (tilt+translate+novel), triage vs ddm:", need("triage_np"), need("ddm"), need("triage_np") < need("ddm"))
a = s[(s.family == "sine2d")].pivot_table(index="stream", columns="policy", values="auroc_novel")
pv = wilcoxon(a.triage_np - a.ddm, alternative="greater").pvalue
print(f"H3 sine2d novel AUROC triage {a.triage_np.mean():.3f} vs ddm {a.ddm.mean():.3f}, Wilcoxon p={pv:.4f} (<0.05?)", pv < 0.05)
al = s[(s.family == "lin")].pivot_table(index="stream", columns="policy", values="auroc_novel")
print(f"   lin (no claim): triage {al.triage_np.mean():.3f} ddm {al.ddm.mean():.3f} fifo {al.fifo.mean():.3f}")
px = s[s.policy == "pxreset"]
print("H4a pxreset resets after tilt/translate:", px[["resets_tilt", "resets_translate"]].sum().tolist(), "after real:", px.resets_real.sum())
g = s.groupby("policy").acc_real.mean()
print("H4b acc after real drift: fifo", round(g.fifo, 3), "ltm", round(g.ltm, 3), "ddm", round(g.ddm, 3))
print("ablation, triage (v2, priority retention) - triage_np:", (p.triage - p.triage_np).groupby("family").mean().round(4).to_dict())
h = summarise("../results/stream_heldout", 10)
h = h.pivot_table(index="stream", columns="policy", values="acc") if len(h) else h
if len(h):
    print("held-out real streams\n", h.round(4).to_string())
    print("R1 triage_np - ddm:", (h.triage_np - h.ddm).round(4).to_dict(), "all >= -0.005:", bool(((h.triage_np - h.ddm) >= -0.005).all()))
    print("R2 triage - triage_np:", (h.triage - h.triage_np).round(4).to_dict())
