"""Additional independent real streams (selection rule and preprocessing written before download: logs/EXPERIMENT_LOG.md,
2026-10-06 23:09). Raw files in ../data/_raw (UCI 224, 357, 864, 222; KDD Cup 99 10% via sklearn). Each stream: time
order, first CAP rows, categorical columns as integer codes, time columns used only for ordering, labels numbered in
sorted order. Written to ../data/<name>.npz with X (float32), y (int), concept (-1) as MICE/code/streams.py.
Excluded before any model is run if the majority-class rate is >= 0.98. A sliding random forest (previous 1000 rows)
against the majority rate is printed as a description only (as MICE/code/streams_heldout2.py).
Round 2 (logs, 2026-10-06 23:25): eeg, news, home, wall, chest.
Usage: python streams_new.py [round]"""
import glob
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
RAW = f"{D}/_raw"
CAP = 100_000


def gas():
    rows = []
    for b in range(1, 11):                                            # batches 1..10 span 36 months
        for line in open(f"{RAW}/gas/Dataset/batch{b}.dat"):
            tok = line.split()
            x = np.zeros(128)
            for kv in tok[1:]:
                k, v = kv.split(":"); x[int(k) - 1] = float(v)
            rows.append((int(tok[0].split(";")[0]), x))
    return pd.DataFrame([r[1] for r in rows]), pd.Series([r[0] for r in rows])


def occupancy():
    df = pd.concat([pd.read_csv(f"{RAW}/occ/{f}") for f in ("datatraining.txt", "datatest.txt", "datatest2.txt")])
    df = df.assign(date=pd.to_datetime(df.date)).sort_values("date", kind="stable")
    return df.drop(columns=["date", "Occupancy"]), df.Occupancy


def room():
    df = pd.read_csv(f"{RAW}/room/Occupancy_Estimation.csv")
    df = df.assign(ts=pd.to_datetime(df.Date + " " + df.Time, format="%Y/%m/%d %H:%M:%S")).sort_values("ts", kind="stable")
    return df.drop(columns=["Date", "Time", "ts", "Room_Occupancy_Count"]), df.Room_Occupancy_Count


def bank():
    df = pd.read_csv(f"{RAW}/bank/bank-additional/bank-additional/bank-additional-full.csv", sep=";")  # file is in date order
    return df.drop(columns=["y", "duration"]), df.y


KDD = {"normal": "normal", **{a: "dos" for a in ("back", "land", "neptune", "pod", "smurf", "teardrop")},
       **{a: "probe" for a in ("ipsweep", "nmap", "portsweep", "satan")},
       **{a: "r2l" for a in ("ftp_write", "guess_passwd", "imap", "multihop", "phf", "spy", "warezclient", "warezmaster")},
       **{a: "u2r" for a in ("buffer_overflow", "loadmodule", "perl", "rootkit")}}


def kdd():
    from sklearn.datasets import fetch_kddcup99
    df = fetch_kddcup99(percent10=True, data_home=f"{RAW}/kdd", as_frame=True).frame       # file order
    y = df.labels.map(lambda b: KDD[b.decode().rstrip(".")])
    X = df.drop(columns="labels")
    for c in X.columns:
        if X[c].dtype == object:
            X[c] = X[c].map(lambda v: v.decode() if isinstance(v, bytes) else v)
    return X, y


def eeg():
    lines = [l for l in open(f"{RAW}/eeg/EEG Eye State.arff") if l.strip() and not l.startswith("@")]
    a = np.array([[float(v) for v in l.strip().split(",")] for l in lines])          # file order = time order
    return pd.DataFrame(a[:, :-1]), pd.Series(a[:, -1].astype(int))


def news():
    df = pd.read_csv(f"{RAW}/news/OnlineNewsPopularity/OnlineNewsPopularity.csv", skipinitialspace=True)
    df = df.sort_values("timedelta", ascending=False, kind="stable")                    # oldest article first
    return df.drop(columns=["url", "timedelta", "shares"]), (df.shares >= 1400).astype(int)


def home():
    meta = pd.read_csv(f"{RAW}/home/HT_Sensor_metadata.dat", sep=r"\s+")
    meta["day"] = pd.to_datetime(meta.date, format="%m-%d-%y")
    df = pd.read_csv(f"{RAW}/home/HT_Sensor_dataset/HT_Sensor_dataset.dat", sep=r"\s+")
    df = df.merge(meta[["id", "class", "day", "t0", "dt"]], on="id")
    df = df.sort_values(["day", "t0", "id", "time"], kind="stable")                    # recordings in calendar order
    on = (df.time >= 0) & (df.time <= df.dt)                                            # stimulus present
    y = np.where(on, df["class"], "background")
    return df[["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "Temp.", "Humidity"]], pd.Series(y)


def wall():
    df = pd.read_csv(f"{RAW}/wall/sensor_readings_24.data", header=None)              # recording order
    return df.iloc[:, :-1], df.iloc[:, -1]


def chest():
    d = f"{RAW}/chest/Activity Recognition from Single Chest-Mounted Accelerometer"
    df = pd.concat([pd.read_csv(f"{d}/{i}.csv", header=None) for i in range(1, 16)], ignore_index=True)
    df = df[df[4] != 0]                                                                  # 0 = unlabelled
    return df[[1, 2, 3]], df[4]


def encode(X):
    X = X.copy()
    for c in X.columns:
        if not pd.api.types.is_numeric_dtype(X[c]):
            X[c] = X[c].astype(str).astype("category").cat.codes
    return X.to_numpy(np.float32)


ROUNDS = {1: (("gas", gas), ("occupancy", occupancy), ("room", room), ("bank", bank), ("kdd", kdd)),
          2: (("eeg", eeg), ("news", news), ("home", home), ("wall", wall), ("chest", chest))}


def main(rnd):
    for name, f in ROUNDS[rnd]:
        X, y = f()
        X, y = encode(X.iloc[:CAP]), y.iloc[:CAP]
        labs = sorted(y.unique()); y = y.map({l: i for i, l in enumerate(labs)}).to_numpy()
        maj_all = np.bincount(y).max() / len(y)
        if maj_all >= 0.98:
            print(f"{name}: EXCLUDED, majority-class rate {maj_all:.3f} >= 0.98", flush=True); continue
        np.savez_compressed(f"{D}/{name}.npz", X=X, y=y, concept=np.full(len(y), -1))
        T = len(y) // 100; rf, maj = [], []
        for t in range(10, T, max(1, T // 40)):
            a, b = slice(max(0, t * 100 - 1000), t * 100), slice(t * 100, (t + 1) * 100)
            rf.append((RandomForestClassifier(100, random_state=0, n_jobs=8).fit(X[a], y[a]).predict(X[b]) == y[b]).mean())
            maj.append((np.bincount(y[a]).argmax() == y[b]).mean())
        print(f"{name}.npz", X.shape, "classes", len(labs), "counts", np.bincount(y).tolist(), "NaN", int(np.isnan(X).sum()),
              f"majority rate {maj_all:.3f}; sliding RF {np.mean(rf):.3f} vs sliding majority {np.mean(maj):.3f}", flush=True)


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
