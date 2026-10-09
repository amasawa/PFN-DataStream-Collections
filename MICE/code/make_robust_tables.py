"""Table rows for the boundary-robustness tests of the TKDE revision (round 4): 4.a misaligned schedules
(../results_paper/misaligned.csv) and 4.b fixed-length half-segment offset (../results_paper/offset.csv).
Writes ../overleaf/tkde/tab_misaligned_rows.tex and tab_offset_rows.tex. No number is typed by hand."""
import pandas as pd

TEX = "../overleaf/tkde"
COND = {"b700": "700", "b1300": "1\\,300", "bvar": "500--2\\,500"}


def misaligned():
    m = pd.read_csv("../results_paper/misaligned.csv")
    rows = []
    for cond in ("b700", "b1300", "bvar"):
        for nc in (30, 100):
            for r in m[(m.cond == cond) & (m.nc == nc)].sort_values("stream").itertuples():
                seed = r.stream.split("_s")[-1]
                rows.append(f"{COND[cond]} & {nc} & {seed} & {r.mice:.1f} & {r.ddm:.1f} & {r.fifo:.1f} & {r.winens:.1f} & "
                            f"{r.arch:.1f} & {r.d_ddm:+.2f} & {r.d_ddm_rec5:+.1f} & {r.d_arch:+.2f} \\\\")
        rows.append("\\addlinespace")
    rows[-1] = "\\midrule"
    rows.append(f"Mean & & & {m.mice.mean():.1f} & {m.ddm.mean():.1f} & {m.fifo.mean():.1f} & {m.winens.mean():.1f} & "
                f"{m.arch.mean():.1f} & {m.d_ddm.mean():+.2f} & {m.d_ddm_rec5.mean():+.1f} & {m.d_arch.mean():+.2f} \\\\")
    open(f"{TEX}/tab_misaligned_rows.tex", "w").write("\n".join(rows) + "\n")


def offset():
    o = pd.read_csv("../results_paper/offset.csv")
    rows = []
    for blk in (500, 2000):
        for nc in (30, 100):
            for r in o[(o.block == blk) & (o.nc == nc)].sort_values("seed").itertuples():
                rows.append(f"{blk} & {nc} & {r.seed} & {r.al_d_ddm:+.2f} & {r.off_d_ddm:+.2f} & {r.delta:+.2f} & "
                            f"{r.al_d_ddm_rec5:+.1f} & {r.off_d_ddm_rec5:+.1f} & {r.al_d_arch:+.2f} & {r.off_d_arch:+.2f} \\\\")
        rows.append("\\addlinespace")
    rows[-1] = "\\midrule"
    rows.append(f"Mean & & & {o.al_d_ddm.mean():+.2f} & {o.off_d_ddm.mean():+.2f} & {o.delta.mean():+.2f} & "
                f"{o.al_d_ddm_rec5.mean():+.1f} & {o.off_d_ddm_rec5.mean():+.1f} & {o.al_d_arch.mean():+.2f} & "
                f"{o.off_d_arch.mean():+.2f} \\\\")
    open(f"{TEX}/tab_offset_rows.tex", "w").write("\n".join(rows) + "\n")


if __name__ == "__main__":
    misaligned()
    offset()
    print(open(f"{TEX}/tab_misaligned_rows.tex").read())
    print(open(f"{TEX}/tab_offset_rows.tex").read())
