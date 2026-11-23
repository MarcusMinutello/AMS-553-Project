"""Build presentation figures from results/ into results/figures/.

    python make_figures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RES = Path(__file__).parent / "results"
FIG = RES / "figures"

# validated categorical order (dataviz reference palette, light mode)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GRAY = "#8a8984"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
DIV_NEG, DIV_POS, DIV_MID = "#2a78d6", "#e34948", "#f0efec"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 12, "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.titlelocation": "left", "legend.frameon": False, "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

# S3 (max simulated payout) picked the same lineup as S2, so it is left off the charts.
STRAT_ORDER = ["B1 Max projection", "B2 Max proj + stack", "S1 U-CVaR (score)",
               "S2 U-CVaR (vs field)"]
_summary = pd.read_csv(RES / "summary.csv")
STRAT_ORDER += [s for s in _summary["strategy"] if s.startswith("S2-CV")]
COLOR = {k: SERIES[i] for i, k in enumerate(STRAT_ORDER)}
COLOR["Field lineup (baseline)"] = GRAY
SHORT = {k: k for k in STRAT_ORDER}
SHORT.update({"S2 U-CVaR (vs field)": "S2 U-CVaR vs field (a=0.99)"})
SHORT.update({k: "S2-CV U-CVaR vs field (a by CV)" for k in STRAT_ORDER if k.startswith("S2-CV")})
SHORT["Field lineup (baseline)"] = "Typical field lineup"


def save(fig, name):
    fig.savefig(FIG / f"{name}.png")
    plt.close(fig)
    print("wrote", name)


def fig_correlation(slate, R):
    ix = slate.index[slate["team"].isin(["TM1", "TM2"])].to_numpy()
    sub = R[np.ix_(ix, ix)]
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", [DIV_NEG, DIV_MID, DIV_POS])
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(sub, cmap=cmap, vmin=-0.5, vmax=0.5)
    labels = slate.loc[ix, "name"].str.replace("_", " ")
    ax.set_xticks(range(len(ix)), labels, rotation=90, fontsize=9)
    ax.set_yticks(range(len(ix)), labels, fontsize=9)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("Latent correlation", color=INK2)
    cb.outline.set_visible(False)
    ax.set_title("Player correlations in one game (TM1 vs TM2)")
    save(fig, "correlation_heatmap")


def fig_marginal(slate):
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    from dfs.outcomes import OutcomeModel
    R = np.load(RES / "corr.npy")
    om = OutcomeModel(slate, R)
    pts, _ = om.sample(200_000, np.random.default_rng(0))
    i = int(slate.index[slate["role"] == "WR1"][0])
    x = pts[:, i]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.hist(x, bins=np.arange(0, 60, 1), color=SERIES[0], edgecolor=SURFACE, linewidth=0.5)
    ax.axvline(x.mean(), color=INK, lw=2)
    ax.text(x.mean() + 0.8, ax.get_ylim()[1] * 0.92, f"mean {x.mean():.1f}", color=INK)
    p99 = np.percentile(x, 99)
    ax.axvline(p99, color=INK2, lw=2, ls="--")
    ax.text(p99 + 0.8, ax.get_ylim()[1] * 0.80, f"99th pct {p99:.1f}", color=INK2)
    ax.set_xlabel("Fantasy points")
    ax.set_ylabel("Simulated count")
    ax.set_title(f"Lognormal marginal: {slate.loc[i, 'name'].replace('_', ' ')} (right-skewed)")
    save(fig, "marginal_wr1")


def fig_payout(pay):
    r = np.arange(1, len(pay) + 1)
    paid = pay > 0
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(r[paid], pay[paid], color=SERIES[0], lw=2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Finishing rank (log scale)")
    ax.set_ylabel("Payout per $1 entry (log scale)")
    top10 = pay[:10].sum() / pay.sum()
    ax.set_title("Top-heavy payout curve, 10,001 entries")
    ax.text(1.2, pay[0] * 0.55, f"1st: ${pay[0]:.0f}", color=INK)
    ax.text(12, pay[10] * 1.4, f"Top 0.1% (10 entries) take {top10:.0%} of the pool", color=INK)
    last = paid.sum()
    ax.text(last * 0.25, pay[last - 1] * 1.6, f"min cash ${pay[last - 1]:.2f} at rank {last:,}",
            color=INK2)
    save(fig, "payout_curve")


def fig_field(fs_example, contests, slate):
    fs = fs_example[0]
    cut01 = np.sort(fs)[-10]
    cash = np.sort(fs)[-int(0.2 * (len(fs) + 1))]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.hist(fs, bins=80, color=GRAY, edgecolor=SURFACE, linewidth=0.4)
    for v, lab, ls in [(cash, f"cash line {cash:.0f}", "--"), (cut01, f"top-0.1% cutoff {cut01:.0f}", "-")]:
        ax.axvline(v, color=INK, lw=2, ls=ls)
        ax.text(v + 1, ax.get_ylim()[1] * (0.9 if ls == "-" else 0.75), lab, color=INK)
    ax.set_xlabel("Lineup score (fantasy points)")
    ax.set_ylabel("Opponent lineups")
    ax.set_title("One simulated contest: 10,000 opponent scores")
    save(fig, "field_scores")

    c = contests.drop_duplicates("contest")
    fig, ax = plt.subplots(figsize=(8, 4.0))
    ax.hist(c["cutoff_top01"], bins=50, color=SERIES[0], edgecolor=SURFACE, linewidth=0.4)
    ax.set_xlabel("Score needed for the top 0.1% (per contest)")
    ax.set_ylabel("Contests")
    ax.set_title(f"The bar to win moves with the slate (mean {c['cutoff_top01'].mean():.0f}, "
                 f"sd {c['cutoff_top01'].std():.0f})")
    save(fig, "cutoff_distribution")


def fig_ownership(slate):
    top = slate.sort_values("field_own", ascending=False).head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.barh(top["name"].str.replace("_", " "), top["field_own"] * 100, color=SERIES[0],
            height=0.7)
    for y, v in enumerate(top["field_own"] * 100):
        ax.text(v + 0.6, y, f"{v:.0f}%", va="center", color=INK2, fontsize=10)
    ax.set_xlabel("Share of opponent lineups (%)")
    ax.set_title("Simulated field ownership: the 'chalk'")
    ax.grid(axis="y", visible=False)
    save(fig, "ownership")


def fig_results(summary):
    s = summary.set_index("strategy").loc[["Field lineup (baseline)"] + STRAT_ORDER]
    metrics = [("cash", "P(cash, top 20%)"), ("top1", "P(top 1%)"), ("top01", "P(top 0.1%)")]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), sharey=True)
    labels = [SHORT[k] for k in s.index]
    for ax, (m, title) in zip(axes, metrics):
        for y, k in enumerate(s.index):
            v, lo, hi = s.loc[k, m] * 100, s.loc[k, m + "_lo"] * 100, s.loc[k, m + "_hi"] * 100
            ax.plot([lo, hi], [y, y], color=COLOR[k], lw=2, solid_capstyle="round")
            ax.plot(v, y, "o", ms=9, color=COLOR[k], mec=SURFACE, mew=2)
            ax.text(hi, y + 0.25, f" {v:.2f}%", color=INK2, fontsize=10, va="bottom")
        base = s.loc["Field lineup (baseline)", m] * 100
        ax.axvline(base, color=GRAY, lw=1, ls=":")
        ax.set_title(title)
        ax.set_xlabel("% of contests (95% CI)")
        ax.grid(axis="y", visible=False)
        ax.set_xlim(left=0)
    axes[0].set_yticks(range(len(labels)), labels)
    axes[0].invert_yaxis()
    fig.suptitle("Out-of-sample finish rates (2,000 contests, CIs clustered by field)",
                 x=0.01, ha="left", fontweight="bold", color=INK, fontsize=15)
    fig.tight_layout()
    save(fig, "results_finish_rates")

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for y, k in enumerate(s.index):
        v, lo, hi = s.loc[k, "roi"] * 100, s.loc[k, "roi_lo"] * 100, s.loc[k, "roi_hi"] * 100
        ax.plot([lo, hi], [y, y], color=COLOR[k], lw=2, solid_capstyle="round")
        ax.plot(v, y, "o", ms=9, color=COLOR[k], mec=SURFACE, mew=2)
        ax.text(hi, y, f"  {v:+.0f}%", color=INK2, fontsize=10, va="center")
    ax.axvline(-15, color=GRAY, lw=1, ls=":")
    ax.text(-15, -0.75, "theory: -15% (rake) ", color=INK2, fontsize=10, ha="right", va="center")
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_ylim(len(s) - 0.5, -1.1)
    ax.set_xlabel("Return on entry fee (%), 95% CI")
    ax.set_title("Expected ROI: heavy-tailed payouts make CIs wide")
    ax.grid(axis="y", visible=False)
    save(fig, "results_roi")


def _strategy_groups(strategies):
    """Group strategies that picked the same lineup: [(pids, color_key, label)]."""
    out = {}
    for _, row in strategies.iterrows():
        k = row["strategy"]
        if k not in COLOR:
            continue
        if row["pids"] in out:
            out[row["pids"]][1].append(SHORT[k].split(" ")[0])
        else:
            out[row["pids"]] = [k, [SHORT[k]]]
    groups = []
    for pids, (k, labs) in out.items():
        lab = labs[0] if len(labs) == 1 else labs[0].split(" ")[0] + " = " + " = ".join(labs[1:])
        groups.append((pids, k, lab))
    return groups


def fig_pool(pool, strategies):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(pool["mean_score"], pool["ucvar_score"], s=22, color=GRAY, alpha=0.6,
               label="Candidate lineups")
    for pids, k, lab in _strategy_groups(strategies):
        m = pool[pool["lineup"] == pids]
        if len(m):
            ax.scatter(m["mean_score"], m["ucvar_score"], s=120, color=COLOR[k],
                       edgecolor=SURFACE, linewidth=2, zorder=3, label=lab)
    ax.set_xlabel("Mean lineup score")
    ax.set_ylabel("U-CVaR 0.99 (mean of top 1% of scores)")
    ax.set_title("Candidate pool: expected points vs. upside")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=10)
    save(fig, "pool_tradeoff")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(pool["avg_field_own"] * 100, pool["ucvar_vs_field"], s=22, color=GRAY, alpha=0.6,
               label="Candidate lineups")
    for pids, k, lab in _strategy_groups(strategies):
        m = pool[pool["lineup"] == pids]
        if len(m):
            ax.scatter(m["avg_field_own"] * 100, m["ucvar_vs_field"], s=120, color=COLOR[k],
                       edgecolor=SURFACE, linewidth=2, zorder=3, label=lab)
    ax.set_xlabel("Average field ownership of lineup's players (%)")
    ax.set_ylabel("U-CVaR 0.99 of (score - top-0.1% cutoff)")
    ax.set_title("Field-aware upside vs. how 'chalky' a lineup is")
    ax.legend(loc="upper right", fontsize=10, frameon=True, facecolor=SURFACE,
              edgecolor=GRID, framealpha=0.95)
    save(fig, "pool_vs_ownership")


def fig_is(summary, tilt, reps):
    p = summary["p_true"].iloc[0]
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for i, (meth, g) in enumerate(reps.groupby("method", sort=False)):
        ax.plot(g["n"], g["rel_error"], "-o", color=SERIES[i], lw=2, ms=8, mec=SURFACE, mew=2)
        ax.text(g["n"].iloc[-1] * 1.08, g["rel_error"].iloc[-1], meth, color=INK, va="center")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Samples per estimate (log scale)")
    ax.set_ylabel("Relative error  sd / p  (log scale)")
    ax.set_title(f"Estimating P(lineup beats top-0.1% cutoff) = {p:.4f}")
    ax.set_xlim(right=reps["n"].max() * 3.5)
    save(fig, "is_relative_error")

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(tilt["t"], tilt["variance_ratio_vs_crude"], "-o", color=SERIES[0], lw=2, ms=8,
            mec=SURFACE, mew=2)
    best = tilt.loc[tilt["variance_ratio_vs_crude"].idxmax()]
    ax.annotate(f"best tilt t = {best['t']:.2f}\n{best['variance_ratio_vs_crude']:.1f}x less variance",
                (best["t"], best["variance_ratio_vs_crude"]), textcoords="offset points",
                xytext=(18, -30), color=INK)
    ax.axhline(1, color=GRAY, lw=1, ls=":")
    ax.set_xlabel("Mean shift t (in sd of the linearized lineup score)")
    ax.set_ylabel("Variance reduction vs. crude MC")
    ax.set_title("Choosing the importance-sampling tilt")
    save(fig, "is_tilt")


def fig_curse(pool, strategies):
    """In-sample estimate vs out-of-sample truth for every candidate (optimizer's curse)."""
    fig, ax = plt.subplots(figsize=(8, 5.2))
    x = (pool["exp_payout_insample"] - 1) * 100
    y = (pool["oos_payout"] - 1) * 100
    ax.scatter(x, y, s=22, color=GRAY, alpha=0.6, label="Candidate lineups")
    lim = [min(x.min(), y.min()) - 10, max(x.max(), y.max()) + 10]
    ax.plot(lim, lim, color=INK2, lw=1, ls=":")
    ax.text(lim[1], lim[1], "  in-sample = out-of-sample", color=INK2, fontsize=10, ha="right",
            va="bottom")
    for pids, k, lab in _strategy_groups(strategies):
        m = pool[pool["lineup"] == pids]
        if len(m):
            ax.scatter((m["exp_payout_insample"] - 1) * 100, (m["oos_payout"] - 1) * 100, s=120,
                       color=COLOR[k], edgecolor=SURFACE, linewidth=2, zorder=3, label=lab)
    ax.set_xlabel("ROI estimated on 5,000 selection scenarios (%)")
    ax.set_ylabel("ROI on 2,000 new contests (%)")
    ax.set_title("The optimizer's curse: tail estimates are noisy")
    ax.legend(loc="upper left", fontsize=10, frameon=True, facecolor=SURFACE,
              edgecolor=GRID, framealpha=0.95)
    save(fig, "optimizers_curse")


def fig_is_thresholds(th):
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.plot(th["p_true"], th["variance_reduction_factor"], "-o", color=SERIES[0], lw=2, ms=9,
            mec=SURFACE, mew=2)
    for _, r in th.iterrows():
        ax.annotate(f"score > {r['threshold']:.0f}: {r['variance_reduction_factor']:.0f}x",
                    (r["p_true"], r["variance_reduction_factor"]), textcoords="offset points",
                    xytext=(-10, 10), color=INK, fontsize=10, ha="right")
    ax.set_xscale("log")
    ax.set_yscale("log")
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    ax.yaxis.set_major_locator(FixedLocator([5, 10, 20]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}x"))
    ax.xaxis.set_major_locator(FixedLocator([0.03, 0.01, 0.003, 0.001]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlim(0.06, 0.0009)
    ax.set_ylim(4.5, 28)
    ax.set_xlabel("Event probability p (log scale, rarer to the right)")
    ax.set_ylabel("Variance reduction vs. crude MC (log)")
    ax.set_title("The rarer the upside event, the more IS helps")
    save(fig, "is_thresholds")


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    slate = pd.read_csv(RES / "slate.csv")
    fig_correlation(slate, np.load(RES / "corr.npy"))
    fig_marginal(slate)
    fig_payout(np.load(RES / "payout_table.npy"))
    contests = pd.read_csv(RES / "contests.csv")
    fig_field(np.load(RES / "field_scores_example.npy"), contests, slate)
    fig_ownership(slate)
    fig_results(pd.read_csv(RES / "summary.csv"))
    fig_pool(pd.read_csv(RES / "pool_selection.csv"), pd.read_csv(RES / "strategies.csv"))
    fig_is(pd.read_csv(RES / "is_summary.csv"), pd.read_csv(RES / "is_tilt.csv"),
           pd.read_csv(RES / "is_reps.csv"))
    pool = pd.read_csv(RES / "pool_selection.csv")
    if "oos_payout" in pool:
        fig_curse(pool, pd.read_csv(RES / "strategies.csv"))
    if (RES / "is_thresholds.csv").exists():
        fig_is_thresholds(pd.read_csv(RES / "is_thresholds.csv"))


if __name__ == "__main__":
    main()
