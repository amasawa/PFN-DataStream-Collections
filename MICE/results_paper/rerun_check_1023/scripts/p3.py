import glob, os, pickle, numpy as np, pandas as pd, reweight
m = lambda a: float(np.mean(list(a.values())))
kw = dict(outer="brier", scale=0.5, temper=True)
for D in ["results_heldout3_tabpfn35","results_heldout4_tabpfn35","results_heldout4_tabpfn35_e","results_heldout3_tabdpt","results_heldout4_tabdpt","results_heldout4_tabdpt_e","results_heldout3_tabicl","results_heldout4_tabicl"]:
    rows=[]
    for f in sorted(glob.glob(f"../{D}/*__micev1000_500.pkl")):
        s=os.path.basename(f).split("__")[0]; c=pickle.load(open(f,"rb"))
        r=dict(stream=s, mice=m(reweight.simulate2(c,**kw)))
        for b in ("fifo1000","ltm1000_75","ddm1000","winens1000"):
            g=f"../{D}/{s}__{b}.npz"; r[b.split("1000")[0]]=float(np.nanmean(np.load(g)["acc"])) if os.path.exists(g) else np.nan
        rows.append(r)
    a=pd.DataFrame(rows).set_index("stream"); base=[c for c in ("fifo","ltm","ddm","winens") if a[c].notna().all()]
    best=(a["mice"]>=a[base].max(1)).sum()
    print(f"{D:28s} n={len(a):2d} mean%", (100*a.mean()).round(2).to_dict(), f"| MICE best on {best}/{len(a)}", f"| MICE-FIFO min {100*(a.mice-a.fifo).min():+.2f}")
