"""Output analysis: per-strategy summaries and paired comparisons.

Contests that share a simulated field are correlated (splitting), so all CIs are
computed over per-field means (cluster-level), i.e. n = number of test fields.
"""
import numpy as np
import pandas as pd
from scipy import stats

from .config import Config


def _ci(x: np.ndarray, level=0.95):
    x = np.asarray(x, float)
    n = len(x)
    m = x.mean()
    h = stats.t.ppf(0.5 + level / 2, n - 1) * x.std(ddof=1) / np.sqrt(n)
    return m, m - h, m + h


def summarize(res: pd.DataFrame, baseline: pd.DataFrame, cfg: Config, n_entries: int) -> pd.DataFrame:
    paid = int(cfg.paid_frac * n_entries)
    top1 = int(round(0.01 * n_entries))
    top01 = int(round(0.001 * n_entries))
    df = res.copy()
    df["cash"] = df["rank"] <= paid
    df["top1"] = df["rank"] <= top1
    df["top01"] = df["rank"] <= top01
    df["pct_rank"] = df["rank"] / n_entries
    df["roi"] = df["payout"] / cfg.entry_fee - 1

    b = baseline.copy()
    b["strategy"] = "Field lineup (baseline)"
    b["cash"] = b["rank"] <= paid
    b["top1"] = b["rank"] <= top1
    b["top01"] = b["rank"] <= top01
    b["pct_rank"] = b["rank"] / n_entries
    b["roi"] = b["payout"] / cfg.entry_fee - 1
    b["score"] = np.nan
    b["dups_in_field"] = np.nan

    cols = ["roi", "cash", "top1", "top01", "pct_rank", "score", "dups_in_field"]
    out = []
    for name, g in pd.concat([b, df], ignore_index=True).groupby("strategy", sort=False):
        per_field = g.groupby("field")[cols].mean()
        row = {"strategy": name, "n_contests": int(len(g)) if name != "Field lineup (baseline)"
               else int(g["field"].nunique() * res["draw"].nunique()),
               "n_fields": int(per_field.shape[0])}
        for c in ["roi", "cash", "top1", "top01"]:
            m, lo, hi = _ci(per_field[c])
            row[c], row[c + "_lo"], row[c + "_hi"] = m, max(lo, -1.0 if c == "roi" else 0.0), hi
        row["mean_pct_rank"] = per_field["pct_rank"].mean()
        row["mean_score"] = per_field["score"].mean()
        row["avg_dups_in_field"] = per_field["dups_in_field"].mean()
        row["max_payout"] = g["payout"].max()
        out.append(row)
    return pd.DataFrame(out)


def paired_tests(res: pd.DataFrame, ref: str, n_boot: int = 10_000, seed: int = 0) -> pd.DataFrame:
    """Paired (common random numbers) comparison of each strategy vs ref, clustered by field."""
    rng = np.random.default_rng(seed)
    n_entries_top01 = None
    wide_pay = res.pivot_table(index=["field", "draw"], columns="strategy", values="payout")
    wide_rank = res.pivot_table(index=["field", "draw"], columns="strategy", values="rank")
    top_k = int(res["cutoff_top01"].notna().any())  # placeholder to keep signature simple
    out = []
    for k in wide_pay.columns:
        if k == ref:
            continue
        d_pay = (wide_pay[k] - wide_pay[ref]).groupby(level="field").mean().to_numpy()
        d_rank = (wide_rank[k] - wide_rank[ref]).groupby(level="field").mean().to_numpy()
        t = stats.ttest_1samp(d_pay, 0.0)
        boots = rng.choice(d_pay, size=(n_boot, len(d_pay)), replace=True).mean(axis=1)
        out.append({"strategy": k, "vs": ref,
                    "mean_payout_diff": d_pay.mean(),
                    "boot_lo": np.percentile(boots, 2.5), "boot_hi": np.percentile(boots, 97.5),
                    "t_stat": t.statistic, "p_value": t.pvalue,
                    "mean_rank_diff": d_rank.mean(),
                    "p_value_rank": stats.ttest_1samp(d_rank, 0.0).pvalue})
    return pd.DataFrame(out)
