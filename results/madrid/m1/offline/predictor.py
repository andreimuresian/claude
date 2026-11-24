"""Offline Madrid 1 predictor: numpy only (no scikit-learn, no pickle), reads models/model_card.json.
    from predictor import Predictor
    P = Predictor("models/model_card.json")
    P.predict(GAP=3.2, BUFFER_H=0.10, CAP_W=3.0, CAP_H=0.5, MTX_SMALL=1.0)   # um
Returns mean, 95 % interval (asymmetric for log targets), flags for extrapolation / invalid geometry, and the
IL / Vpi*L at BUFFER_H - 40 nm (process worst case)."""
import json, numpy as np

class Predictor:
    def __init__(self, card="models/model_card.json"):
        self.c = json.load(open(card)); self.lo = np.array(self.c["lo"]); self.hi = np.array(self.c["hi"])
        self.o = {}
        for k, m in self.c["outputs"].items():
            self.o[k] = dict(m, Xu=np.array(m["Xtrain_u"]), alpha=np.array(m["alpha"]), L=np.array(m["L"]), ls=np.array(m["length_scales"]), beta=np.array(m["beta"]))

    def _k(self, A, B, m):
        d = np.sqrt(np.maximum(((A[:, None, :] - B[None, :, :]) / m["ls"]) ** 2, 0).sum(-1))
        if m["nu"] == 2.5: k = (1 + np.sqrt(5) * d + 5 * d ** 2 / 3) * np.exp(-np.sqrt(5) * d)
        elif m["nu"] == 1.5: k = (1 + np.sqrt(3) * d) * np.exp(-np.sqrt(3) * d)
        else: k = np.exp(-0.5 * d ** 2)
        return m["const"] * k

    def predict_array(self, X):
        """X: (n,5) in model inputs [GAP, BUFFER_H, CAP_F, CAP_H, MTX_SMALL] (um / fraction)."""
        X = np.atleast_2d(np.asarray(X, float)); Z = (X - self.lo) / (self.hi - self.lo); out = {}
        for k, m in self.o.items():
            Ks = self._k(Z, m["Xu"], m); mt = Ks @ m["alpha"]
            v = np.linalg.solve(m["L"], Ks.T) if len(Z) < 2000 else __import__("scipy.linalg", fromlist=["x"]).solve_triangular(m["L"], Ks.T, lower=True)
            var = np.maximum(m["const"] + m["noise"] - np.sum(v * v, 0), 0)
            t = np.c_[np.ones(len(Z)), Z] @ m["beta"] + m["mu"] + m["sd"] * mt; st = m["sd"] * np.sqrt(var)
            if m["log10"]: mean, lo, hi = 10 ** t, 10 ** (t - 1.96 * st), 10 ** (t + 1.96 * st)
            else: mean, lo, hi = t, t - 1.96 * st, t + 1.96 * st
            out[k] = dict(mean=mean, lo95=lo, hi95=hi, std_t=st)
        out["outside_bounds"] = np.any((X < self.lo - 1e-9) | (X > self.hi + 1e-9), axis=1)
        return out

    def predict(self, GAP, BUFFER_H, CAP_W, CAP_H, MTX_SMALL, worst_case_dbuf=-0.040):
        f = (GAP - CAP_W) / (GAP - self.c["capw_min"]); flags = []
        if CAP_W > GAP + 1e-9: flags.append("CAP_W > GAP (impossible)")
        if CAP_W < self.c["capw_min"] - 1e-9: flags.append("CAP_W below trained range")
        x = np.array([[GAP, BUFFER_H, f, CAP_H, MTX_SMALL]]); r = self.predict_array(x)
        if r["outside_bounds"][0]: flags.append("outside trained bounds: extrapolation")
        xw = x.copy(); xw[0, 1] += worst_case_dbuf; rw = self.predict_array(xw)
        if rw["outside_bounds"][0]: flags.append("worst-case buffer outside trained range")
        res = {k: {kk: float(vv[0]) for kk, vv in r[k].items()} for k in self.o}
        res["worst_case"] = {k: {kk: float(vv[0]) for kk, vv in rw[k].items()} for k in self.o}
        res["flags"] = flags
        return res

if __name__ == "__main__":
    P = Predictor(); r = P.predict(GAP=3.2, BUFFER_H=0.10, CAP_W=3.0, CAP_H=0.5, MTX_SMALL=1.0)
    for k in ("VpiL", "IL"): print(f"{k:5s} {r[k]['mean']:.4f}  95% [{r[k]['lo95']:.4f}, {r[k]['hi95']:.4f}]   at buffer-40nm: {r['worst_case'][k]['mean']:.4f}")
    print("flags:", r["flags"] or "none")
