"""Lineup construction: MILP template (scipy/HiGHS) + U-CVaR selection.

DraftKings NFL roster: QB, 2 RB, 3 WR, TE, FLEX (RB/WR/TE), DST; salary <= cap.
"""
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

from .config import Config


class LineupMILP:
    def __init__(self, slate: pd.DataFrame, cfg: Config):
        self.slate = slate
        self.cfg = cfg
        P = len(slate)
        pos = slate["pos"].to_numpy()
        sal = slate["salary"].to_numpy(float)
        rows, lo, hi = [], [], []

        def add(a, l, h):
            rows.append(a); lo.append(l); hi.append(h)

        one = lambda m: m.astype(float)
        add(np.ones(P), cfg.lineup_size, cfg.lineup_size)
        add(one(pos == "QB"), 1, 1)
        add(one(pos == "DST"), 1, 1)
        add(one(pos == "RB"), 2, 3)
        add(one(pos == "WR"), 3, 4)
        add(one(pos == "TE"), 1, 2)
        add(sal, 0, cfg.salary_cap)
        self.base = (np.array(rows), np.array(lo, float), np.array(hi, float))

        # stacking rows: x_QB(team) - x_WR1(team) <= 0
        srows = []
        for team, g in slate.groupby("team"):
            qb = g.index[g["role"] == "QB1"][0]
            wr1 = g.index[g["role"] == "WR1"][0]
            r = np.zeros(P); r[qb] = 1; r[wr1] = -1
            srows.append(r)
        self.stack_rows = np.array(srows)
        self.P = P

    def solve(self, c: np.ndarray, stack: bool = False, max_overlap: int | None = None,
              previous: list | None = None) -> np.ndarray:
        """Maximize c'x. Returns sorted pids of the chosen lineup."""
        A, lo, hi = self.base
        cons = [LinearConstraint(A, lo, hi)]
        if stack:
            cons.append(LinearConstraint(self.stack_rows, -np.inf, 0))
        if max_overlap is not None and previous:
            M = np.zeros((len(previous), self.P))
            for k, lin in enumerate(previous):
                M[k, lin] = 1
            cons.append(LinearConstraint(M, -np.inf, max_overlap))
        res = milp(-np.asarray(c, float), constraints=cons, integrality=np.ones(self.P),
                   bounds=Bounds(0, 1))
        if res.x is None:
            raise RuntimeError(f"MILP failed: {res.message}")
        return np.sort(np.flatnonzero(res.x > 0.5))


def unique_lineups(lineups) -> np.ndarray:
    return np.unique(np.array([np.sort(l) for l in lineups]), axis=0)


def candidate_pool(milp: LineupMILP, gen_points: np.ndarray, mu: np.ndarray, sd: np.ndarray,
                   lambda_grid) -> np.ndarray:
    """Scenario-optimal lineups (one per generation scenario) + mean+lambda*sd lineups,
    with and without a QB-WR1 stack. Returns unique lineups [K, 9]."""
    out = []
    for d in gen_points:
        out.append(milp.solve(d))
    for lam in lambda_grid:
        out.append(milp.solve(mu + lam * sd))
        out.append(milp.solve(mu + lam * sd, stack=True))
    return unique_lineups(out)


def lineup_scores(points: np.ndarray, lineups: np.ndarray) -> np.ndarray:
    """points [n, P], lineups [K, 9] -> scores [K, n] (same summation order everywhere)."""
    return points[:, lineups].sum(axis=-1).T


def upper_cvar(values: np.ndarray, alpha: float, weights: np.ndarray | None = None) -> np.ndarray:
    """U-CVaR_alpha along the last axis: (weighted) mean of the top (1 - alpha) tail."""
    values = np.atleast_2d(values)
    n = values.shape[-1]
    if weights is None:
        k = max(1, int(round((1 - alpha) * n)))
        top = np.partition(values, n - k, axis=-1)[..., n - k:]
        return top.mean(axis=-1)
    w = weights / weights.sum()
    order = np.argsort(-values, axis=-1)
    v = np.take_along_axis(values, order, axis=-1)
    ws = w[order]
    cum = np.cumsum(ws, axis=-1)
    tail = 1 - alpha
    take = np.clip(tail - (cum - ws), 0, ws)       # partial weight at the boundary
    return (v * take).sum(axis=-1) / tail


def select_ucvar(pool: np.ndarray, points: np.ndarray, alpha: float, weights=None,
                 benchmark: np.ndarray | None = None):
    """Pick the candidate with max U-CVaR of score (or of score - benchmark, per scenario).
    Returns (best lineup, ucvar values for the whole pool)."""
    S = lineup_scores(points, pool)
    if benchmark is not None:
        S = S - benchmark[None, :]
    u = upper_cvar(S, alpha, weights)
    return pool[int(np.argmax(u))], u
