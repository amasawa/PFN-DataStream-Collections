"""Trained-expert baselines for recurring concepts, under the protocol of run.py (batches of B rows, batch t is predicted
before its labels arrive, batch 0 is warm-up and not scored). CPU only (stream venv).

mooe_<feat>_<I>_<c>_<g>   MOOE (Zhao, Cao, Wan, AAAI 2025), Algorithm 1 and Eqs. (4)-(10), extended to several classes
        the way the official MATLAB code treats the binary case (squared loss on linear outputs, here one output per
        class with one-hot targets, prediction = arg max):
        - K <= Kmax = 25 experts: K-1 static offline experts and one online expert trained by OGD, step
          c / (beta sqrt(t)) with beta = max ||z||^2 seen so far (the paper's D / sqrt(beta t));
        - meta expert: weighted average of the experts' parameters, exponential weights on the loss of each labelled
          row inside the online interval, nu = 4 sqrt(ln K / I), initial weights by priority, Eq. (7);
        - after I rows the interval becomes offline: its expert minimises the interval loss plus
          (g / 2) ||W - sum_k alpha_k W_k||^2 (Eq. 9, solved in closed form); queue of Kmax - 1 offline experts;
          the next online expert inherits the parameters (warm start).
        feat: lin = standardised inputs + bias; rff = 500 random Fourier features of the standardised inputs + bias
        (still linear in the parameters, so inside MOOE's assumptions). Inputs are standardised with the mean and
        standard deviation of the warm-up batch. Losses are clipped to [0, 1] for the meta expert (Assumption 3).
nse     Learn++.NSE (Elwell & Polikar, 2011), sigmoid parameters a = 0.5, b = 10, one CART per batch, no pruning.
Usage: python run_trained.py --streams s1 s2 --methods mooe_rff_100_0.1_0.1 nse --out dir"""
import argparse, os, time
import numpy as np

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


class MOOE:
    def __init__(self, d, C, I, c, g, kmax=25):
        self.I, self.c, self.g, self.kmax, self.C = I, c, g, kmax, C
        self.Woff = np.zeros((0, d, C))    # offline experts, oldest first (queue)
        self.Wo = np.zeros((d, C))         # online expert
        self.IZ, self.IY = [], []          # rows of the current online interval
        self.beta = 1e-12
        self._init_alpha()

    def _init_alpha(self):
        K = len(self.Woff) + 1
        k = np.arange(1, K + 1)
        self.alpha = (K + 1) / ((K + 1 - k) * (K + 2 - k) * K)   # Eq. (7): the online expert (k = K) has the largest
        self.nu = 4 * np.sqrt(np.log(max(K, 2)) / self.I)

    def _mix(self):
        return np.tensordot(self.alpha[:-1], self.Woff, 1) + self.alpha[-1] * self.Wo   # Eq. (6)

    def predict(self, Z):
        return (Z @ self._mix()).argmax(1)

    def learn(self, Z, y):
        Y = np.eye(self.C)[y]
        for z, t_ in zip(Z, Y):
            self.IZ.append(z); self.IY.append(t_)
            out = np.r_[np.einsum("d,kdc->kc", z, self.Woff), (z @ self.Wo)[None]]
            loss = np.clip(((out - t_) ** 2).sum(1) / 2, 0, 1)
            a = self.alpha * np.exp(-self.nu * loss)             # Eq. (8)
            self.alpha = a / a.sum()
            self.beta = max(self.beta, float(z @ z))             # smoothness of the squared loss: max ||z||^2
            self.Wo = self.Wo - self.c / (self.beta * np.sqrt(len(self.IZ))) * np.outer(z, out[-1] - t_)  # Eq. (10)
            if len(self.IZ) == self.I:                           # the interval becomes offline
                Zi, Yi = np.array(self.IZ), np.array(self.IY)
                n, d = Zi.shape
                Wk = np.linalg.solve(Zi.T @ Zi / n + self.g * np.eye(d), Zi.T @ Yi / n + self.g * self._mix())  # Eq. (9)
                self.Woff = np.r_[self.Woff, Wk[None]][-(self.kmax - 1):]
                self.IZ, self.IY = [], []
                self._init_alpha()


class NSE:
    def __init__(self, C, a=0.5, b=10):
        self.C, self.a, self.b, self.h, self.beta = C, a, b, [], []

    def _votes(self, X, w):
        V = np.zeros((len(X), self.C))
        for h, wk in zip(self.h, w):
            if wk > 0:
                V[np.arange(len(X)), h.predict(X).astype(int)] += wk
        return V

    def predict(self, X):
        return self._votes(X, self.w).argmax(1) if self.h else np.zeros(len(X), int)

    def learn(self, X, y):
        from sklearn.tree import DecisionTreeClassifier
        m = len(y)
        if self.h:
            wrong = self.predict(X) != y
            E = wrong.mean()
            D = np.where(wrong, 1.0, E) if 0 < E else np.ones(m)
            D = D / D.sum()
        else:
            D = np.ones(m) / m
        self.h.append(DecisionTreeClassifier(random_state=len(self.h)).fit(X, y))
        self.beta.append([])
        t = len(self.h)
        for k, h in enumerate(self.h):
            eps = float(D[h.predict(X) != y].sum())
            if k == t - 1 and eps > 0.5:        # new classifier worse than chance on its own batch: refit once
                self.h[k] = h = DecisionTreeClassifier(random_state=1000 + k, max_depth=3).fit(X, y)
                eps = float(D[h.predict(X) != y].sum())
            eps = min(eps, 0.5)
            self.beta[k].append(max(eps, 1e-6) / (1 - max(eps, 1e-6)))
        self.w = np.zeros(t)
        for k in range(t):
            bk = np.array(self.beta[k])                       # errors of classifier k since its creation
            om = 1 / (1 + np.exp(-self.a * (np.arange(len(bk)) + 1 - self.b)))   # sigmoid: recent errors weigh more
            om = om / om.sum()
            self.w[k] = np.log(1 / (om @ bk))


def features(kind, d, seed=0):
    if kind == "lin":
        return lambda Xs: np.c_[Xs, np.ones(len(Xs))]
    rng, D = np.random.default_rng(seed), int(kind[3:] or 500)   # rff = 500 features, rff2000 = 2000 features
    Om, ph = rng.normal(scale=np.sqrt(2 * (1.0 / d)), size=(d, D)), rng.uniform(0, 2 * np.pi, D)
    return lambda Xs: np.c_[np.sqrt(2 / D) * np.cos(Xs @ Om + ph), np.ones(len(Xs))]


def run(stream, method, B, out):
    dst = f"{out}/{stream}__{method}.npz"
    if os.path.exists(dst):
        return
    z = np.load(f"{DATA}/{stream}.npz"); X, y, concept = z["X"].astype(float), z["y"].astype(int), z["concept"]
    C, T = int(y.max()) + 1, len(y) // B
    acc, wt = np.full(T, np.nan), np.zeros(T)
    if method.startswith("mooe"):
        _, feat, I, c, g = method.split("_")
        mu, sd = X[:B].mean(0), X[:B].std(0) + 1e-6
        phi = features(feat, X.shape[1])
        Z = phi(np.clip((X[:T * B] - mu) / sd, -10, 10))
        m = MOOE(Z.shape[1], C, int(I), float(c), float(g))
    else:
        m, Z = NSE(C), X
    for t in range(T):
        t0 = time.time(); q = slice(t * B, (t + 1) * B)
        if t > 0:
            acc[t] = (m.predict(Z[q]) == y[q]).mean()
        m.learn(Z[q], y[q])
        wt[t] = time.time() - t0
    np.savez_compressed(dst, acc=acc, ll=np.full(T, np.nan), wt=wt, B=B, concept=concept, calls=0,
                        n_experts=len(m.Woff) + 1 if method.startswith("mooe") else len(m.h))
    print(stream, method, f"acc={np.nanmean(acc):.4f}", f"time={wt.sum():.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--methods", nargs="+")
    ap.add_argument("--B", type=int, default=100); ap.add_argument("--out", default="../results_trained_dev")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        for me in a.methods:
            run(s, me, a.B, a.out)
