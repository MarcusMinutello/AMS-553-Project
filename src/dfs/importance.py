"""Importance sampling for a rare upside event.

Target: p = P(score of lineup L > c), where c is the (average) top-0.1% field cutoff.
Crude MC vs. IS with a mean shift in the latent Gaussian space. The shift is along
v = R a / sqrt(a' R a), where a_i = d score / d Z_i at Z = 0 (= s_i e^{m_i} for i in L).
Moving Z's mean by t*v shifts the linearized score by t standard deviations.
"""
import numpy as np
import pandas as pd


def _direction(om, lineup):
    a = np.zeros(om.P)
    a[lineup] = om.s[lineup] * np.exp(om.m[lineup])
    v = om.R @ a / np.sqrt(a @ om.R @ a)
    return v


def _estimate(om, lineup, c, n, rng, theta=None):
    pts, w = om.sample(n, rng, theta)
    hit = pts[:, lineup].sum(axis=1) > c
    x = hit * w
    return x.mean(), x.std(ddof=1)


def threshold_sweep(om, lineup, thresholds, rng, n_truth, n_pilot=20_000):
    """For each threshold: true p (crude, shared samples), best tilt and variance reduction."""
    v = _direction(om, lineup)
    hits = np.zeros(len(thresholds))
    for _ in range(n_truth // 200_000):
        pts, _ = om.sample(200_000, rng)
        sc = pts[:, lineup].sum(axis=1)
        hits += (sc[:, None] > np.asarray(thresholds)[None, :]).sum(axis=0)
    rows = []
    for c, h in zip(thresholds, hits):
        p = h / n_truth
        best = (None, np.inf)
        for t in np.arange(0.5, 6.01, 0.25):
            m, s = _estimate(om, lineup, c, n_pilot, rng, theta=t * v)
            if s < best[1]:
                best = (t, s)
        rows.append({"threshold": c, "p_true": p, "t_star": best[0],
                     "variance_reduction_factor": p * (1 - p) / best[1] ** 2 if p > 0 else np.nan})
    return pd.DataFrame(rows)


def run_is_experiment(om, lineup, c, rng, quick=False, extra_thresholds=()):
    v = _direction(om, lineup)

    # ground truth by large crude MC (chunked)
    n_truth = 400_000 if quick else 2_000_000
    hits = 0
    for _ in range(n_truth // 200_000):
        pts, _ = om.sample(200_000, rng)
        hits += int((pts[:, lineup].sum(axis=1) > c).sum())
    p_true = hits / n_truth

    # pilot: per-sample std of the estimator as a function of tilt t
    t_grid = np.round(np.arange(0.0, 4.01, 0.25), 2)
    n_pilot = 20_000
    tilt = []
    for t in t_grid:
        m, s = _estimate(om, lineup, c, n_pilot, rng, theta=None if t == 0 else t * v)
        tilt.append({"t": t, "estimate": m, "per_sample_sd": s,
                     "variance_ratio_vs_crude": np.nan})
    tilt = pd.DataFrame(tilt)
    crude_var = tilt.loc[tilt["t"] == 0, "per_sample_sd"].iloc[0] ** 2
    if crude_var == 0:
        crude_var = p_true * (1 - p_true)
    tilt["variance_ratio_vs_crude"] = crude_var / tilt["per_sample_sd"] ** 2
    t_star = float(tilt.loc[tilt["t"] > 0].sort_values("per_sample_sd")["t"].iloc[0])

    # repeated estimates at several sample sizes
    reps = 100 if quick else 300
    rows = []
    for n in (250, 500, 1000, 2000, 4000):
        for method, theta in (("Crude MC", None), ("Importance sampling", t_star * v)):
            ests = np.array([_estimate(om, lineup, c, n, rng, theta)[0] for _ in range(reps)])
            rows.append({"n": n, "method": method, "mean": ests.mean(), "sd": ests.std(ddof=1),
                         "rel_error": ests.std(ddof=1) / p_true,
                         "frac_zero": float((ests == 0).mean()),
                         "q05": np.percentile(ests, 5), "q95": np.percentile(ests, 95)})
    reps_df = pd.DataFrame(rows)
    summary = pd.DataFrame([{
        "cutoff": c, "p_true": p_true, "n_truth": n_truth, "t_star": t_star,
        "variance_reduction_factor": float(tilt.loc[tilt["t"] == t_star, "variance_ratio_vs_crude"].iloc[0]),
    }])
    out = {"summary": summary, "tilt": tilt, "reps": reps_df}
    if extra_thresholds:
        out["thresholds"] = threshold_sweep(om, lineup, [c, *extra_thresholds], rng, n_truth)
    return out
