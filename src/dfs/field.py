"""Opponent field generator (Haugh & Singal 2019, Algorithm 1), vectorized.

Per field (contest):
  1. Positional ownership p_pos ~ Dirichlet(kappa * p0_pos), where p0_pos is a
     softmax of standardized (projection, salary) within the position; this mirrors
     the paper's Dirichlet-regression features (projection, cost).
  2. Each opponent independently: stack ~ Bernoulli(q); QB ~ Mult(1, p_QB),
     2 RB / 3 WR / 1 TE / 1 DST drawn without replacement (Gumbel-top-k trick);
     FLEX = the next-ranked RB/WR/TE, choosing the position with prob flex weights.
     If stacking, WR slot #1 is replaced by the QB's team WR1 (if not already chosen).
  3. Accept only lineups with salary in [B_lb, B]. Repeat until O accepted.

Field mix: following the paper's observation that ~80% of DFS players are
"minnows" and the rest "sharks", a fraction shark_frac of each field is drawn from a
pool of optimizer-built lineups (noisy projections). Sharks can duplicate each other.
"""
import numpy as np
import pandas as pd

from .config import Config


class FieldModel:
    def __init__(self, slate: pd.DataFrame, cfg: Config):
        self.cfg = cfg
        self.slate = slate
        self.salary = slate["salary"].to_numpy(float)
        self.idx = {p: slate.index[slate["pos"] == p].to_numpy() for p in ["QB", "RB", "WR", "TE", "DST"]}
        self.p0 = {}
        for p, ix in self.idx.items():
            pr = slate.loc[ix, "proj"].to_numpy()
            sal = slate.loc[ix, "salary"].to_numpy()
            score = cfg.own_beta_proj * _z(pr) + cfg.own_beta_salary * _z(sal)
            e = np.exp(score - score.max())
            self.p0[p] = e / e.sum()
        # main WR (WR1) of each QB's team
        wr1 = slate[slate["role"] == "WR1"].set_index("team")["pid"]
        self.qb_stack_wr = wr1.loc[slate.loc[self.idx["QB"], "team"]].to_numpy()
        self.acceptance_rate = np.nan
        self.stack_rate = np.nan
        self.shark_pool = None

    def draw_ownership(self, rng: np.random.Generator) -> dict:
        k = self.cfg.dirichlet_kappa
        return {p: rng.dirichlet(k * p0) for p, p0 in self.p0.items()}

    def _candidates(self, n: int, own: dict, rng: np.random.Generator):
        """n candidate lineups (unfiltered), shape [n, 9], plus stack flags."""
        def topk(pos, k):
            g = np.log(own[pos] + 1e-300) + rng.gumbel(size=(n, len(own[pos])))
            order = np.argsort(-g, axis=1)[:, :k]
            return self.idx[pos][order]

        qb = topk("QB", 1)[:, 0]
        rb = topk("RB", 3)          # 3rd is FLEX candidate
        wr = topk("WR", 4)          # 4th is FLEX candidate
        te = topk("TE", 2)          # 2nd is FLEX candidate
        dst = topk("DST", 1)[:, 0]

        fw = self.cfg.flex_pos_weights
        u = rng.random(n)
        flex = np.where(u < fw["RB"], rb[:, 2], np.where(u < fw["RB"] + fw["WR"], wr[:, 3], te[:, 1]))

        wrs = wr[:, :3].copy()
        stack = rng.random(n) < self.cfg.stack_prob
        qb_pos = np.searchsorted(self.idx["QB"], qb)
        target = self.qb_stack_wr[qb_pos]
        already = (wrs == target[:, None]).any(axis=1) | (flex == target)
        do = stack & ~already
        wrs[do, 0] = target[do]

        L = np.column_stack([qb, rb[:, :2], wrs, te[:, 0], flex, dst])
        return L, stack

    def build_shark_pool(self, milp, rng: np.random.Generator, size: int | None = None):
        """'Sharks' build lineups with an optimizer on their own noisy projections:
        c = mu * exp(N(0, noise^2)) + lam * sd, lam ~ U(0, 1), QB-WR1 stack w.p. 1/2."""
        size = size or self.cfg.shark_pool_size
        mu = self.slate["proj"].to_numpy(float)
        sd = self.slate["sd"].to_numpy(float)
        pool = []
        for _ in range(size):
            c = mu * np.exp(rng.normal(0.0, self.cfg.shark_noise, len(mu))) + rng.uniform(0, 1) * sd
            pool.append(milp.solve(c, stack=bool(rng.random() < 0.5)))
        self.shark_pool = np.array(pool)
        return self.shark_pool

    def generate(self, rng: np.random.Generator, n_opponents=None, own=None, batch=None):
        """Returns (lineups[O, 9] sorted pids, ownership dict used).
        A fraction shark_frac of the field is drawn (with replacement) from the shark
        pool, if one has been built; the rest are Algorithm-1 'minnows'."""
        O_total = n_opponents or self.cfg.n_opponents
        n_shark = int(round(self.cfg.shark_frac * O_total)) if self.shark_pool is not None else 0
        O = O_total - n_shark
        own = own if own is not None else self.draw_ownership(rng)
        batch = batch or max(4 * O, 20_000)
        lo, hi = self.cfg.salary_floor, self.cfg.salary_cap
        out, n_tried, n_stack = [], 0, 0
        n_have = 0
        while n_have < O:
            L, stack = self._candidates(batch, own, rng)
            sal = self.salary[L].sum(axis=1)
            ok = (sal >= lo) & (sal <= hi)
            n_tried += batch
            out.append(L[ok])
            n_stack += int(stack[ok].sum())
            n_have += int(ok.sum())
        lineups = np.sort(np.concatenate(out)[:O], axis=1)
        self.acceptance_rate = n_have / n_tried
        self.stack_rate = n_stack / n_have
        if n_shark:
            sharks = self.shark_pool[rng.integers(0, len(self.shark_pool), n_shark)]
            lineups = np.concatenate([lineups, sharks])
            lineups = lineups[rng.permutation(len(lineups))]
        return lineups, own


def _z(x):
    sd = x.std()
    return (x - x.mean()) / sd if sd > 0 else np.zeros_like(x)


def lineup_has_stack(lineups: np.ndarray, slate: pd.DataFrame) -> np.ndarray:
    """True where the lineup's QB is paired with any same-team WR/TE."""
    team = slate["team"].to_numpy()
    pos = slate["pos"].to_numpy()
    is_qb = pos[lineups] == "QB"
    qb_team = team[lineups][is_qb]
    recv = np.isin(pos[lineups], ["WR", "TE"])
    return ((team[lineups] == qb_team[:, None]) & recv).any(axis=1)
