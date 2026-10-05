"""Lists the withheld-class episodes of pre-registration 3 (see logs/EXPERIMENT_LOG.md): for every multi-class real
stream, every class c and event position (33% and 66% of the stream), the episode is kept if the 1000 rows after the
event contain at least 30 and at most 500 rows of class c and at least 5000 rows of other classes precede the event.
Prints one family string per line (nov:<stream>:<class>:<pos>). Uses labels only; no model is involved."""
import glob, os, numpy as np
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
for f in sorted(glob.glob(f"{D}/insects_*.npz")) + [f"{D}/covertype.npz"]:
    y = np.load(f)["y"].astype(int); name = os.path.basename(f)[:-4]
    for pos in (33, 66):
        e = int(len(y) * pos / 100)
        for c in range(int(y.max()) + 1):
            n = int((y[e:e + 1000] == c).sum())
            if 30 <= n <= 500 and (y[:e] != c).sum() >= 5000:
                print(f"nov:{name}:{c}:{pos}")
