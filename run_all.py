"""Reproduce every number in the presentation.

    python run_all.py            # full run (~5 min)
    python run_all.py --quick    # smoke test (~1 min)
    python run_all.py --no-sharks --out results_nosharks   # field = paper's Algorithm 1 only

Outputs go to results/: slate.csv, strategies.csv, contests.csv, field_baseline.csv,
summary.csv, paired_tests.csv, pool_selection.csv, is_*.csv, run_info.json.
Figures are made separately by make_figures.py.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from dfs.config import Config  # noqa: E402
from dfs.contest import Contest, simulate  # noqa: E402
from dfs.field import FieldModel, lineup_has_stack  # noqa: E402
from dfs.importance import run_is_experiment  # noqa: E402
from dfs.optimize import LineupMILP, candidate_pool, lineup_scores, select_ucvar, unique_lineups, upper_cvar  # noqa: E402
from dfs.outcomes import OutcomeModel  # noqa: E402
from dfs.slate import build_correlation, build_slate  # noqa: E402
from dfs.stats import paired_tests, summarize  # noqa: E402

OUT = Path(__file__).parent / "results"


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.1f}s] {msg}", flush=True)


def main(quick: bool, no_sharks: bool = False, out: str | None = None):
    global OUT
    if out:
        OUT = Path(__file__).parent / out
    cfg = Config()
    if no_sharks:
        cfg.shark_frac = 0.0
    if quick:
        cfg.n_gen_scenarios, cfg.n_select_fields, cfg.n_select_draws = 60, 10, 50
        cfg.n_test_fields, cfg.n_test_draws, cfg.n_field_lineup_baseline = 20, 10, 50
    OUT.mkdir(exist_ok=True)

    # ---------------- 1. inputs ----------------
    slate = build_slate(cfg.n_teams, cfg.seed_slate)
    R = build_correlation(slate)
    om = OutcomeModel(slate, R)
    fm = FieldModel(slate, cfg)
    milp = LineupMILP(slate, cfg)
    mu, sd = slate["proj"].to_numpy(), slate["sd"].to_numpy()
    np.save(OUT / "corr.npy", R)
    log(f"slate: {len(slate)} players, min eig(R) = {np.linalg.eigvalsh(R).min():.3f}")

    # sharks for the generation/selection stages (test stage gets its own pool below)
    if cfg.shark_frac > 0:
        fm.build_shark_pool(milp, np.random.default_rng(cfg.seed_select + 1))
        log(f"shark pool (selection): {len(np.unique(fm.shark_pool, axis=0))} unique lineups")
    else:
        log("no sharks: field is the paper's Algorithm 1 only")

    # pilot field -> expected ownership (used only to generate contrarian candidates)
    pilot, _ = fm.generate(np.random.default_rng(cfg.seed_gen + 7))
    own = np.bincount(pilot.ravel(), minlength=len(slate)) / len(pilot)
    slate["field_own"] = own
    slate.to_csv(OUT / "slate.csv", index=False)
    log(f"pilot field: acceptance {fm.acceptance_rate:.3f}, minnow stack rate {fm.stack_rate:.3f}, "
        f"mean proj {mu[pilot].sum(axis=1).mean():.1f} (max-proj lineup {mu[milp.solve(mu)].sum():.1f})")

    # ---------------- 2. candidate pool ----------------
    rng_gen = np.random.default_rng(cfg.seed_gen)
    gen_pts, _ = om.sample(cfg.n_gen_scenarios, rng_gen)
    pool = list(candidate_pool(milp, gen_pts, mu, sd, cfg.lambda_grid))
    # ownership-penalized ("leverage") candidates: mu + lam*sd - gamma*own
    for lam in (0.0, 0.5, 1.0):
        for gamma in (5, 10, 20, 40):
            for stack in (False, True):
                pool.append(milp.solve(mu + lam * sd - gamma * own, stack=stack))
    pool = unique_lineups(pool)
    log(f"candidate pool: {len(pool)} unique lineups")

    # ---------------- 3. selection scenarios (with simulated fields) ----------------
    rng_sel = np.random.default_rng(cfg.seed_select)
    O = cfg.n_opponents
    contest = Contest(cfg, O + 1)
    top_k = max(1, int(round(0.001 * (O + 1))))
    sel_pts, cutoffs, pool_pay = [], [], []
    for f in range(cfg.n_select_fields):
        field, _ = fm.generate(rng_sel)
        pts, _ = om.sample(cfg.n_select_draws, rng_sel)
        F = lineup_scores(pts, field)
        S = lineup_scores(pts, pool)
        for d in range(cfg.n_select_draws):
            fs = np.sort(F[:, d])
            cutoffs.append(fs[-top_k])
            pool_pay.append(contest.evaluate(fs, S[:, d])[0])
        sel_pts.append(pts)
    sel_pts = np.concatenate(sel_pts)
    cutoffs = np.array(cutoffs)
    pool_pay = np.array(pool_pay).T            # [K, n_sel]
    log(f"selection: {len(sel_pts)} scenarios over {cfg.n_select_fields} fields")

    # ---------------- 4. strategies ----------------
    a = cfg.ucvar_alpha
    b1 = milp.solve(mu)
    b2 = milp.solve(mu, stack=True)
    s1, u_raw = select_ucvar(pool, sel_pts, a)
    s2, u_exc = select_ucvar(pool, sel_pts, a, benchmark=cutoffs)
    exp_pay = pool_pay.mean(axis=1)
    s3 = pool[int(np.argmax(exp_pay))]
    # S2-CV: choose alpha by validation inside the selection data (never the test data).
    # Pick on the first half of the selection fields, score the pick by mean simulated
    # payout on the second half, then re-select on all scenarios with the winning alpha.
    n_half = (cfg.n_select_fields // 2) * cfg.n_select_draws
    tr, va = slice(0, n_half), slice(n_half, None)
    cv_rows = []
    for al in (0.90, 0.95, 0.975, 0.99):
        _, u_tr = select_ucvar(pool, sel_pts[tr], al, benchmark=cutoffs[tr])
        k = int(np.argmax(u_tr))
        cv_rows.append({"alpha": al, "pick": k, "val_payout": float(pool_pay[k, va].mean())})
    cv = pd.DataFrame(cv_rows)
    cv.to_csv(OUT / "alpha_cv.csv", index=False)
    alpha_cv = float(cv.loc[cv["val_payout"].idxmax(), "alpha"])
    s2cv, _ = select_ucvar(pool, sel_pts, alpha_cv, benchmark=cutoffs)
    log(f"S2-CV: validation picked alpha = {alpha_cv}")
    print(cv.round(3).to_string(index=False))

    strategies = {"B1 Max projection": b1, "B2 Max proj + stack": b2,
                  "S1 U-CVaR (score)": s1, "S2 U-CVaR (vs field)": s2,
                  f"S2-CV U-CVaR (vs field, a={alpha_cv})": s2cv,
                  "S3 Max sim. payout": s3}

    # alpha sensitivity of the two U-CVaR selections (in-sample picks)
    alpha_rows = []
    for al in (0.90, 0.95, 0.99, 0.995):
        _, ur = select_ucvar(pool, sel_pts, al)
        _, ue = select_ucvar(pool, sel_pts, al, benchmark=cutoffs)
        alpha_rows.append({"alpha": al, "pick_score": int(np.argmax(ur)),
                           "pick_vs_field": int(np.argmax(ue))})
    alpha_picks = pd.DataFrame(alpha_rows)

    S_pool = lineup_scores(sel_pts, pool)
    pd.DataFrame({
        "lineup": [" ".join(map(str, l)) for l in pool],
        "mean_score": S_pool.mean(axis=1), "sd_score": S_pool.std(axis=1),
        "ucvar_score": u_raw, "ucvar_vs_field": u_exc, "exp_payout_insample": exp_pay,
        "avg_field_own": own[pool].mean(axis=1), "proj": mu[pool].sum(axis=1),
        "salary": slate["salary"].to_numpy()[pool].sum(axis=1),
    }).to_csv(OUT / "pool_selection.csv", index=False)

    rows = []
    for k, l in strategies.items():
        rows.append({"strategy": k, "players": "; ".join(slate.loc[l, "name"]),
                     "pids": " ".join(map(str, l)),
                     "salary": int(slate.loc[l, "salary"].sum()), "proj": mu[l].sum(),
                     "avg_field_own": own[l].mean(),
                     "has_stack": bool(lineup_has_stack(l[None, :], slate)[0])})
    pd.DataFrame(rows).to_csv(OUT / "strategies.csv", index=False)
    for k, l in strategies.items():
        log(f"{k:24s} proj {mu[l].sum():6.1f}  own {own[l].mean():.3f}  {', '.join(slate.loc[l, 'name'])}")

    # ---------------- 5. out-of-sample contests ----------------
    rng_test = np.random.default_rng(cfg.seed_test)
    if cfg.shark_frac > 0:
        fm.build_shark_pool(milp, np.random.default_rng(cfg.seed_test + 1))
        log("shark pool (test) rebuilt with a fresh seed")
    # evaluate the named strategies AND every pool candidate on the same contests (CRN)
    all_strats = dict(strategies)
    all_strats.update({f"pool_{i:03d}": l for i, l in enumerate(pool)})
    res_all, extras = simulate(all_strats, slate, om, fm, cfg, cfg.n_test_fields, cfg.n_test_draws,
                               rng_test, n_field_baseline=cfg.n_field_lineup_baseline,
                               keep_field_scores=True)
    is_pool = res_all["strategy"].str.startswith("pool_")
    res = res_all[~is_pool].reset_index(drop=True)
    rp = res_all[is_pool].copy()
    n_ent = O + 1
    rp["cash"] = rp["rank"] <= int(cfg.paid_frac * n_ent)
    rp["top1"] = rp["rank"] <= int(round(0.01 * n_ent))
    rp["top01"] = rp["rank"] <= int(round(0.001 * n_ent))
    oos = rp.groupby("strategy").agg(oos_payout=("payout", "mean"), oos_cash=("cash", "mean"),
                                     oos_top1=("top1", "mean"), oos_top01=("top01", "mean"),
                                     oos_pct_rank=("rank", "mean"), oos_dups=("dups_in_field", "mean"))
    oos["oos_pct_rank"] /= n_ent
    # per-field payout SE for each candidate (clustered)
    pf = rp.groupby(["strategy", "field"])["payout"].mean().groupby("strategy")
    oos["oos_payout_se"] = pf.std(ddof=1) / np.sqrt(pf.count())
    oos.index = [int(s.split("_")[1]) for s in oos.index]
    pool_df = pd.read_csv(OUT / "pool_selection.csv").join(oos.sort_index())
    pool_df.to_csv(OUT / "pool_selection.csv", index=False)
    alpha_picks["oos_roi_score"] = pool_df.loc[alpha_picks["pick_score"], "oos_payout"].to_numpy() - 1
    alpha_picks["oos_roi_vs_field"] = pool_df.loc[alpha_picks["pick_vs_field"], "oos_payout"].to_numpy() - 1
    alpha_picks["proj_score"] = pool_df.loc[alpha_picks["pick_score"], "proj"].to_numpy()
    alpha_picks["proj_vs_field"] = pool_df.loc[alpha_picks["pick_vs_field"], "proj"].to_numpy()
    alpha_picks.to_csv(OUT / "alpha_sensitivity.csv", index=False)
    print(alpha_picks.round(3).to_string(index=False))
    res.to_csv(OUT / "contests.csv", index=False)
    extras["field_baseline"].to_csv(OUT / "field_baseline.csv", index=False)
    np.save(OUT / "field_scores_example.npy", np.array(extras["field_scores"]))
    np.save(OUT / "payout_table.npy", extras["contest"].pay)
    log(f"test: {res['contest'].nunique()} contests")

    summary = summarize(res, extras["field_baseline"], cfg, O + 1)
    summary.to_csv(OUT / "summary.csv", index=False)
    tests = paired_tests(res, ref="B1 Max projection")
    tests.to_csv(OUT / "paired_tests.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(summary.round(4).to_string(index=False))
        print(tests.round(4).to_string(index=False))

    # ---------------- 6. importance sampling ----------------
    c = float(res["cutoff_top01"].mean())
    is_res = run_is_experiment(om, s1, c, np.random.default_rng(cfg.seed_is), quick=quick,
                               extra_thresholds=(165.0, 180.0, 195.0))
    for k, v in is_res.items():
        v.to_csv(OUT / f"is_{k}.csv", index=False)
    log("importance sampling done")
    print(is_res["summary"].round(6).to_string(index=False))

    json.dump({"config": {k: (v if not isinstance(v, tuple) else list(v))
                          for k, v in cfg.__dict__.items()},
               "quick": quick, "shark_frac": cfg.shark_frac, "pool_size": int(len(pool)),
               "acceptance_rate": float(fm.acceptance_rate),
               "is_cutoff": c, "alpha_cv": alpha_cv}, open(OUT / "run_info.json", "w"), indent=2)
    log("done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-sharks", action="store_true", help="opponent field without optimizer sharks")
    ap.add_argument("--out", default=None, help="output folder (default: results)")
    a = ap.parse_args()
    main(a.quick, a.no_sharks, a.out)
