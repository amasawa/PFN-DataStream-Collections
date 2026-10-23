import csv, re, sys
D = "/private/tmp/claude-501/-Users-amasawa-Desktop-SynologyDrive-Short-MICE/8d20b900-e4ef-44b2-8897-4ae00b51e988/scratchpad"
import sys; TAB = sys.argv[1]
S = {(r["set"], r["method"]): r for r in csv.DictReader(open(f"{D}/sum2.csv"))}
KEY = {"ARF": "arf", "SRP": "srp", "HAT": "hat", "Leveraging Bagging": "levbag", "ADWIN Bagging": "adwinbag",
       "Learn++.NSE": "nse", "MOOE, 2000 features": "mooe_rff2000_100_2_0.01",
       "MOOE, 4000 features": "mooe_rff4000_100_2_0.01", "Fast level only": "fast",
       r"\method{} (detected segments)": "mice_cp", r"\method{}, fixed segments, $\eta_2=10$": "mice10"}
COLS = [("real", k) for k in ("acc", "f1", "auc", "ece", "brier")] + [("real", "worst")] + \
       [("grid", k) for k in ("acc", "f1", "auc", "ece", "brier")] + [("generator", "acc"), ("confirm", "acc")]
LOW = {4, 5, 10, 11}
SH = ["\\first", "\\second", "\\third"]


def strip(c):
    c = c.strip()
    for s in SH:
        if c.startswith(s + "{") and c.endswith("}"):
            return c[len(s) + 1:-1]
    return c


def num(c):
    try:
        return float(c.replace("$-$", "-").replace("$^\\dagger$", ""))
    except ValueError:
        return None


lines = open(TAB).read().split("\n")
out, rows, filled = [], [], 0
for L in lines:
    if "&" not in L:
        out.append(L); continue
    cells = [c.strip() for c in L.strip().removesuffix("\\\\").split("&")]
    name = re.sub(r"~\\citep\{[^}]*\}", "", cells[0]).strip()
    m = KEY.get(name)
    for i, (st, k) in enumerate(COLS, 1):
        c = strip(cells[i])
        if m and (c == "--" or "dagger" in c):
            r = S.get((st, m))
            v = r and (r["worst_vs_fifo"] if k == "worst" else r[k])
            if v not in (None, "", "nan"):
                x = float(v)
                c = (f"$-${abs(x):.1f}" if x < 0 else f"{x:.1f}") if k == "worst" else f"{x:.{2 if st == 'confirm' else 1}f}"
                filled += 1
        cells[i] = c
    rows.append(len(out)); out.append(cells)
grid = [out[i] for i in rows]
for j in range(1, 14):
    vals = sorted({num(g[j]) for g in grid if num(g[j]) is not None and "dagger" not in g[j]}, reverse=j not in LOW)[:3]
    for g in grid:
        v = num(g[j])
        if v is not None and "dagger" not in g[j] and v in vals:
            g[j] = SH[vals.index(v)] + "{" + g[j] + "}"
for i in rows:
    out[i] = " & ".join(out[i]) + " \\\\"
if True:
    open(TAB, "w").write("\n".join(out))
print("filled", filled)
print("\n".join(out))
