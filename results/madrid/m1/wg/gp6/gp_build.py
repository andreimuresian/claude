"""Madrid 1 GP surrogate: 6 geometry inputs (incl. rib width WG) -> log10(IL) and Vpi*L.
Run: python3 gp_build.py   (reads ../sweep_gp.txt, writes models/, metrics, parity plots)
Design choices (see deck): inputs scaled to [0,1] on the design bounds; CAP_W enters as the margin fraction
f = (GAP - CAP_W)/(GAP - 2.8) so the domain is a box; Matern-5/2 ARD + white noise, optionally on top of a
linear mean (GP on residuals of a least-squares plane); 10-fold CV with all scaling refitted inside folds."""
import json, hashlib, pickle, time, warnings
import numpy as np, sklearn
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, RBF, ConstantKernel as C, WhiteKernel
from sklearn.model_selection import KFold
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

NAMES = ["GAP", "BUFFER_H", "CAP_F", "CAP_H", "MTX_SMALL", "WG"]
UNITS = ["um", "um", "-", "um", "um", "um"]
LO = np.array([3.0, 0.05, 0.0, 0.5, 0.5, 1.0]); HI = np.array([4.5, 0.20, 1.0, 1.4, 1.0, 1.5])
CAPW_MIN = 2.8

PATHS = ["../../sweep_gp.txt", "../sweep_wg.txt"]
def capf(g, cw, wg):
    d = g - 2 * wg
    return 0.0 if d < 1e-6 else (g - cw) / d
def load(paths=PATHS):
    R, seen = [], set()
    for path in paths:
        for l in open(path):
            if not l.startswith("RESULT"): continue
            r = json.loads(l[7:]); r.setdefault("wg", 1.4); k = (r["gap"], r["buf"], r["cap_w"], r["cap_h"], r["mtx_small"], r["wg"])
            if k in seen: continue
            seen.add(k); R.append(r)
    X = np.array([[r["gap"], r["buf"], capf(r["gap"], r["cap_w"], r["wg"]), r["cap_h"], r["mtx_small"], r["wg"]] for r in R])
    IL = np.array([r["IL_dBcm"] for r in R]); V = np.array([r["VpiL_Vcm"] for r in R])
    return R, np.clip(X, LO, HI), IL, V

def u(X): return (X - LO) / (HI - LO)

def kernel(kind, d=6):
    ls = dict(length_scale=np.ones(d), length_scale_bounds=(1e-2, 1e2))
    base = Matern(nu=2.5, **ls) if kind == "m52" else Matern(nu=1.5, **ls) if kind == "m32" else RBF(**ls)
    return C(1.0, (1e-3, 1e3)) * base + WhiteKernel(1e-5, (1e-9, 1e-3))

class Model:
    """target transform t(y); optional linear mean; standardised residual GP."""
    def __init__(self, kind="m52", linmean=True, log=True, restarts=10):
        self.kind, self.linmean, self.log, self.restarts = kind, linmean, log, restarts
    def fit(self, X, y):
        Z = u(X); t = np.log10(y) if self.log else y.copy()
        A = np.c_[np.ones(len(Z)), Z]
        self.beta = np.linalg.lstsq(A, t, rcond=None)[0] if self.linmean else np.r_[t.mean(), np.zeros(Z.shape[1])]
        r = t - A @ self.beta; self.mu, self.sd = r.mean(), r.std() or 1.0
        self.gp = GaussianProcessRegressor(kernel(self.kind), n_restarts_optimizer=self.restarts, random_state=0, normalize_y=False)
        self.gp.fit(Z, (r - self.mu) / self.sd); return self
    def predict_t(self, X):
        Z = u(X); m, s = self.gp.predict(Z, return_std=True)
        return np.c_[np.ones(len(Z)), Z] @ self.beta + self.mu + self.sd * m, self.sd * s
    def predict(self, X):
        t, s = self.predict_t(X)
        return (10 ** t if self.log else t), t, s

def cv(X, y, **kw):
    kf = KFold(10, shuffle=True, random_state=1); tp = np.zeros_like(y); sp = np.zeros_like(y)
    for tr, te in kf.split(X):
        m = Model(restarts=3, **kw).fit(X[tr], y[tr]); _, tp[te], sp[te] = m.predict(X[te])
    t = np.log10(y) if kw.get("log", True) else y
    yp = 10 ** tp if kw.get("log", True) else tp
    res = t - tp
    return dict(R2_t=1 - np.sum(res ** 2) / np.sum((t - t.mean()) ** 2), R2_phys=1 - np.sum((y - yp) ** 2) / np.sum((y - y.mean()) ** 2),
                MAE=float(np.mean(np.abs(y - yp))), MAPE_pct=float(100 * np.mean(np.abs(y - yp) / y)), maxAPE_pct=float(100 * np.max(np.abs(y - yp) / y)),
                cover95_pct=float(100 * np.mean(np.abs(res) <= 1.96 * sp))), yp

if __name__ == "__main__":
    R, X, IL, V = load(); n = len(R); print("samples", n)
    sha = hashlib.sha256(b"".join(open(p, "rb").read() for p in PATHS)).hexdigest()[:16]
    cands = {"IL": [dict(kind=k, linmean=lm, log=True) for k in ("m52", "m32", "rbf") for lm in (True, False)],
             "VpiL": [dict(kind=k, linmean=lm, log=lg) for k in ("m52", "m32", "rbf") for lm in (True, False) for lg in (True, False)]}
    Y = {"IL": IL, "VpiL": V}; report = {}; best = {}
    for tgt in ("IL", "VpiL"):
        rows = []
        for kw in cands[tgt]:
            met, yp = cv(X, Y[tgt], **kw); rows.append((kw, met, yp))
            print(tgt, kw, {k: round(v, 4) for k, v in met.items()})
        ok = [r for r in rows if r[1]["cover95_pct"] >= 85] or rows   # calibrated uncertainty first, then accuracy
        kw, met, yp = min(ok, key=lambda r: r[1]["MAPE_pct"])
        best[tgt] = (kw, met, yp); report[tgt] = dict(candidates=[dict(cfg=r[0], **r[1]) for r in rows], chosen=kw, chosen_cv=met)
    Path = __import__("pathlib").Path; Path("models").mkdir(exist_ok=True)
    card = dict(created=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), dataset="results/madrid/m1/sweep_gp.txt + results/madrid/m1/wg/sweep_wg.txt", dataset_sha256_16=sha,
                n_samples=n, sklearn=sklearn.__version__, wavelength_nm=1625, inputs=NAMES, units=UNITS, lo=LO.tolist(), hi=HI.tolist(),
                capw_min_rule="CAP_W >= 2*WG", cap_f_definition="CAP_F = (GAP - CAP_W) / (GAP - 2*WG); CAP_W = GAP - CAP_F*(GAP-2*WG)",
                fixed=dict(signal="10 x 10 um", ground_tongue_w=10, ground_tall="10 x 10 um", film=0.55, etch=0.275, ald=0), outputs={})
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
    for i, tgt in enumerate(("IL", "VpiL")):
        kw, met, yp = best[tgt]; m = Model(restarts=25, **kw).fit(X, Y[tgt])
        pickle.dump(m, open(f"models/gp_{tgt}.pkl", "wb"))
        g = m.gp; k = g.kernel_; c = float(k.k1.k1.constant_value); base = k.k1.k2; noise = float(k.k2.noise_level)
        nu = float(getattr(base, "nu", np.inf)); ls = np.atleast_1d(base.length_scale).tolist()
        card["outputs"][tgt] = dict(units="dB/cm" if tgt == "IL" else "V*cm", log10=kw["log"], kernel=kw["kind"], nu=nu, linear_mean=kw["linmean"],
                                    beta=m.beta.tolist(), mu=m.mu, sd=m.sd, const=c, length_scales=ls, noise=noise,
                                    Xtrain_u=u(X).tolist(), alpha=g.alpha_.ravel().tolist(), L=g.L_.tolist(), cv=met, lml=float(g.log_marginal_likelihood_value_))
        y = Y[tgt]; a = ax[i]; a.loglog(y, yp, "o", ms=4, mfc="none") if tgt == "IL" else a.plot(y, yp, "o", ms=4, mfc="none")
        lo_, hi_ = y.min() * 0.9, y.max() * 1.1; a.plot([lo_, hi_], [lo_, hi_], "r--"); a.set_xlabel(f"FEM {tgt}"); a.set_ylabel(f"GP 10-fold CV {tgt}")
        a.set_title(f"{tgt}: {kw['kind']}, lin-mean={kw['linmean']}, log={kw['log']}\nR²={met['R2_phys']:.4f}  MAPE={met['MAPE_pct']:.2f} %  max={met['maxAPE_pct']:.1f} %  95%-cover={met['cover95_pct']:.0f} %", fontsize=9)
        a.grid(alpha=.3, which="both")
        ax[2].bar(np.arange(6) + (i - 0.5) * 0.38, ls, 0.38, label=tgt)
        print(tgt, "final", kw, "ls", np.round(ls, 3), "noise", noise)
    ax[2].set_xticks(range(6)); ax[2].set_xticklabels(NAMES); ax[2].set_yscale("log"); ax[2].set_ylabel("ARD length scale (inputs in [0,1])"); ax[2].legend(); ax[2].set_title("Short length = strong / non-linear influence", fontsize=9)
    fig.tight_layout(); fig.savefig("gp_parity_ard.png", dpi=150)
    json.dump(card, open("models/model_card.json", "w")); json.dump(report, open("cv_report.json", "w"), indent=1)
    # self-check: portable numpy predictor reproduces sklearn
    import predictor; P = predictor.Predictor("models/model_card.json")
    for tgt in ("IL", "VpiL"):
        m = pickle.load(open(f"models/gp_{tgt}.pkl", "rb")); ys, ts, ss = m.predict(X[:20]); r = P.predict_array(X[:20])
        print(tgt, "numpy vs sklearn max rel diff", float(np.max(np.abs(r[tgt]["mean"] / ys - 1))), float(np.max(np.abs(r[tgt]["std_t"] / ss - 1))))
