"""Confirmation set for MICE with detected segmentation (PLAN.md): nine 100,000-row segments of two real sources that
no method in this repository has loaded. Raw files in ~/pfn-runs/raw-newdata-20261017 (checksums in PLAN.md).

Bitcoin Heist (UCI 526): rows sorted by (year, day); within a day in a random order (default_rng(0) keys; the file
  lists all ransomware rows first, so file order within a day would put each day's ransomware rows first); label: white -> 0, any
  ransomware family -> 1; features length, weight, count, looped, neighbors, income (address, year and day dropped).
  Segments: the first 100,000 rows of each year 2013..2017 -> cc_btc_<year>.
CIC-IDS2017 (MachineLearningCSV.zip): the day files in capture order (Thursday: morning, afternoon; Friday: morning,
  PortScan, DDoS), rows in file order; Monday (benign only) is not used. Labels grouped into 9 classes (BENIGN, DoS,
  DDoS, PortScan, Bot, WebAttack, Patator, Infiltration, Heartbleed). Features: the 78 numeric columns minus the
  duplicate "Fwd Header Length.1" and minus the columns constant over the whole file set; +-inf and NaN -> 0.
  Segments: per day (Tue..Fri), the day's rows are cut into aligned 100,000-row blocks and the block with the largest
  min(#BENIGN, #non-BENIGN) is used (the most mixed block) -> cc_cic_<day>.
Supplementary (reported, not part of any hypothesis): PokerHand (MICE/data/external_cdd/poker.csv, the file of the
  held-out sets) rows [500k, 600k) and [600k, 700k), after the fourth held-out set ([300k, 500k)) -> cc_poker_f, _g.
Labels are re-indexed per segment to the classes present (as streams_heldout4.py). concept = -1 (unknown).
Writes <out>/cc_*.npz and <out>/cc_manifest[_<part>].csv; refuses to overwrite.
Usage: python make_streams.py <out dir> [main | poker]   (default main)"""
import os
import sys
import numpy as np, pandas as pd

RAW = os.path.expanduser("~/pfn-runs/raw-newdata-20261017")
N = 100_000
GROUP = {"BENIGN": "BENIGN", "DDoS": "DDoS", "PortScan": "PortScan", "Bot": "Bot", "Infiltration": "Infiltration",
         "Heartbleed": "Heartbleed", "FTP-Patator": "Patator", "SSH-Patator": "Patator"}
DAYS = {"tue": ["Tuesday-WorkingHours"], "wed": ["Wednesday-workingHours"],
        "thu": ["Thursday-WorkingHours-Morning-WebAttacks", "Thursday-WorkingHours-Afternoon-Infilteration"],
        "fri": ["Friday-WorkingHours-Morning", "Friday-WorkingHours-Afternoon-PortScan",
                "Friday-WorkingHours-Afternoon-DDos"]}
ALL_DAYS = ["Monday-WorkingHours"] + sum(DAYS.values(), [])


def group(lbl):
    lbl = lbl.strip()
    if lbl.startswith("DoS"):
        return "DoS"
    if lbl.startswith("Web Attack"):
        return "WebAttack"
    return GROUP[lbl]


def bitcoin():
    d = pd.read_csv(f"{RAW}/BitcoinHeistData.csv")
    d["key"] = np.random.default_rng(0).random(len(d))
    d = d.sort_values(["year", "day", "key"]).reset_index(drop=True)
    feats = ["length", "weight", "count", "looped", "neighbors", "income"]
    for yr in range(2013, 2018):
        s = d[d.year == yr].iloc[:N]
        assert len(s) == N, (yr, len(s))
        yield f"cc_btc_{yr}", s[feats].to_numpy(np.float32), (s.label != "white").astype(int).to_numpy(), \
            dict(source="bitcoinheist", rows=f"year {yr}, first {N} rows after the (year, day, random) sort", days=f"{s.day.min()}-{s.day.max()}")


def cic():
    files = {f: pd.read_csv(f"{RAW}/cic/MachineLearningCVE/{f}.pcap_ISCX.csv", low_memory=False) for f in ALL_DAYS}
    for f in files.values():
        f.columns = f.columns.str.strip()
    feats = [c for c in files[ALL_DAYS[0]].columns if c not in ("Label", "Fwd Header Length.1")]
    allx = pd.concat([files[f][feats] for f in ALL_DAYS]).replace([np.inf, -np.inf], np.nan).fillna(0)
    feats = [c for c in feats if allx[c].nunique() > 1]
    del allx
    for day, fs in DAYS.items():
        d = pd.concat([files[f] for f in fs], ignore_index=True)
        mal = (d.Label.str.strip() != "BENIGN").to_numpy()
        nb = len(d) // N
        mixed = [min(mal[i * N:(i + 1) * N].sum(), N - mal[i * N:(i + 1) * N].sum()) for i in range(nb)]
        i = int(np.argmax(mixed)); s = d.iloc[i * N:(i + 1) * N]
        X = s[feats].replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy(np.float64)
        assert np.isfinite(X).all() and np.abs(X).max() < 3e38
        yield f"cc_cic_{day}", X.astype(np.float32), s.Label.map(group).to_numpy(), \
            dict(source="cicids2017", rows=f"{day} block {i} of {nb} (rows {i * N}-{(i + 1) * N}), mixed counts {mixed}",
                 days=day)


def poker():
    df = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "data", "external_cdd", "poker.csv"))
    X, t = df.drop(columns="target").to_numpy(np.float32), df.target.to_numpy()
    for tag, lo in (("f", 500_000), ("g", 600_000)):
        yield f"cc_poker_{tag}", X[lo:lo + N], t[lo:lo + N], dict(source="poker", rows=f"rows {lo}-{lo + N}", days="")


def main():
    out = sys.argv[1]
    part = sys.argv[2] if len(sys.argv) > 2 else "main"
    os.makedirs(out, exist_ok=True)
    man = []
    for name, X, t, info in (list(bitcoin()) + list(cic()) if part == "main" else list(poker())):
        dst = f"{out}/{name}.npz"
        assert not os.path.exists(dst), dst
        labs = sorted(set(t.tolist())); y = np.array([labs.index(v) for v in t.tolist()])
        np.savez_compressed(dst, X=X, y=y, concept=np.full(len(y), -1))
        cnt = np.bincount(y)
        man.append(dict(stream=name, n=len(y), features=X.shape[1], classes=len(labs), labels="|".join(map(str, labs)),
                        majority=cnt.max() / len(y), counts="|".join(map(str, cnt)), **info))
        print(man[-1], flush=True)
    pd.DataFrame(man).to_csv(f"{out}/cc_manifest{'' if part == 'main' else '_' + part}.csv", index=False)


if __name__ == "__main__":
    main()
