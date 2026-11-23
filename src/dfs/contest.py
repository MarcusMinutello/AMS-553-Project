"""Top-heavy payout table and out-of-sample contest simulation.

Each contest = one simulated opponent field (O lineups) + one outcome draw.
"Splitting": each field is reused for several outcome draws. Every strategy plays
the same contests (common random numbers), and is entered as a single extra entry,
so the contest has O + 1 entries. Ties split the tied prizes evenly.
"""
import numpy as np
import pandas as pd
from scipy.optimize import brentq

from .config import Config
from .field import FieldModel
from .optimize import lineup_scores


def payout_table(cfg: Config, n_entries: int) -> np.ndarray:
    """Payout by rank (index 0 = 1st). Top paid_frac cash; min cash for every paid
    rank plus a power-law bonus R(r) = A r^-g calibrated so 1st ~ first_place_frac."""
    pool = n_entries * cfg.entry_fee * (1 - cfg.rake)
    K = int(cfg.paid_frac * n_entries)
    r = np.arange(1, K + 1, dtype=float)
    extra = pool - cfg.min_cash * K
    target_first = cfg.first_place_frac * pool - cfg.min_cash
    # choose g so that A = extra / sum(r^-g) equals target_first
    f = lambda g: extra / np.sum(r ** -g) - target_first
    g = brentq(f, 0.3, 5.0)
    A = extra / np.sum(r ** -g)
    pay = np.zeros(n_entries)
    pay[:K] = cfg.min_cash + A * r ** -g
    return pay


class Contest:
    def __init__(self, cfg: Config, n_entries: int):
        self.pay = payout_table(cfg, n_entries)
        self.cum = np.concatenate([[0.0], np.cumsum(self.pay)])
        self.n_entries = n_entries

    def payout(self, n_better: np.ndarray, n_tied: np.ndarray) -> np.ndarray:
        """Our entry is tied with n_tied field entries and beaten by n_better."""
        lo = n_better
        hi = n_better + n_tied + 1
        return (self.cum[hi] - self.cum[lo]) / (n_tied + 1)

    def evaluate(self, field_sorted: np.ndarray, scores: np.ndarray):
        """field_sorted: sorted field scores [O]; scores: our entries' scores [K].
        Returns (payout, rank) where rank is 1-based (best case among ties)."""
        O = len(field_sorted)
        right = np.searchsorted(field_sorted, scores, side="right")
        left = np.searchsorted(field_sorted, scores, side="left")
        n_better = O - right
        n_tied = right - left
        return self.payout(n_better, n_tied), n_better + 1


def simulate(strategies: dict, slate: pd.DataFrame, outcome_model, field_model: FieldModel,
             cfg: Config, n_fields: int, n_draws: int, rng: np.random.Generator,
             n_field_baseline: int = 0, keep_field_scores: bool = False):
    """Run n_fields * n_draws contests. Returns (per-contest results DataFrame, extras)."""
    names = list(strategies)
    lineups = np.array([strategies[k] for k in names])
    O = cfg.n_opponents
    contest = Contest(cfg, O + 1)
    top_k = max(1, int(round(0.001 * (O + 1))))
    P = len(slate)
    powers = P ** np.arange(lineups.shape[1], dtype=np.int64)
    our_keys = np.sort(lineups, axis=1) @ powers
    rows, base_rows, field_snap = [], [], []
    for f in range(n_fields):
        field, _ = field_model.generate(rng, n_opponents=O + n_field_baseline)
        held_out, field = field[:n_field_baseline], field[n_field_baseline:]
        # duplicates of our lineups inside the field (lineups hashed to int64 keys)
        fkeys, fcounts = np.unique(field @ powers, return_counts=True)
        pos = np.searchsorted(fkeys, our_keys).clip(0, len(fkeys) - 1)
        dup_arr = np.where(fkeys[pos] == our_keys, fcounts[pos], 0)
        pts, _ = outcome_model.sample(n_draws, rng)
        F = lineup_scores(pts, field)               # [O, n_draws]
        ours = lineup_scores(pts, lineups)          # [S, n_draws]
        base = lineup_scores(pts, held_out) if n_field_baseline else None
        for d in range(n_draws):
            fs = np.sort(F[:, d])
            cutoff_01 = fs[-top_k]
            cash_line = fs[-int(cfg.paid_frac * (O + 1))]
            pay, rank = contest.evaluate(fs, ours[:, d])
            S = len(names)
            rows.append(np.column_stack([np.full(S, f), np.full(S, d), np.arange(S), ours[:, d],
                                         rank, pay, np.full(S, cutoff_01), np.full(S, cash_line),
                                         dup_arr]))
            if base is not None:
                bp, br = contest.evaluate(fs, base[:, d])
                base_rows.append(np.column_stack([np.full(len(bp), f), bp, br]))
            if keep_field_scores and f < 3 and d == 0:
                field_snap.append(fs)
    res = pd.DataFrame(np.concatenate(rows),
                       columns=["field", "draw", "sid", "score", "rank", "payout",
                                "cutoff_top01", "cash_line", "dups_in_field"])
    for c in ["field", "draw", "sid", "rank", "dups_in_field"]:
        res[c] = res[c].astype(int)
    res.insert(2, "strategy", np.array(names, dtype=object)[res.pop("sid").to_numpy()])
    res["contest"] = res["field"] * n_draws + res["draw"]
    extras = {"contest": contest, "top_k": top_k}
    if base_rows:
        b = np.concatenate(base_rows)
        extras["field_baseline"] = pd.DataFrame(b, columns=["field", "payout", "rank"])
    if field_snap:
        extras["field_scores"] = field_snap
    return res, extras
